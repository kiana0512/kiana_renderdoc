"""Measure source-vs-Unity color error by the source shader's t5.x material band."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source_color", type=Path)
    p.add_argument("unity_color", type=Path)
    p.add_argument("unity_mask_debug", type=Path)
    args = p.parse_args()
    source = np.asarray(Image.open(args.source_color).convert("RGB"), np.float32)
    unity = np.asarray(Image.open(args.unity_color).convert("RGB"), np.float32)
    mask = np.asarray(Image.open(args.unity_mask_debug).convert("RGB"), np.float32)
    if source.shape != unity.shape or source.shape != mask.shape:
        raise ValueError("All images must have equal dimensions")
    visible = (source.max(axis=2) > 8) & (unity.max(axis=2) > 8)
    # PS 31475 instructions 58-62: max(4 - floor(t5.x * 5), 0).
    band = np.maximum(4 - np.floor(mask[:, :, 0] / 255 * 5).astype(np.int16), 0)
    result = []
    for index in range(5):
        select = visible & (band == index)
        if not np.any(select):
            continue
        diff = source[select] - unity[select]
        result.append({"band": index, "pixels": int(select.sum()),
                       "meanAbsError": float(np.abs(diff).mean()),
                       "meanSourceMinusUnity": np.round(diff.mean(axis=0), 3).tolist()})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
