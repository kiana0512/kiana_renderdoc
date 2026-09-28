"""Compare two Unity candidates to an RDC target in one exact pixel rectangle.

Usage: python compare_stage_region.py SOURCE.png CANDIDATE_A.png CANDIDATE_B.png X0 Y0 X1 Y1
Coordinates use the PNG's top-left origin; upper bounds are exclusive.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main(source_path: Path, a_path: Path, b_path: Path, box):
    source = np.asarray(Image.open(source_path).convert("RGB"), np.int16)
    a = np.asarray(Image.open(a_path).convert("RGB"), np.int16)
    b = np.asarray(Image.open(b_path).convert("RGB"), np.int16)
    if a.shape != source.shape or b.shape != source.shape:
        raise ValueError("Images must have equal dimensions")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= source.shape[1] and 0 <= y0 < y1 <= source.shape[0]):
        raise ValueError("Invalid rectangle")
    src = source[y0:y1, x0:x1]
    selected = src.max(axis=2) > 8
    report = {"box": box, "sourceForegroundPixels": int(selected.sum())}
    for name, arr in (("candidateA", a), ("candidateB", b)):
        image = arr[y0:y1, x0:x1]
        overlap = selected & (image.max(axis=2) > 8)
        report[name] = {
            "overlapPixels": int(overlap.sum()),
            "rgbMAEInOverlap": float(np.abs(src[overlap] - image[overlap]).mean())
            if overlap.any() else None,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise SystemExit(__doc__)
    main(*(Path(v) for v in sys.argv[1:4]), [int(v) for v in sys.argv[4:]])
