"""Compare an outline draw's RDC/Unity changed-pixel coverage and RT0 color."""

import argparse
import json

import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-before", required=True)
    parser.add_argument("--source-after", required=True)
    parser.add_argument("--unity-before", required=True)
    parser.add_argument("--unity-after", required=True)
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    args = parser.parse_args()
    sb, sa, ub, ua = map(load, (args.source_before, args.source_after,
                                args.unity_before, args.unity_after))
    if not (sb.shape == sa.shape == ub.shape == ua.shape):
        raise ValueError("Image dimensions differ")
    sm = np.max(np.abs(sa - sb), axis=2) > 1
    um = np.max(np.abs(ua - ub), axis=2) > 1
    if args.roi:
        x0, y0, x1, y1 = args.roi
        roi = np.zeros(sm.shape, bool)
        roi[y0:y1, x0:x1] = True
        sm &= roi
        um &= roi
    overlap = sm & um
    union = sm | um
    diff = np.abs(sa - ua)
    if args.roi:
        region = roi
    else:
        region = np.ones(sm.shape, bool)
    result = {
        "sourceChangedPixels": int(sm.sum()),
        "unityChangedPixels": int(um.sum()),
        "overlapPixels": int(overlap.sum()),
        "sourceRecall": float(overlap.sum() / max(sm.sum(), 1)),
        "unityPrecision": float(overlap.sum() / max(um.sum(), 1)),
        "changedRGBMAE": float(diff[sm].mean()),
        "overlapRGBMAE": float(diff[overlap].mean()) if overlap.any() else None,
        "unionRGBMAE": float(diff[union].mean()),
        "regionRGBMAE": float(diff[region].mean()),
        "falsePositivePixels": int((um & ~sm).sum()),
        "falseNegativePixels": int((sm & ~um).sum()),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
