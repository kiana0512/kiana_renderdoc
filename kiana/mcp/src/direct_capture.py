"""Verified Kiana direct-capture orchestration for D3D11 applications."""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any

from .nsight_bridge import _find_kiana_binary, _minimal_environment, _sha256


PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _wait_json(path: Path, timeout_seconds: int, pending_status: str = "") -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                value = json.loads(path.read_text(encoding="utf-8-sig"))
                if not pending_status or value.get("status") != pending_status:
                    return value
            except (OSError, json.JSONDecodeError) as error:
                last_error = error
        time.sleep(0.5)
    message = "Timed out waiting for %s" % path.name
    if last_error:
        message += ": %s" % last_error
    raise TimeoutError(message)


def capture_kiana_d3d11(executable: str, working_dir: str = "", arguments: list[str] | None = None,
                        output_dir: str = "", capture_frame: int = 900,
                        unity_safe_mode: bool = True, hook_children: bool = True,
                        terminate_after_capture: bool = False, open_diagnostics: bool = True,
                        timeout_seconds: int = 300,
                        preserve_export_identity: bool = False,
                        wrap_opted_out_devices: bool = False) -> dict[str, Any]:
    """Capture and independently verify one D3D11 frame with Kiana RenderDoc."""
    target = Path(executable).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError("Executable not found: %s" % target)
    work = Path(working_dir).expanduser().resolve() if working_dir else target.parent
    if not work.is_dir():
        raise FileNotFoundError("Working directory not found: %s" % work)
    if capture_frame < 1:
        raise ValueError("capture_frame must be positive")
    if timeout_seconds < 10:
        raise ValueError("timeout_seconds must be at least 10")

    if output_dir:
        out = Path(output_dir).expanduser().resolve()
    else:
        out = target.parent / "KianaCaptures" / (
            "%s-d3d11-frame%d-%s" %
            (target.stem, capture_frame, datetime.now().strftime("%Y%m%d-%H%M%S")))
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be new or empty: %s" % out)
    out.mkdir(parents=True, exist_ok=True)

    config_path = out / "direct-capture-config.json"
    result_path = out / "direct-capture-result.json"
    config_path.write_text(json.dumps({
        "executable": str(target),
        "working_dir": str(work),
        "arguments": list(arguments or []),
        "output": str(out),
        "frame": capture_frame,
        "timeout_seconds": timeout_seconds,
        "hook_children": hook_children,
        "terminate_after_capture": terminate_after_capture,
        "environment": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    environment = _minimal_environment({
        "KIANA_DIRECT_CAPTURE_CONFIG": str(config_path),
        "KIANA_UNITY_SAFE_MODE": "1" if unity_safe_mode else "0",
        "KIANA_CAPTURE_DIAGNOSTICS": "1" if open_diagnostics else "0",
        "KIANA_EXPORT_IDENTITY": "1" if preserve_export_identity else "0",
        "KIANA_D3D11_CAPTURE_OVERRIDE": "1" if wrap_opted_out_devices else "0",
    })
    qrenderdoc = _find_kiana_binary("kiana_qrenderdoc.exe")
    subprocess.Popen(
        [str(qrenderdoc), "--python=%s" % (PACKAGE_ROOT / "mcp" / "worker" / "rdoc_direct_capture.py")],
        cwd=str(work), env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    capture_result = _wait_json(result_path, timeout_seconds + 30, "waiting_for_capture")
    if capture_result.get("status") != "capture_saved":
        raise RuntimeError(capture_result.get("error") or "Kiana did not save a capture")
    rdc_files = [Path(item["path"]).resolve() for item in capture_result.get("rdc_files", [])]
    if len(rdc_files) != 1 or not rdc_files[0].is_file():
        raise RuntimeError("Kiana did not confirm exactly one completed RDC")
    rdc = rdc_files[0]

    verify_config = out / "verify-config.json"
    verify_result = out / "verification.json"
    verify_config.write_text(json.dumps({"capture": str(rdc), "result": str(verify_result)}),
                             encoding="utf-8")
    verify_environment = _minimal_environment({"KIANA_NSIGHT_VERIFY_CONFIG": str(verify_config)})
    subprocess.Popen(
        [str(qrenderdoc), "--python=%s" % (PACKAGE_ROOT / "mcp" / "worker" / "rdoc_verify.py")],
        env=verify_environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    verification = _wait_json(verify_result, max(90, timeout_seconds))
    if not verification.get("ok"):
        raise RuntimeError("Saved RDC failed replay verification: %s" % verification)

    return {
        "status": "capture_saved",
        "capture": str(rdc),
        "bytes": rdc.stat().st_size,
        "sha256": _sha256(rdc),
        "api": verification.get("api"),
        "frame_number": verification.get("frame_number"),
        "action_count": verification.get("action_count"),
        "draw_count": verification.get("draw_count"),
        "dispatch_count": verification.get("dispatch_count"),
        "resource_count": verification.get("resource_count"),
        "shader_count": verification.get("shader_count"),
        "unity_safe_mode": unity_safe_mode,
        "preserve_export_identity": preserve_export_identity,
        "wrap_opted_out_devices": wrap_opted_out_devices,
        "target_was_terminated": bool(capture_result.get("child_terminated")),
        "diagnostic_log": str(out / "renderdoc-debug.log"),
        "verification": str(verify_result),
    }
