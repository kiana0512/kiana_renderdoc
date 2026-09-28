"""Inventory texture slots referenced by each exported G-buffer pixel shader.

Usage: python analyze_shader_texture_slots.py BINDINGS.json SHADERS_DIR
The result records static references, not proof that a runtime branch sampled it.
"""

import json
import re
import sys
from pathlib import Path


def main(manifest_path: str, shader_dir: str) -> None:
    events = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["events"]
    rows = []
    for event in events:
        eid = event["eventId"]
        path = Path(shader_dir) / f"EID{eid}-fragment.txt"
        if not path.exists():
            # Multiple draws share a shader. Use a representative disassembly.
            representative = next((v for v in events
                                   if v["fragmentShader"] == event["fragmentShader"]
                                   and (Path(shader_dir) / f"EID{v['eventId']}-fragment.txt").exists()), None)
            if representative is None:
                raise FileNotFoundError(f"No pixel shader for EID {eid}")
            path = Path(shader_dir) / f"EID{representative['eventId']}-fragment.txt"
        disassembly = path.read_text(encoding="utf-8")
        instruction_lines = [line for line in disassembly.splitlines()
                             if re.match(r"\s*\d+:\s", line)]
        structured = sorted({int(slot) for slot in re.findall(
            r"dcl_resource_structured\s+t(\d+)", disassembly)})
        used = sorted({int(slot) for line in instruction_lines
                       if re.search(r"\b(sample|gather|ld|resinfo)", line)
                       for slot in re.findall(r"\bt(\d+)\.", line)
                       if int(slot) not in structured})
        bound = sorted({texture["slot"] for texture in event["textures"]
                        if texture["stage"] == "fragment"})
        rows.append({"eventId": eid, "pixelShader": event["fragmentShader"],
                     "disassembly": path.name, "boundFragmentSlots": bound,
                     "structuredBufferSlots": structured,
                     "referencedFragmentSlots": used,
                     "boundButUnreferenced": sorted(set(bound) - set(used)),
                     "referencedButUnbound": sorted(set(used) - set(bound))})
    print(json.dumps({"events": rows}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
