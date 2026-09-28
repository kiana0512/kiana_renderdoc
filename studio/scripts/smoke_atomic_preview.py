import hashlib
import json
import os
import sys
from pathlib import Path

SOURCE_ROOT = Path(r"E:\renderdoc")
KIANA_MCP = SOURCE_ROOT / "kiana" / "mcp"
sys.path.insert(0, str(KIANA_MCP))

from src.ipc_client import IPCClient


capture = r"E:\KianaFrame38112Workspace\Frame38112Capture\capture_frame38112.rdc"
out = Path(r"E:\KianaStudioElectron\test-results\composition-smoke")
out.mkdir(parents=True, exist_ok=True)
client = IPCClient(timeout=180)
client.call("open_capture", {"capture_path": capture}, timeout=180)

cases = [
    (19, 1181, "precompute-01"),
    (36, 1181, "precompute-02"),
    (51, 1181, "precompute-03"),
    (945, 53242, "gbuffer-character"),
    (1610, 53234, "transparent-cloth"),
    (2200, 1181, "ui-clear"),
    (2223, 1181, "ui-first-draw"),
    (2487, 1181, "ui-mid"),
    (3199, 1181, "ui-main-state"),
    (3299, 1181, "ui-last-layer"),
]

results = []
for eid, rid, label in cases:
    path = out / f"eid-{eid}-rid-{rid}-{label}.png"
    reply = client.call(
        "save_texture",
        {
            "event_id": eid,
            "resource_id": rid,
            "output_path": str(path),
            "mip": 0,
            "slice": -1,
        },
        timeout=180,
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
    results.append(
        {
            "eventId": eid,
            "resourceId": rid,
            "label": label,
            "path": str(path),
            "bytes": path.stat().st_size if path.exists() else 0,
            "sha256": digest,
            "reply": reply,
        }
    )

print(json.dumps({"pid": os.environ.get("KIANA_PID"), "results": results}, ensure_ascii=False, indent=2))
