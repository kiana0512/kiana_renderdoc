"""Backfill per-EID composition semantics into an existing reconstruction manifest.

Usage:
  python enrich_composition_stages.py MANIFEST_PATH

KIANA_PID must identify the headless Kiana RenderDoc instance that already has
the manifest's capture loaded. The normal analysis pipeline writes the same data
for newly generated packages; this utility upgrades older packages in place.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

RENDERDOC_ROOT = Path(os.environ.get("KIANA_SOURCE_ROOT", r"E:\renderdoc"))
sys.path.insert(0, str(RENDERDOC_ROOT / "kiana" / "mcp"))

from src.ipc_client import IPCClient  # noqa: E402
from src.scene_reconstruction import _composition_stages  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: enrich_composition_stages.py MANIFEST_PATH")
    manifest_path = Path(sys.argv[1]).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    action_path = manifest_path.parent / "action-index.json"
    actions = json.loads(action_path.read_text(encoding="utf-8")).get("actions") or []
    client = IPCClient(timeout=120)
    counts = {}
    for module in manifest.get("modules") or []:
        event_range = module.get("event_range") or [0, 0]
        stages = _composition_stages(
            client.call, actions, str(module.get("module") or "auxiliary"),
            int(event_range[0] or 0), int(event_range[1] or 0),
        )
        module["composition_stages"] = stages
        counts[str(module.get("pass_number") or 0)] = len(stages)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"manifest": str(manifest_path), "stage_counts": counts},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
