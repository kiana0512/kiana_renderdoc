"""Print RenderDoc compare and stencil enum values in Kiana's bundled replay ABI."""

import renderdoc as rd
from pathlib import Path

lines = []

for enum_name in ("CompareFunction", "StencilOperation", "CullMode"):
    enum = getattr(rd, enum_name, None)
    lines.append(enum_name)
    if enum is None:
        continue
    for name in dir(enum):
        if name.startswith("_"):
            continue
        try:
            value = getattr(enum, name)
            lines.append("  {} = {}".format(name, int(value)))
        except (TypeError, ValueError, AttributeError):
            pass

Path("F:/KianaStudioElectron/docs/frame38112-renderdoc-enums.txt").write_text("\n".join(lines))
