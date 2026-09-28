"""Build a renderer-reconstruction report from a live Kiana capture."""
from __future__ import annotations

import json
from pathlib import Path
import re
import time
from typing import Any, Callable


PASS_RE = re.compile(r"^(Colour|Depth-only|Compute) Pass #")


def group_passes(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group RenderDoc's flattened synthetic pass markers with their child actions."""
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for action in actions:
        name = str(action.get("name", ""))
        if PASS_RE.match(name):
            current = {
                "name": name,
                "outputs": list(action.get("outputs") or []),
                "actions": [],
            }
            groups.append(current)
        elif current is not None:
            current["actions"].append(action)
    return groups


def classify_pass(name: str, draw_count: int, total_indices: int,
                  representative: dict[str, Any] | None,
                  pipeline: dict[str, Any] | None,
                  textures: list[dict[str, Any]] | None) -> str:
    """Return a conservative reconstruction-oriented pass category."""
    if name.startswith("Depth-only"):
        return "深度/阴影准备"
    if name.startswith("Compute"):
        return "计算着色/屏幕空间处理"
    representative = representative or {}
    pipeline = pipeline or {}
    texture_names = " ".join(str(item.get("texName", "")) for item in (textures or []))
    vertex_inputs = pipeline.get("vertexInputs") or []
    indices = int(representative.get("numIndices", 0) or 0)
    average_indices = (float(total_indices) / draw_count) if draw_count else 0.0
    if "font" in texture_names.lower() or (draw_count >= 35 and 0 < average_indices <= 24):
        return "UI/文字/图标合成"
    if not vertex_inputs and 0 < indices <= 6:
        return "全屏后处理/拷贝"
    if len(representative.get("outputs") or []) >= 3 and vertex_inputs:
        return "场景几何/G-buffer"
    if vertex_inputs and indices >= 12:
        return "几何/透明物/界面网格"
    return "合成/辅助 Pass"


def _safe_call(call: Callable[..., Any], method: str, params: dict[str, Any],
               timeout: int = 180) -> Any:
    last: Exception | None = None
    for attempt in range(2):
        try:
            return call(method, params, timeout=timeout)
        except Exception as error:
            last = error
            if attempt == 0:
                time.sleep(0.2)
    raise last or RuntimeError("Unknown IPC failure")


def _texture_label(info: dict[str, Any]) -> str:
    return "%s (%sx%s, %s)" % (
        info.get("name", "Resource %s" % info.get("id", "?")),
        info.get("w", "?"), info.get("h", "?"), info.get("fmt", "?"))


def build_report(call: Callable[..., Any], output_dir: str,
                 focus_event_ids: list[int] | None = None,
                 save_previews: bool = True) -> dict[str, Any]:
    """Inspect one loaded frame and write JSON plus a Chinese Markdown report."""
    out = Path(output_dir).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be new or empty: %s" % out)
    out.mkdir(parents=True, exist_ok=True)
    previews = out / "pass-previews"
    if save_previews:
        previews.mkdir()

    status = _safe_call(call, "get_capture_status", {})
    if not status.get("loaded"):
        raise RuntimeError("No capture is loaded in the selected Kiana instance")
    draw_tree = _safe_call(call, "get_draw_calls", {
        "include_children": True, "only_actions": False,
    })
    groups = group_passes(list(draw_tree.get("actions") or []))
    passes: list[dict[str, Any]] = []

    for number, group in enumerate(groups, 1):
        actions = list(group["actions"])
        draws = [item for item in actions if int(item.get("numIndices", 0) or 0) > 0]
        representative = max(draws, key=lambda item: int(item.get("numIndices", 0) or 0),
                             default=None)
        row: dict[str, Any] = {
            "number": number,
            "name": group["name"],
            "outputs": group["outputs"],
            "event_min": min((item.get("eventId", 0) for item in actions), default=0),
            "event_max": max((item.get("eventId", 0) for item in actions), default=0),
            "draw_count": len(draws),
            "total_indices": sum(int(item.get("numIndices", 0) or 0) for item in draws),
            "representative": representative,
            "output_info": [],
        }
        for resource_id in group["outputs"][:4]:
            try:
                row["output_info"].append(_safe_call(
                    call, "get_texture_info", {"resource_id": resource_id}, timeout=60))
            except Exception as error:
                row["output_info"].append({"id": resource_id, "error": str(error)})
        if save_previews and group["outputs"]:
            preview = previews / ("pass-%02d-output-%s.png" % (number, group["outputs"][0]))
            try:
                row["preview"] = _safe_call(call, "save_texture", {
                    "resource_id": group["outputs"][0], "output_path": str(preview),
                    "mip": 0, "slice": -1,
                }, timeout=120)
            except Exception as error:
                row["preview_error"] = str(error)
        pipeline: dict[str, Any] = {}
        textures: list[dict[str, Any]] = []
        if representative:
            event_id = int(representative["eventId"])
            try:
                row["draw_details"] = _safe_call(
                    call, "get_draw_call_details", {"event_id": event_id})
                pipeline = _safe_call(call, "get_pipeline_state", {"event_id": event_id})
                row["pipeline"] = pipeline
                textures = _safe_call(call, "get_bound_textures", {
                    "event_id": event_id, "stage": "fragment",
                })
                row["textures"] = textures
            except Exception as error:
                row["inspection_error"] = str(error)
        row["category"] = classify_pass(
            group["name"], len(draws), row["total_indices"], representative,
            pipeline, textures)
        passes.append(row)

    focused = []
    for event_id in focus_event_ids or []:
        item: dict[str, Any] = {"event_id": event_id}
        for method, params, key in (
            ("get_draw_call_details", {"event_id": event_id}, "draw_details"),
            ("get_pipeline_state", {"event_id": event_id}, "pipeline"),
            ("get_bound_textures", {"event_id": event_id, "stage": "fragment"}, "textures"),
            ("reverse_shader", {"event_id": event_id, "stage": "fragment"}, "fragment_shader"),
        ):
            try:
                item[key] = _safe_call(call, method, params, timeout=180)
            except Exception as error:
                item[key] = {"error": str(error)}
        focused.append(item)

    geometry_candidates = sorted(
        [row for row in passes if row.get("representative") and
         row["category"] in ("场景几何/G-buffer", "几何/透明物/界面网格")],
        key=lambda row: int(row["representative"].get("numIndices", 0) or 0), reverse=True)
    result = {
        "capture": status,
        "pass_count": len(passes),
        "passes": passes,
        "focus_events": focused,
        "recommended_geometry_events": [
            int(row["representative"]["eventId"]) for row in geometry_candidates[:12]
        ],
    }
    json_path = out / "render-reconstruction-report.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str),
                         encoding="utf-8")

    lines = [
        "# Kiana 渲染还原报告", "",
        "- API：`%s`" % status.get("api"),
        "- 帧：`%s`" % status.get("frameNumber"),
        "- Draw：`%s`；Dispatch：`%s`；API 调用：`%s`" %
        (status.get("draws"), status.get("dispatches"), status.get("calls")),
        "- 自动识别 Pass：`%d`" % len(passes), "",
        "## Pass 顺序", "",
        "| # | 事件范围 | 分类 | Draw | 索引总数 | 代表 EID | 主要输出 |",
        "|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in passes:
        representative = row.get("representative") or {}
        output = "; ".join(_texture_label(info) for info in row["output_info"] if "error" not in info)
        lines.append("| %d | %s–%s | %s | %d | %d | %s | %s |" % (
            row["number"], row["event_min"], row["event_max"], row["category"],
            row["draw_count"], row["total_indices"], representative.get("eventId", ""),
            output.replace("|", "\\|")))
    lines += ["", "## 建议的还原顺序", "",
              "1. 从 `场景几何/G-buffer` 的代表事件导出 FBX、顶点布局和材质贴图。",
              "2. 根据 Depth-only Pass 恢复遮挡、阴影或深度预处理。",
              "3. 按 Pass 顺序复现光照、透明物和屏幕空间处理。",
              "4. 全屏三角形且没有顶点输入的事件通常是后处理，不应当作模型导出。",
              "5. 最后恢复 UI/字体/图标层；它们通常包含大量四边形或 Font Texture。", "",
              "## 推荐几何事件", "",
              ", ".join("EID %d" % value for value in result["recommended_geometry_events"]) or "无", "",
              "完整管线、纹理和焦点事件着色器信息见 `render-reconstruction-report.json`。"]
    markdown_path = out / "render-reconstruction-report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "status": "report_saved",
        "markdown": str(markdown_path),
        "json": str(json_path),
        "preview_directory": str(previews) if save_previews else "",
        "pass_count": len(passes),
        "focus_event_count": len(focused),
        "recommended_geometry_events": result["recommended_geometry_events"],
    }
