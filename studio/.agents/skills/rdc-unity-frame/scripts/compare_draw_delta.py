"""Compare multiple Unity stages only where the current RDC draw changes RT0."""
import json
import sys
from PIL import Image
import numpy as np


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


source_before, source_after = load(sys.argv[1]), load(sys.argv[2])
mask = np.max(np.abs(source_after - source_before), axis=2) > 1
result = {"changedPixels": int(mask.sum()), "candidates": []}
for path in sys.argv[3:]:
    candidate = load(path)
    diff = np.abs(candidate - source_after)
    result["candidates"].append({
        "path": path,
        "changedRGBMAE": float(diff[mask].mean()),
        "samples": {f"{x},{y}": {
            "source": source_after[y, x].tolist(),
            "unity": candidate[y, x].tolist(),
        } for x, y in [(930, 580), (940, 600), (950, 605)]},
    })
print(json.dumps(result, ensure_ascii=False, indent=2))
