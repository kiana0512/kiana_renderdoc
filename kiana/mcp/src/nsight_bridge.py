"""Official Nsight D3D12 capture and offline Nsight -> Kiana RDC bridge."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
OS_ENVIRONMENT = {
    "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATH", "PATHEXT",
    "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
    "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "USERNAME",
    "USERDOMAIN", "HOMEDRIVE", "HOMEPATH",
}
SENSITIVE_METADATA_KEYS = {"process_environment", "process_command_line"}


def _minimal_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    result = {key: value for key, value in os.environ.items()
              if key.upper() in OS_ENVIRONMENT}
    if extra:
        result.update(extra)
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_metadata(value: Any) -> Any:
    """Remove process secrets before capture metadata is persisted or returned."""
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_METADATA_KEYS:
                clean[key] = "<redacted by Kiana>"
            else:
                clean[key] = sanitize_metadata(item)
        return clean
    if isinstance(value, list):
        return [sanitize_metadata(item) for item in value]
    return value


def count_source_commands(functions: list[dict[str, Any]]) -> dict[str, int]:
    names = Counter(str(item.get("function_name", "")) for item in functions)
    draws = sum(count for name, count in names.items()
                if re.search(r"(?:^|_)Draw(?:Indexed|Instanced|IndexedInstanced)?$", name))
    dispatches = sum(count for name, count in names.items()
                     if re.search(r"(?:^|_)Dispatch(?:Mesh|Rays)?$", name))
    presents = sum(count for name, count in names.items() if "Present" in name)
    return {"events": len(functions), "draws": draws,
            "dispatches": dispatches, "presents": presents}


def _find_nsight(binary: str) -> Path:
    roots = []
    for env_name in ("PROGRAMFILES", "PROGRAMW6432"):
        root = os.environ.get(env_name)
        if root:
            roots.extend(Path(root).glob("NVIDIA Corporation/Nsight Graphics */host/windows-desktop-nomad-x64"))
    candidates = sorted({path.resolve() for path in roots}, reverse=True)
    for root in candidates:
        candidate = root / binary
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("NVIDIA Nsight Graphics is required (%s not found)" % binary)


def _find_kiana_binary(name: str) -> Path:
    candidates = [PACKAGE_ROOT / name, PACKAGE_ROOT.parent / "x64" / "Development" / name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Kiana binary not found: %s" % name)


def _find_gfxreconstruct() -> tuple[Path, Path]:
    roots = [PACKAGE_ROOT / "tools" / "gfxreconstruct",
             PACKAGE_ROOT / "thirdparty" / "gfxreconstruct"]
    for root in roots:
        replay = root / "gfxrecon-replay.exe"
        capture = root / "d3d12_capture" / "d3d12_capture.dll"
        if replay.is_file() and capture.is_file():
            return replay.resolve(), capture.parent.resolve()
    raise FileNotFoundError("Bundled GFXReconstruct D3D12 tools are missing")


def _run(command: list[Path | str], *, cwd: Path | None = None,
         environment: dict[str, str] | None = None, timeout: int = 300,
         log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([str(item) for item in command], cwd=str(cwd) if cwd else None,
                            env=environment or _minimal_environment(), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if log_path:
        log_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Command failed (%d): %s" %
                           (result.returncode, Path(str(command[0])).name))
    return result


def _metadata(nsight_replay: Path, source: Path, option: str) -> str:
    return _run([nsight_replay, option, source], timeout=120).stdout.lstrip("\ufeff\x00")


def _image_comparison(source: Path, replay: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageStat
        with Image.open(source) as left, Image.open(replay) as right:
            left = left.convert("RGB")
            right = right.convert("RGB")
            if left.size != right.size:
                return {"status": "different_dimensions", "source": left.size, "rdc": right.size}
            diff = ImageChops.difference(left, right)
            extrema = diff.getextrema()
            means = ImageStat.Stat(diff).mean
            return {"status": "exact" if not diff.getbbox() else "different",
                    "dimensions": left.size,
                    "mean_absolute_error": round(sum(means) / len(means), 6),
                    "max_absolute_error": max(value[1] for value in extrema)}
    except ImportError:
        return {"status": "not_compared", "reason": "Pillow is not installed"}
    except Exception as error:
        return {"status": "not_compared", "reason": str(error)}


def capture_nsight_d3d12(executable: str, working_dir: str = "", arguments: str = "",
                         output_dir: str = "", capture_frame: int = 1200,
                         terminate_after_capture: bool = False,
                         timeout_seconds: int = 900) -> dict[str, Any]:
    """Capture one D3D12 frame with the official Nsight CLI.

    The game is left running by default. No protection, security, or injection checks
    are altered; this is the same documented capture path exposed by Nsight Graphics.
    """
    target = Path(executable).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError("Executable not found: %s" % target)
    if capture_frame < 2:
        raise ValueError("capture_frame must be at least 2")
    work = Path(working_dir).expanduser().resolve() if working_dir else target.parent
    if not work.is_dir():
        raise FileNotFoundError("Working directory not found: %s" % work)
    out = (Path(output_dir).expanduser().resolve() if output_dir else
           target.parent / "KianaCaptures")
    out.mkdir(parents=True, exist_ok=True)
    stem = "%s-frame%d-%s" % (target.stem, capture_frame,
                               datetime.now().strftime("%Y%m%d-%H%M%S"))
    output_base = out / stem
    log_path = out / (stem + ".log")
    command = [_find_nsight("ngfx-capture.exe"), "--exe", target,
               "--working-dir", work, "--args", arguments,
               "--output-file", output_base, "--frame-count", "1",
               "--capture-frame", str(capture_frame), "--bundle-replayer",
               "--no-block-on-first-incompatibility",
               "--no-block-on-interfering-application", "--diagnostic-mode"]
    if terminate_after_capture:
        command.append("--terminate-after-capture")
    _run(command, cwd=work, environment=_minimal_environment(),
         timeout=timeout_seconds, log_path=log_path)
    captures = sorted(out.glob(stem + "*.ngfx-capture"), key=lambda item: item.stat().st_mtime)
    if not captures:
        raise RuntimeError("Nsight reported success but did not create a capture")
    capture = captures[-1]
    return {"status": "capture_saved", "capture": str(capture),
            "bytes": capture.stat().st_size, "sha256": _sha256(capture),
            "capture_frame": capture_frame, "target_was_terminated": terminate_after_capture,
            "log": str(log_path)}


def convert_nsight_to_rdc(capture_path: str, output_dir: str = "",
                          nsight_path: str = "") -> dict[str, Any]:
    """Convert an Nsight D3D12 capture into a verified Kiana RDC offline."""
    source = Path(capture_path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".ngfx-capture":
        raise ValueError("Provide an existing .ngfx-capture file")
    out = (Path(output_dir).expanduser().resolve() if output_dir else
           source.parent / (source.stem + "-kiana-" + datetime.now().strftime("%Y%m%d-%H%M%S")))
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be new or empty: %s" % out)
    out.mkdir(parents=True, exist_ok=True)
    nsight = Path(nsight_path).expanduser().resolve() if nsight_path else _find_nsight("ngfx-replay.exe")
    if not nsight.is_file():
        raise FileNotFoundError("Nsight replayer not found: %s" % nsight)
    result: dict[str, Any] = {
        "status": "running", "source": str(source), "source_sha256": _sha256(source),
        "source_bytes": source.stat().st_size,
        "provenance": ["Nsight Graphics", "isolated bundled Nsight replay",
                       "GFXReconstruct D3D12", "Kiana RenderDoc"],
        "scope": "offline recapture; original capture remains authoritative",
        "steps": [],
    }
    result_path = out / "bridge-result.json"

    def save_result() -> None:
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def stage(name: str, command: list[Path | str], *, cwd: Path | None = None,
              environment: dict[str, str] | None = None, timeout: int = 300) -> None:
        record = {"stage": name, "status": "running"}
        result["steps"].append(record)
        save_result()
        try:
            _run(command, cwd=cwd, environment=environment, timeout=timeout,
                 log_path=out / (name + ".log"))
            record["status"] = "finished"
        except Exception as error:
            record.update(status="failed", error=str(error))
            save_result()
            raise
        save_result()

    try:
        raw_metadata = json.loads(_metadata(nsight, source, "--metadata"))
        metadata = sanitize_metadata(raw_metadata)
        if str(metadata.get("primary_api", "")).upper() != "D3D12":
            raise ValueError("The offline bridge currently supports D3D12 captures only")
        (out / "source-metadata.sanitized.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        functions = json.loads(_metadata(nsight, source, "--metadata-functions"))
        objects = json.loads(_metadata(nsight, source, "--metadata-objects"))
        (out / "source-functions.json").write_text(
            json.dumps(functions, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "source-objects.json").write_text(
            json.dumps(objects, ensure_ascii=False, indent=2), encoding="utf-8")
        logs = _metadata(nsight, source, "--metadata-logs")
        (out / "source-logs.txt").write_text(logs, encoding="utf-8")
        screenshot = out / "source-final-present.png"
        stage("source-screenshot", [nsight, "--metadata-screenshot", screenshot, source], timeout=120)
        result["source"] = {"path": str(source), "sha256": _sha256(source),
                            "bytes": source.stat().st_size,
                            "primary_api": metadata.get("primary_api"),
                            "captured_frame": metadata.get("captured_frame"),
                            "resolution": metadata.get("resolution"),
                            "commands": count_source_commands(functions),
                            "evidence_directory": str(out)}
        save_result()

        qrenderdoc = _find_kiana_binary("kiana_qrenderdoc.exe")
        renderdoccmd = _find_kiana_binary("kiana_renderdoccmd.exe")
        gfxrecon, capture_dll_dir = _find_gfxreconstruct()
        isolated = out / "isolated-replayer"
        stage("extract-replayer", [nsight, "--bundle-replayer", "--bundle-replayer-extract-only",
                                   "--bundle-replayer-no-rename", "--bundle-replayer-dir",
                                   isolated, source], timeout=180)
        for name in ("d3d12.dll", "dxgi.dll", "d3d12_capture.dll"):
            shutil.copy2(capture_dll_dir / name, isolated / name)
        gfxr_log = out / "gfxreconstruct-capture.log"
        gfxr_environment = _minimal_environment({
            "GFXRECON_CAPTURE_FILE": str(out / "intermediate.gfxr"),
            "GFXRECON_CAPTURE_FILE_TIMESTAMP": "false",
            "GFXRECON_CAPTURE_FRAMES": "2",
            "GFXRECON_LOG_FILE": str(gfxr_log),
        })
        stage("capture-intermediate", [isolated / "ngfx-replay.exe", "--present-hidden",
                                       "--loop-count", "3", "--no-block-on-incompatibility",
                                       source], cwd=isolated, environment=gfxr_environment, timeout=300)
        intermediate = out / "intermediate_frame_2.gfxr"
        if not intermediate.is_file():
            raise RuntimeError("GFXReconstruct did not create intermediate_frame_2.gfxr")

        rdc_dir = out / "renderdoc"
        rdc_dir.mkdir()
        recapture_config = out / "recapture-config.json"
        recapture_config.write_text(json.dumps({"source": str(intermediate),
                                                "replayer": str(gfxrecon),
                                                "output": str(rdc_dir)}), encoding="utf-8")
        stage("capture-rdc", [qrenderdoc, "--python=%s" %
                              (PACKAGE_ROOT / "mcp" / "worker" / "rdoc_recapture.py")],
              environment=_minimal_environment({"KIANA_NSIGHT_BRIDGE_CONFIG": str(recapture_config)}),
              timeout=420)
        recapture = json.loads((rdc_dir / "recapture-result.json").read_text(encoding="utf-8"))
        captures = list(rdc_dir.glob("*.rdc"))
        if recapture.get("status") != "capture_saved" or len(captures) != 1:
            raise RuntimeError("Kiana did not confirm exactly one completed RDC")
        rdc = captures[0]
        verify_path = rdc_dir / "verification.json"
        verify_config = out / "verify-config.json"
        verify_config.write_text(json.dumps({"capture": str(rdc), "result": str(verify_path)}),
                                 encoding="utf-8")
        stage("verify-rdc", [qrenderdoc, "--python=%s" %
                             (PACKAGE_ROOT / "mcp" / "worker" / "rdoc_verify.py")],
              environment=_minimal_environment({"KIANA_NSIGHT_VERIFY_CONFIG": str(verify_config)}),
              timeout=900)
        verification = json.loads(verify_path.read_text(encoding="utf-8"))
        if not verification.get("ok"):
            raise RuntimeError("RDC replay verification failed")
        thumbnail = rdc_dir / "rdc-final-present.png"
        stage("thumbnail-rdc", [renderdoccmd, "thumb", "-o", thumbnail,
                                "-f", "png", rdc], timeout=180)
        source_counts = result["source"]["commands"]
        command_match = (source_counts["draws"] == verification["draw_count"] and
                         source_counts["dispatches"] == verification["dispatch_count"])
        image_comparison = _image_comparison(screenshot, thumbnail)
        result.update({
            "status": "rdc_verified",
            "rdc": verification,
            "rdc_path": str(rdc),
            "fidelity": {
                "draw_dispatch_counts_match": command_match,
                "source_draws": source_counts["draws"],
                "rdc_draws": verification["draw_count"],
                "source_dispatches": source_counts["dispatches"],
                "rdc_dispatches": verification["dispatch_count"],
                "final_present": image_comparison,
                "claim": "evidence-preserving replay recapture, not byte-for-byte format conversion",
            },
        })
    except Exception as error:
        result.update(status="failed", error=str(error))
        save_result()
        raise
    save_result()
    return result
