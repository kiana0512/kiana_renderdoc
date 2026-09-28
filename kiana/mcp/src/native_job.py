"""One-shot native desktop analysis worker.

Writes newline-delimited JSON so Kiana Studio can show deterministic progress
without embedding Python in the WinUI process.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if __package__ in (None, ""):
    package_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(package_root.parent))
    from kiana.mcp.src.ipc_client import IPCClient, instances
    from kiana.mcp.src.scene_reconstruction import build_scene_package
else:
    from .ipc_client import IPCClient, instances
    from .scene_reconstruction import build_scene_package


def emit(kind: str, **values):
    print(json.dumps({"type": kind, **values}, ensure_ascii=False, default=str), flush=True)


def connect(capture: Path) -> IPCClient:
    active = instances()
    if not active:
        home = Path(os.environ.get("KIANA_HOME", Path(__file__).resolve().parents[2]))
        gui = home / "kiana_qrenderdoc.exe"
        if not gui.is_file():
            raise FileNotFoundError("Kiana GUI not found: %s" % gui)
        subprocess.Popen([str(gui), str(capture)], cwd=str(capture.parent))
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            active = instances()
            if active:
                break
            time.sleep(0.5)
    if not active:
        raise TimeoutError("Kiana GUI bridge did not start")
    client = IPCClient(timeout=360)
    client.pid = active[-1]["pid"]
    return client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--engine", choices=("unreal", "unity"), default="unreal")
    parser.add_argument("--max-geometry", type=int, default=12)
    args = parser.parse_args()
    capture = Path(args.capture).resolve()
    if not capture.is_file():
        raise FileNotFoundError(capture)

    emit("progress", percent=4, message="正在连接 Kiana 回放进程")
    client = connect(capture)
    emit("progress", percent=9, message="正在载入 RDC；大文件可能需要一分钟")
    opened = client.call("open_capture", {"capture_path": str(capture)}, timeout=240)
    if isinstance(opened, dict) and opened.get("error"):
        raise RuntimeError(opened["error"])
    emit("progress", percent=18, message="正在索引 Draw、Dispatch 与资源依赖")

    last = {"percent": 18}
    def call(method, params=None, timeout=None):
        progress_map = {
            "get_capture_status": (20, "识别图形 API 与帧状态"),
            "get_frame_summary": (23, "统计帧事件"),
            "get_draw_calls": (28, "构建完整动作索引"),
            "get_pipeline_state": (36, "分析 Pass 与管线状态"),
            "get_bound_textures": (48, "追踪纹理与 Render Target"),
            "save_texture": (62, "导出纹理证据"),
            "export_fbx": (72, "导出唯一几何候选"),
            "export_drawcall": (83, "保存 Shader、常量与绑定证据"),
        }
        percent, message = progress_map.get(method, (last["percent"], "正在分析 " + method))
        if percent > last["percent"]:
            last["percent"] = percent
            emit("progress", percent=percent, message=message)
        return client.call(method, params or {}, timeout=timeout)

    result = build_scene_package(call, args.output, args.engine, args.max_geometry, True, True)
    emit("progress", percent=96, message="正在写入重建清单与引擎导入脚本")
    emit("result", manifest=result["manifest"], output_dir=result["output_dir"], coverage=result["coverage"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        emit("error", message=str(error), error_type=type(error).__name__)
        raise
