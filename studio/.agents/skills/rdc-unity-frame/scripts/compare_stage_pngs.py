"""Compare a Unity stage PNG with the same RDC render-target snapshot.

Usage: python compare_stage_pngs.py RDC.png UNITY.png [--diff-output DIFF.png]
Both files must use the same target dimensions and orientation.
"""

import argparse
import json

import numpy as np
from PIL import Image


def main(source_path: str, unity_path: str, diff_output: str | None) -> None:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.int16)
    unity = np.asarray(Image.open(unity_path).convert("RGB"), dtype=np.int16)
    if source.shape != unity.shape:
        raise ValueError(f"Image sizes differ: {source.shape} vs {unity.shape}")
    source_mask = np.max(source, axis=2) > 8
    unity_mask = np.max(unity, axis=2) > 8
    intersection = source_mask & unity_mask
    union = source_mask | unity_mask
    difference = np.abs(source - unity).astype(np.float32)
    if diff_output:
        heat = np.clip(difference.mean(axis=2) * 3, 0, 255).astype(np.uint8)
        output = np.stack((heat, heat // 4, np.zeros_like(heat)), axis=2)
        Image.fromarray(output, "RGB").save(diff_output)
    print(json.dumps({
        "source": source_path,
        "unity": unity_path,
        "width": source.shape[1],
        "height": source.shape[0],
        "sourceForegroundPixels": int(source_mask.sum()),
        "unityForegroundPixels": int(unity_mask.sum()),
        "foregroundIoU": float(intersection.sum() / max(union.sum(), 1)),
        "rgbMAEInIntersection": float(difference[intersection].mean()) if intersection.any() else None,
        "rgbMAEInUnion": float(difference[union].mean()) if union.any() else None,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("unity")
    parser.add_argument("--diff-output")
    options = parser.parse_args()
    main(options.source, options.unity, options.diff_output)
