"""Check EID1273's Eye_E vertex texture lookup against captured VSOut v5.

Usage: python audit_eye_vertex_lookup.py EID1273_KMF.bytes EID1273.vsout.bin RID23285.png
The source VS converts IA COLOR0.r to an 8-bit index, splits nibbles into
the 16x16 Eye_E texel address, and writes 2*RGB, alpha to PS v5.
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main(kmf_path: Path, vsout_path: Path, texture_path: Path):
    raw = kmf_path.read_bytes()
    if raw[:4] != b"KMF1":
        raise ValueError("KMF1 expected")
    count, _ = struct.unpack_from("<II", raw, 4)
    color_offset = 12 + count * 10 * 4
    colors = np.frombuffer(raw, "<f4", count=count * 4,
                           offset=color_offset).reshape(count, 4)
    vsraw = vsout_path.read_bytes()
    stride = len(vsraw) // count
    if len(vsraw) != count * stride or stride != 132:
        raise ValueError("Unexpected EID1273 VSOut stride")
    # Position occupies the first 16 bytes; o0..o4 occupy 72 more bytes.
    v5 = np.stack([np.frombuffer(vsraw, "<f4", count=4, offset=i * stride + 88)
                   for i in range(count)])
    texels = np.asarray(Image.open(texture_path).convert("RGBA"), np.float32) / 255
    if texels.shape != (16, 16, 4):
        raise ValueError("Eye_E should be 16x16")
    packed = np.clip((colors[:, 0] * 255 + 0.5).astype(np.int32), 0, 255)
    x = packed & 15
    source_y = 15 - (packed >> 4)
    results = {}
    for label, png_y in (("sameRow", source_y), ("flippedRow", 15 - source_y)):
        expected = texels[png_y, x].copy()
        expected[:, :3] *= 2
        error = np.abs(expected - v5)
        results[label] = {"meanAbsError": float(error.mean()),
                          "maxAbsError": float(error.max()),
                          "matchingVertices1e-4": int((error.max(axis=1) < 1e-4).sum())}
    print(json.dumps({"vertexCount": count, "vsoutStride": stride,
                      "firstPackedIndex": int(packed[0]),
                      "firstCapturedV5": v5[0].tolist(),
                      "rowOrientations": results}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*(Path(p) for p in sys.argv[1:]))
