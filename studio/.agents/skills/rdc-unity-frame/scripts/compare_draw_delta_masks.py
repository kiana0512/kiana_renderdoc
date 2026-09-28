"""Compare which pixels one RDC draw changes against one Unity candidate.

Usage: python compare_draw_delta_masks.py SOURCE_BEFORE SOURCE_AFTER UNITY_BEFORE UNITY_AFTER
"""

import json
import sys

import numpy as np
from PIL import Image


def rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def main(paths):
    source_before, source_after, unity_before, unity_after = map(rgb, paths)
    if len({x.shape for x in (source_before, source_after, unity_before, unity_after)}) != 1:
        raise ValueError("Stage images must have identical dimensions")
    source = np.max(np.abs(source_after - source_before), axis=2) > 1
    unity = np.max(np.abs(unity_after - unity_before), axis=2) > 1
    intersection = source & unity
    union = source | unity
    yy, xx = np.where(unity)
    report = {
        "sourceChangedPixels": int(source.sum()),
        "unityChangedPixels": int(unity.sum()),
        "overlapPixels": int(intersection.sum()),
        "maskIoU": float(intersection.sum() / max(union.sum(), 1)),
        "recall": float(intersection.sum() / max(source.sum(), 1)),
        "precision": float(intersection.sum() / max(unity.sum(), 1)),
        "unityBoundingRect": [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
        if xx.size else None,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
