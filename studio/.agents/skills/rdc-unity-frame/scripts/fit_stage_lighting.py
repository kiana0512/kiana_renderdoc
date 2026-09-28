"""Fit a simple directional test light against one captured G-buffer stage.

This is a diagnostic approximation, not a recovered game lighting model. It
uses source normal RT and compares a Unity albedo-only render to source color.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    for name in ("source_color", "unity_albedo", "source_normals"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    src = np.asarray(Image.open(args.source_color).convert("RGB"), np.float32) / 255
    base = np.asarray(Image.open(args.unity_albedo).convert("RGB"), np.float32) / 255
    encoded = np.asarray(Image.open(args.source_normals).convert("RGB"), np.float32) / 255
    normal = encoded * 2 - 1
    norm = np.linalg.norm(normal, axis=2, keepdims=True)
    normal /= np.maximum(norm, 1e-5)
    # Isolate pale skin; umbrella and purple clothing are outside this range.
    mask = ((base[:, :, 0] > 0.40) &
            (base[:, :, 0] > base[:, :, 1] * 1.07) &
            (base[:, :, 1] > base[:, :, 2] * 1.01) &
            (src.max(axis=2) > 0.1))
    y = (src.sum(axis=2) / np.maximum(base.sum(axis=2), 0.05))[mask]
    n = normal[mask]
    rng = np.random.default_rng(38112)
    take = rng.choice(len(y), min(len(y), 10000), replace=False)
    y, n = y[take], n[take]
    best = None
    directions = rng.normal(size=(1600, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    for direction in directions:
        lambert = np.maximum(n @ direction, 0)
        x = np.stack((np.ones_like(lambert), lambert), axis=1)
        ambient, diffuse = np.linalg.lstsq(x, y, rcond=None)[0]
        if ambient < 0.15 or diffuse < 0:
            continue
        pred = ambient + diffuse * lambert
        error = float(np.mean(np.abs(pred - y)))
        if best is None or error < best["meanAbsoluteRatioError"]:
            best = {"direction": direction.tolist(), "ambient": float(ambient),
                    "diffuse": float(diffuse), "meanAbsoluteRatioError": error}
    result = {"skinSamples": int(len(y)), "baselineRatioMAE": float(np.mean(np.abs(1-y))),
              "fit": best}
    payload = json.dumps(result, indent=2)
    print(payload)
    if args.output:
        args.output.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
