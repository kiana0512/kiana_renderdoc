"""Extract the face pixel shader's fixed cb3 color/shading rows.

Usage: python extract_face_material_tables.py PIXEL_CBUFFERS_ALL.json OUTPUT.json
PS31476 and PS31480 use cb3[29..35] as the base multiplier,
highlight tint and face shade colors. The eye PS31489 is separate.
"""

import json
import sys
from pathlib import Path


def main(source: Path, output: Path):
    events = json.loads(source.read_text(encoding="utf-8"))["events"]
    draws = []
    for event in events:
        if event["pixelShaderId"] not in (31476, 31480):
            continue
        cb3 = next(b["float4s"] for b in event["pixelConstantBuffers"] if b["slot"] == 3)
        draws.append({"eid": event["eventId"], "pixelShader": event["pixelShaderId"],
                      "colorRows": [{"register": index, "value": cb3[index]}
                                    for index in range(29, 36)]})
    result = {"frame": 38112, "shaderFamily": [31476, 31480], "draws": draws}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{len(draws)} face draws -> {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
