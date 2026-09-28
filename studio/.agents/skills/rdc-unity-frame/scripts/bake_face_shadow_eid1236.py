"""Bake the RDC EID1236 stencil-limited face darkening as a capture projection.

The 1202 and 1236 RT0 images are consecutive color stages. Their ratio is
stored on the face surface through the captured world-to-clip projection, so
Scene and Game cameras sample the same 3D-attached shadow.
"""
from pathlib import Path

import numpy as np
from PIL import Image


snapshots = Path(r"E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-snapshots")
destination = Path(r"F:/KianaFrame38112Unity/Assets/Kiana/Textures/FaceShadowEID1236.png")
before = np.asarray(Image.open(snapshots / "EID1202-RID53242.png").convert("RGB"), dtype=np.float32)
after = np.asarray(Image.open(snapshots / "EID1236-RID53242.png").convert("RGB"), dtype=np.float32)
dark = np.mean(before - after, axis=2) > 3.0
factor = np.clip((after + 0.5) / np.maximum(before + 0.5, 1.0), 0.0, 1.0)
result = np.zeros((*dark.shape, 4), dtype=np.uint8)
result[:, :, :3] = np.uint8(np.rint(factor * 255.0))
result[:, :, 3] = np.uint8(dark * 255)
destination.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(result, "RGBA").save(destination)
print(destination, "dark pixels", int(dark.sum()))
