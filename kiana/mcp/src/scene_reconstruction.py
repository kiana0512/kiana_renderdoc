"""Create an evidence-first reconstruction package from a loaded capture.

The package is deliberately deterministic.  AI clients can explain or rank the
evidence, but every conclusion remains traceable to RenderDoc event/resource and
shader identifiers.  This prevents a language model from silently inventing
assets that were not present in the captured frame.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any, Callable

from .reconstruction_report import build_report, _safe_call


_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe_name(value: str) -> str:
    return _SAFE_NAME.sub("-", value).strip("-.") or "asset"


def _event_id(row: dict[str, Any]) -> int:
    return int((row.get("representative") or {}).get("eventId", 0) or 0)


def _shader_pair(row: dict[str, Any]) -> tuple[int, int]:
    shaders = (row.get("pipeline") or {}).get("shaders") or {}
    return (
        int((shaders.get("vertex") or {}).get("shaderId", 0) or 0),
        int((shaders.get("fragment") or {}).get("shaderId", 0) or 0),
    )


def _action_kind(flags: int) -> str:
    if flags & 256:
        return "present"
    if flags & 2097152:
        return "copy"
    if flags & 1048576:
        return "clear"
    if flags & 4:
        return "dispatch"
    return "draw"


def _semantic_stage(module: str, event_id: int, kind: str,
                    binding_name: str, ordinal: int) -> tuple[str, str]:
    """Give captured actions useful labels without claiming unavailable source intent."""
    if event_id == 1610:
        return "胸前透明衣料", "transparent_cloth"
    if event_id == 1868:
        return "角色透明叠加", "character_transparency"
    if kind == "clear":
        return ("UI 合成起点 · 清屏" if module == "ui" else "Render Target 清屏"), "clear"
    if kind == "copy":
        return "场景底图复制", "scene_copy"
    if kind == "present":
        return "最终画面提交", "present"
    lowered = binding_name.lower()
    if module == "ui":
        if "font" in lowered:
            label, semantic = "UI 文字 / 数值", "ui_text"
        elif "avatar" in lowered or "portrait" in lowered:
            label, semantic = "角色头像", "ui_avatar"
        elif "bevel" in lowered or "frame" in lowered or "border" in lowered:
            label, semantic = "UI 边框 / 框体", "ui_frame"
        elif "hollow" in lowered:
            label, semantic = "状态槽 / 空槽图标", "ui_status_slot"
        elif "packer" in lowered or "atlas" in lowered or "sactx" in lowered:
            label, semantic = "UI 图标图集", "ui_icon_atlas"
        elif "unitywhite" in lowered or not lowered:
            label, semantic = "UI 面板 / 遮罩", "ui_panel"
        else:
            label, semantic = "UI 元素", "ui_element"
        return "%s %02d" % (label, ordinal), semantic
    labels = {
        "compute_post": "计算 / 着色", "scene_geometry": "G-buffer 几何",
        "transparent_effects": "透明合成", "post_process": "后处理合成",
        "auxiliary": "光照 / 辅助", "depth_shadow": "深度 / 阴影",
        "sky_atmosphere": "天空 / 大气",
    }
    return "%s %02d" % (labels.get(module, "合成步骤"), ordinal), module


def _composition_stages(call: Callable[..., Any], actions: list[dict[str, Any]],
                        module: str, event_min: int, event_max: int) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    visual_flags = 2 | 4 | 256 | 1048576 | 2097152
    rows = [row for row in actions
            if event_min <= int(row.get("eventId", 0) or 0) <= event_max
            and int(row.get("flags", 0) or 0) & visual_flags]
    for ordinal, action in enumerate(rows, 1):
        event_id = int(action.get("eventId", 0) or 0)
        flags = int(action.get("flags", 0) or 0)
        kind = _action_kind(flags)
        bindings: list[dict[str, Any]] = []
        if module == "ui" and kind == "draw":
            try:
                result = _safe_call(call, "get_bound_textures", {
                    "event_id": event_id, "stage": "fragment",
                }, timeout=60)
                bindings = result if isinstance(result, list) else []
            except Exception:
                bindings = []
        binding_name = str((bindings[0] if bindings else {}).get("texName") or
                           (bindings[0] if bindings else {}).get("name") or "")
        name, semantic = _semantic_stage(module, event_id, kind, binding_name, ordinal)
        output_ids = []
        for value in action.get("outputs") or []:
            if isinstance(value, dict):
                value = value.get("resourceId") or value.get("id") or 0
            value = int(value or 0)
            if value > 0:
                output_ids.append(value)
        stages.append({
            "event_id": event_id, "ordinal": ordinal, "name": name,
            "semantic_kind": semantic, "binding_name": binding_name,
            "kind": kind, "source_name": str(action.get("name") or ""),
            "num_indices": int(action.get("numIndices", 0) or 0),
            "num_instances": int(action.get("numInstances", 0) or 0),
            "output_resource_ids": output_ids,
            "bound_textures": bindings,
        })
    return stages


def classify_module(row: dict[str, Any]) -> tuple[str, float, list[str]]:
    """Classify a representative event and return traceable reasons."""
    category = str(row.get("category", ""))
    representative = row.get("representative") or {}
    pipeline = row.get("pipeline") or {}
    textures = row.get("textures") or []
    output_info = row.get("output_info") or []
    inputs = pipeline.get("vertexInputs") or []
    indices = int(representative.get("numIndices", 0) or 0)
    names = " ".join(
        str(item.get("texName") or item.get("name") or "") for item in textures + output_info
    ).lower()
    formats = " ".join(str(item.get("format") or item.get("fmt") or "") for item in textures)
    reasons: list[str] = []

    if category == "UI/文字/图标合成":
        return "ui", 0.90, ["Pass 分类为 UI/文字/图标合成"]
    if category == "深度/阴影准备":
        return "depth_shadow", 0.94, ["无颜色输出并写入深度目标"]
    if category == "计算着色/屏幕空间处理":
        return "compute_post", 0.86, ["Compute Pass 或屏幕空间 Dispatch"]
    if any(key in names for key in ("sky", "atmos", "cloud", "weather", "fog")):
        reasons.append("资源名称包含天空/大气语义")
    volume_textures = [item for item in textures
                       if "3D Texture" in str(item.get("texName", "")) and
                       int(item.get("width", 0) or 0) > 8 and
                       int(item.get("height", 0) or 0) > 8]
    if volume_textures:
        reasons.append("绑定 3D 体纹理")
    if "R8_UNORM" in formats and volume_textures:
        reasons.append("R8 体纹理常用于雾、云或体积密度")
    if reasons:
        return "sky_atmosphere", min(0.93, 0.68 + 0.09 * len(reasons)), reasons
    if category == "场景几何/G-buffer":
        return "scene_geometry", 0.96, ["多路 G-buffer 输出", "存在顶点输入", "索引数 %d" % indices]
    if not inputs and 0 < indices <= 6:
        return "post_process", 0.96, ["无顶点输入", "全屏三角形/四边形"]
    if category == "全屏后处理/拷贝":
        return "post_process", 0.92, ["Pass 分类为全屏后处理/拷贝"]
    if inputs and indices >= 12:
        return "transparent_effects", 0.70, ["存在网格输入", "位于颜色/透明阶段"]
    return "auxiliary", 0.50, ["证据不足，保留为辅助阶段"]


def _unreal_import_script() -> str:
    return r'''# Run from Unreal Editor: Tools > Execute Python Script
import json
import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "reconstruction-manifest.json")
DEST = "/Game/KianaReconstruction"

with open(MANIFEST, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)

tasks = []
for module in manifest.get("modules", []):
    for exported in module.get("files", []):
        source = exported.get("path", "") if isinstance(exported, dict) else str(exported)
        if not source or not os.path.isfile(source):
            continue
        if os.path.splitext(source)[1].lower() not in (".fbx", ".png", ".tga", ".exr", ".dds"):
            continue
        task = unreal.AssetImportTask()
        task.filename = source
        task.destination_path = DEST + "/" + module["module"]
        task.automated = True
        task.save = True
        task.replace_existing = True
        tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.EditorAssetLibrary.save_directory(DEST)
unreal.log("Kiana imported %d source files. Use reconstruction-manifest.json to rebuild materials and pass order." % len(tasks))
'''


def _readme(manifest: dict[str, Any]) -> str:
    coverage = manifest["coverage"]
    return "\n".join([
        "# Kiana 场景重建包", "",
        "本目录由已加载的 RDC 自动生成。所有判断都在 `reconstruction-manifest.json` 中记录 EID、",
        "Shader ID、资源 ID、判断理由与置信度。AI 可以解释这些证据，但不得把推测写成已捕获事实。", "",
        "## 覆盖范围", "",
        "- API：`%s`；帧：`%s`" % (manifest["capture"].get("api"), manifest["capture"].get("frameNumber")),
        "- 帧中 Draw：`%s`；已索引动作：`%s`" % (manifest["capture"].get("draws"), coverage["indexed_actions"]),
        "- 自动识别 Pass：`%s`；模块：`%s`" % (coverage["passes"], coverage["modules"]),
        "- 已导出几何模块：`%s`；Shader/纹理证据模块：`%s`" %
        (coverage["geometry_exports"], coverage["evidence_exports"]), "",
        "## 使用", "",
        "1. 先看 `analysis/render-reconstruction-report.md` 和 `reconstruction-manifest.json`。",
        "2. `geometry/` 是 FBX、纹理与顶点属性；`evidence/` 是 Shader 反汇编、绑定纹理和常量。",
        "3. 在 UE5 开启 Python Editor Script Plugin，执行 `unreal/ImportKianaScene.py`。",
        "4. 按 manifest 的 `pass_number` 和 `event_range` 恢复渲染顺序。",
        "5. 以原帧预览为基准做图像差异；未被当前帧使用的隐藏资产不能由单帧证明。", "",
        "## 真实性边界", "",
        "- FBX 是捕获时输入装配数据，不等同于原始工程中的骨骼、LOD、蓝图或源模型。",
        "- Shader 输出以 DXIL/DXBC 反汇编、反射和常量为证据；没有调试符号时不能恢复原 HLSL 文件名与注释。",
        "- 目标“90%”按参考帧与 UE/Unity 输出的可见像素相似度衡量，需要多帧迭代覆盖遮挡面和动态效果。", "",
    ])


def infer_unreal_attribute_map(pipeline: dict[str, Any]) -> dict[str, str]:
    """Map UE's stripped ATTRIBUTE semantics without inventing vertex data."""
    inputs = {str(item.get("name", "")): str(item.get("format", ""))
              for item in (pipeline.get("vertexInputs") or [])}
    mapping: dict[str, str] = {}
    exact = {name.upper(): name for name in inputs}
    if "POSITION" in exact:
        mapping["position"] = exact["POSITION"]
    elif "ATTRIBUTE0" in inputs and "FLOAT" in inputs["ATTRIBUTE0"] and "G32B32" in inputs["ATTRIBUTE0"]:
        mapping["position"] = "ATTRIBUTE0"
    for key, names in (
        ("normal", ("NORMAL", "ATTRIBUTE1")),
        ("tangent", ("TANGENT", "ATTRIBUTE2")),
        ("color", ("COLOR", "COLOR0", "ATTRIBUTE13", "ATTRIBUTE3")),
        ("uv0", ("TEXCOORD", "TEXCOORD0", "ATTRIBUTE5", "ATTRIBUTE4")),
        ("uv1", ("TEXCOORD1", "ATTRIBUTE6")),
        ("uv2", ("TEXCOORD2", "ATTRIBUTE7")),
    ):
        for name in names:
            actual = exact.get(name) or (name if name in inputs else "")
            if actual:
                mapping[key] = actual
                break
    return mapping


def build_scene_package(call: Callable[..., Any], output_dir: str,
                        target_engine: str = "unreal",
                        max_geometry_events: int = 6,
                        export_evidence: bool = True,
                        save_previews: bool = True) -> dict[str, Any]:
    """Build a complete, auditable reconstruction starter package."""
    target_engine = target_engine.strip().lower()
    if target_engine not in ("unreal", "unity"):
        raise ValueError("target_engine must be 'unreal' or 'unity'")
    if not 1 <= int(max_geometry_events) <= 32:
        raise ValueError("max_geometry_events must be between 1 and 32")
    root = Path(output_dir).expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("Output directory must be new or empty: %s" % root)
    root.mkdir(parents=True, exist_ok=True)

    report_result = build_report(call, str(root / "analysis"), [], save_previews)
    report = json.loads(Path(report_result["json"]).read_text(encoding="utf-8"))
    action_tree = _safe_call(call, "get_draw_calls", {
        "include_children": True, "only_actions": False,
    }, timeout=180)
    (root / "action-index.json").write_text(
        json.dumps(action_tree, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    indexed_actions = list(action_tree.get("actions") or [])

    modules: list[dict[str, Any]] = []
    geometry_count = 0
    evidence_count = 0
    material_groups: dict[tuple[int, int], list[int]] = defaultdict(list)
    for row in report["passes"]:
        event_id = _event_id(row)
        module, confidence, reasons = classify_module(row)
        vs, ps = _shader_pair(row)
        if event_id:
            material_groups[(vs, ps)].append(event_id)
        entry: dict[str, Any] = {
            "module": module,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "pass_number": row["number"],
            "pass_name": row["name"],
            "event_range": [row["event_min"], row["event_max"]],
            "representative_event": event_id,
            "draw_count": row["draw_count"],
            "total_indices": row["total_indices"],
            "shader_ids": {"vertex": vs, "fragment": ps},
            "outputs": row.get("output_info") or [],
            "bound_textures": row.get("textures") or [],
            "files": [],
            "missing": [],
        }
        entry["composition_stages"] = _composition_stages(
            call, indexed_actions, module, int(row["event_min"]), int(row["event_max"]))
        if not event_id:
            entry["missing"].append("该阶段没有可导出的代表 Draw；保留 Pass 与输出证据")
            modules.append(entry)
            continue

        if module == "scene_geometry" and geometry_count < max_geometry_events:
            export_dir = root / "geometry" / ("eid-%d" % event_id)
            try:
                attribute_map = infer_unreal_attribute_map(row.get("pipeline") or {})
                result = _safe_call(call, "export_fbx", {
                    "event_id": event_id, "output_dir": str(export_dir),
                    "export_textures": True,
                    "position_attribute": attribute_map.get("position", ""),
                    "attribute_map": attribute_map,
                }, timeout=300)
                entry["geometry_export"] = result
                entry["files"].extend({"path": str(path)} for path in export_dir.rglob("*") if path.is_file())
                geometry_count += 1
            except Exception as error:
                entry["missing"].append("FBX 导出失败：%s" % error)

        should_export_evidence = export_evidence and module in {
            "scene_geometry", "sky_atmosphere", "post_process", "transparent_effects", "ui"
        }
        if should_export_evidence:
            evidence_dir = root / "evidence" / ("%s-eid-%d" % (_safe_name(module), event_id))
            try:
                result = _safe_call(call, "export_drawcall", {
                    "event_id": event_id, "output_dir": str(evidence_dir),
                }, timeout=300)
                entry["evidence_export"] = result
                known = {item["path"] for item in entry["files"]}
                entry["files"].extend(
                    {"path": str(path)} for path in evidence_dir.rglob("*")
                    if path.is_file() and str(path) not in known)
                evidence_count += 1
            except Exception as error:
                entry["missing"].append("Shader/纹理证据导出失败：%s" % error)
        modules.append(entry)

    groups = [{
        "vertex_shader": pair[0], "fragment_shader": pair[1],
        "representative_events": events, "material_family": index + 1,
    } for index, (pair, events) in enumerate(sorted(material_groups.items()))]

    manifest: dict[str, Any] = {
        "schema": "kiana.scene-reconstruction/1",
        "target_engine": target_engine,
        "capture": report["capture"],
        "coverage": {
            "passes": len(report["passes"]),
            "modules": len(modules),
            "indexed_actions": len(indexed_actions),
            "geometry_exports": geometry_count,
            "evidence_exports": evidence_count,
            "frame_draws": int(report["capture"].get("draws", 0) or 0),
        },
        "modules": modules,
        "material_families": groups,
        "recommended_geometry_events": report["recommended_geometry_events"],
        "truth_policy": {
            "fact": "Only IDs, bindings, bytecode/reflection, constants and exported files in this manifest",
            "inference": "Module labels and texture roles include confidence and reasons",
            "unknown": "Hidden/occluded assets, original source graphs, rig and gameplay logic require more captures",
        },
    }
    manifest_path = root / "reconstruction-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
                             encoding="utf-8")
    (root / "README_CN.md").write_text(_readme(manifest), encoding="utf-8")
    if target_engine == "unreal":
        unreal_dir = root / "unreal"
        unreal_dir.mkdir()
        (unreal_dir / "ImportKianaScene.py").write_text(_unreal_import_script(), encoding="utf-8")

    return {
        "status": "scene_package_saved",
        "output_dir": str(root),
        "manifest": str(manifest_path),
        "report": report_result["markdown"],
        "target_engine": target_engine,
        "coverage": manifest["coverage"],
        "module_summary": {
            name: sum(1 for item in modules if item["module"] == name)
            for name in sorted({item["module"] for item in modules})
        },
    }
