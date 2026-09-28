"""Keep only PS constant-buffer registers referenced by each G-buffer shader.

The full dump comes from inspect_pixel_cbuffers.py. This report is evidence for
porting shader branches, not a claim that Unity implements them yet.
"""

import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--shader-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dump = json.loads(args.dump.read_text(encoding="utf-8"))
    if not dump["ok"]:
        raise RuntimeError("Full pixel constant-buffer dump has replay errors")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    events = {event["eventId"]: event for event in dump["events"]}
    representative = {}
    for binding in manifest["events"]:
        candidate = args.shader_dir / f"EID{binding['eventId']}-fragment.txt"
        if candidate.exists():
            representative[binding["fragmentShader"]] = candidate
    result = {"frame": 38112, "pass": 5, "draws": []}
    for binding in manifest["events"]:
        eid = binding["eventId"]
        event = events[eid]
        shader = representative[binding["fragmentShader"]]
        source = shader.read_text(encoding="utf-8")
        registers = {}
        for instruction in re.findall(r"^\s*\d+:.*$", source, flags=re.MULTILINE):
            for slot, index in re.findall(r"\bcb(\d+)\[(\d+)\]", instruction):
                registers.setdefault(int(slot), set()).add(int(index))
        buffers = {item["slot"]: item for item in event["pixelConstantBuffers"]}
        used = {}
        for slot, indices in sorted(registers.items()):
            buffer = buffers.get(slot)
            if not buffer or not buffer.get("float4s"):
                raise RuntimeError(f"EID {eid}: referenced cb{slot} is unbound")
            data = buffer["float4s"]
            if max(indices) >= len(data):
                raise RuntimeError(f"EID {eid}: cb{slot}[{max(indices)}] exceeds {len(data)} float4s")
            used[str(slot)] = {str(index): data[index] for index in sorted(indices)}
        result["draws"].append({
            "eventId": eid,
            "pixelShaderId": event["pixelShaderId"],
            "shaderDisassembly": shader.name,
            "usedConstantRegisters": used,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(result['draws'])} draws to {args.output}")


if __name__ == "__main__":
    main()
