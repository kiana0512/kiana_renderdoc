# DXBC to HLSL

Use this workflow for repeatable RenderDoc shader extraction and Unity pipeline reconstruction.

## Tool chain

- `scripts/export_shader_raw_batch.py` opens the RDC once and exports the bound vertex and pixel shader DXBC containers for every requested EID.
- `scripts/run_bundled_renderdoc_python.ps1` hosts the custom RenderDoc `renderdoc.pyd` in its matching embedded Python 3.6 runtime. Do not import that module from system Python.
- `scripts/export_decompile_shaders.ps1` invokes the exporter and decompiles every exported container to HLSL.
- The supported decompiler is `coconutbird/d3dasm` at commit `a292206`. Its required `napbat/cfglib` sibling is pinned to `6e57c16`. Record both commits in the output manifest.

Default tool locations are `E:\KianaTools\d3dasm` and `E:\napbat\cfglib`. Override `-Decompiler` when another verified binary is used.

## Invocation

```powershell
scripts/export_decompile_shaders.ps1 `
  -Capture 'E:\capture.rdc' `
  -EventIds 1403,1419,1429,1447,1466,1484,1511 `
  -OutputDirectory 'E:\analysis\deferred-lighting-shaders'
```

The output directory contains `EID<id>-VS.dxbc`, `EID<id>-PS.dxbc`, matching `.hlsl` files and `shader-decompile-manifest.json` with capture and shader hashes.

## Reconstruction contract

For each EID, save these items together:

1. Raw VS and PS DXBC plus SHA-256.
2. Decompiled HLSL and decompiler commit.
3. Pixel and vertex constant-buffer bytes or float4 values.
4. Read-only and read-write resource slots, texture formats, dimensions, mips and array slices.
5. Sampler filters, addressing, LOD and bias.
6. Rasterizer, depth, stencil, blend and write-mask state.
7. Render-target and depth/stencil formats.
8. A captured same-EID output used only as an offline oracle.
9. A native Unity same-EID output and numerical/visual comparison.

Keep one Unity pass/module per source EID while validating. Preserve stencil routing and additive/overwrite behavior; merging passes before their outputs match makes errors impossible to localize.

## State translation traps

- RenderDoc's `CompareFunction` values come from `renderdoc/api/replay/replay_enums.h`; they are not the numeric `D3D12_COMPARISON_FUNC` values. In the current API, value `6` is `Equal` and value `7` is `NotEqual`. Translate by enum name or RenderDoc header, never by the D3D numeric table.
- A deferred lighting pass can depend on stencil bits written by an earlier depth/prepass that is outside the selected G-buffer draw range. Reconstruct those writes before judging the pixel shader. Frame 38112 requires character-family bit `0x80`; EID1419 selects it with reference `144` and read mask `160`.
- A depth resource can appear under a second resource ID/view when bound as an SRV. Frame 38112 uses D32S8 resource `53238` as the depth target and its sampleable view/resource `53259` in deferred pixel shaders. Treat them as the same underlying depth contract.
- Keep experimental stage output behind an explicit routing switch. A generated shader compiling successfully is not evidence that its register bindings, stencil selection or color result are correct.

Decompiler output can rename registers and restructure control flow. Do not infer semantic names such as AO, skin, or fog from temporary variables alone. Confirm each meaning from bindings, source values and final data flow. Never present a captured attachment as a Unity render.
