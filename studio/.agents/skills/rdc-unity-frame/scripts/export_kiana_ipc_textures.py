"""Export RDC texture IDs through a live Kiana RenderDoc bridge."""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path


def connect_frame(frame, pid=None, kiana_install=Path(r"C:\Users\RT\AppData\Local\Kiana RenderDoc")):
    sys.path.insert(0, str(kiana_install / "mcp"))
    from src import ipc_client

    candidates = []
    for manifest in (Path(tempfile.gettempdir()) / "kiana_mcp").glob("*/**/instance.json"):
        try:
            info = json.loads(manifest.read_text(encoding="utf-8"))
            if info.get("enabled") and time.time() - info.get("heartbeat", 0) < 10:
                candidates.append((manifest.parent.parent, info["pid"]))
        except (OSError, ValueError, KeyError):
            pass
    for mailbox, candidate_pid in candidates:
        if pid is not None and pid != candidate_pid:
            continue
        ipc_client.transport.mailbox_root = lambda mailbox=mailbox: str(mailbox)
        client = ipc_client.IPCClient(timeout=60)
        client.pid = candidate_pid
        try:
            status = client.call("get_capture_status", {}, timeout=5)
        except Exception:
            continue
        if status.get("loaded") and status.get("frameNumber") == frame:
            print(f"Selected live Kiana PID {candidate_pid}: frame {frame}", flush=True)
            return client
    else:
        raise RuntimeError(f"No responsive Kiana bridge with frame {frame}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("resource_ids", nargs="+", type=int)
    ap.add_argument("--pid", type=int)
    ap.add_argument("--frame", type=int, default=38112)
    ap.add_argument("--kiana-install", type=Path, default=Path(r"C:\Users\RT\AppData\Local\Kiana RenderDoc"))
    args = ap.parse_args()
    client = connect_frame(args.frame, args.pid, args.kiana_install)

    args.output.mkdir(parents=True, exist_ok=True)
    for resource_id in args.resource_ids:
        target = args.output / f"RID{resource_id}.png"
        if target.exists() and target.stat().st_size > 0:
            print(f"{resource_id}: already exported", flush=True)
            continue
        try:
            result = client.call("save_texture", {"resource_id": resource_id, "output_path": str(target), "mip": 0, "slice": -1})
            print(f"{resource_id}: {result}", flush=True)
        except Exception as exc:
            print(f"{resource_id}: ERROR {exc}", flush=True)


if __name__ == "__main__":
    main()
