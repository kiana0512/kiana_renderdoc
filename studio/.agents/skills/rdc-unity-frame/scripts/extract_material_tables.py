"""Extract dynamic per-band material constants from the body shader family.

Usage: python extract_material_tables.py PIXEL_CBUFFERS_ALL.json OUTPUT.json
The disassembly uses cb3[band+5], cb3[band+10] and cb3[band+15]; a
static register scanner does not include these dynamic lookups.
"""

import hashlib
import json
import sys
from pathlib import Path


def main(source: Path, output: Path):
    data = json.loads(source.read_text(encoding="utf-8"))
    draws = []
    for event in data["events"]:
        if event["pixelShaderId"] not in (31475, 42681, 33678):
            continue
        buffers = {b["slot"]: b["float4s"] for b in event["pixelConstantBuffers"]}
        cb0, cb3 = buffers[0], buffers[3]
        bands = []
        for band in range(5):
            tint = cb3[band + 5]
            layer = cb3[band + 10]
            mode = cb3[band + 15]
            bands.append({"band": band, "tint": tint[:3],
                          "arraySlice": layer[0], "weight": layer[1],
                          "strengthCap": layer[2], "mode": mode[1],
                          "uvScale": cb3[band][:2], "uvOffset": cb3[band][2:]})
        fingerprint = hashlib.sha256(json.dumps(bands).encode()).hexdigest()[:12]
        draws.append({"eid": event["eventId"], "pixelShader": event["pixelShaderId"],
                      "tableFingerprint": fingerprint,
                      "active": cb0[24][2] >= 0.5,
                      "normalProjectionRows": [cb0[i][:3] for i in (119, 120, 121)],
                      "normalProjectionScale": cb0[42][1],
                      "albedoMultiplier": cb3[38][:3],
                      "bands": bands})
    result = {"frame": 38112, "shaderFamily": [31475, 42681, 33678], "draws": draws,
              "uniqueTables": len(set(d["tableFingerprint"] for d in draws))}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{len(draws)} draws, {result['uniqueTables']} unique band tables -> {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
