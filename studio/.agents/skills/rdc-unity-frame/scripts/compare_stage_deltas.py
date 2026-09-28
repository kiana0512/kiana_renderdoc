"""Count changed pixels and bounding rectangles between successive RDC RT snapshots.

Usage: python compare_stage_deltas.py SNAPSHOT_DIR EID_A EID_B [EID_C ...]
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main(directory: Path, eids):
    report = []
    for before, after in zip(eids, eids[1:]):
        a = np.asarray(Image.open(directory / f"EID{before}-RID53242.png").convert("RGB"), np.int16)
        b = np.asarray(Image.open(directory / f"EID{after}-RID53242.png").convert("RGB"), np.int16)
        changed = np.max(np.abs(a - b), axis=2) > 1
        yy, xx = np.where(changed)
        report.append({"from": before, "to": after,
                       "changedPixels": int(changed.sum()),
                       "boundingRect": ([int(xx.min()), int(yy.min()),
                                         int(xx.max()) + 1, int(yy.max()) + 1]
                                        if xx.size else None)})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), [int(eid) for eid in sys.argv[2:]])
