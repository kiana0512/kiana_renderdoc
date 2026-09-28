"""Extract PS31478/31479 per-draw color bands from captured PS cb3.

Usage: python extract_outline_material_tables.py PIXEL_CBUFFERS_ALL.json OUTPUT.json
PS31479 chooses cb3[49..53] from t3.r thresholds 0.2/0.4/0.6/0.8.
PS31478 chooses cb3[36..38] from v5.w thresholds 0.6/0.8.
"""

import json
import sys
from pathlib import Path


def main(source: Path, output: Path):
    data = json.loads(source.read_text(encoding="utf-8"))
    draws = []
    for event in data["events"]:
        ps = event["pixelShaderId"]
        if ps not in (31478, 31479):
            continue
        buffers = {b["slot"]: b["float4s"] for b in event["pixelConstantBuffers"]}
        cb3 = buffers[3]
        start = 49 if ps == 31479 else 36
        count = 5 if ps == 31479 else 3
        record = {
            "eid": event["eventId"],
            "pixelShader": ps,
            "bands": [{"band": i, "color": cb3[start + i]} for i in range(count)],
        }
        if ps == 31479:
            record["albedoMultiplier"] = cb3[38]
        draws.append(record)
    result = {"frame": 38112, "shaderFamily": [31478, 31479], "draws": draws}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{len(draws)} outline draws -> {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
