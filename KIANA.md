# Kiana source layout

This is a source snapshot of the local Kiana workbench and modified RenderDoc tree.

- `renderdoc/`, `qrenderdoc/`, `renderdoccmd/`, `renderdocshim/`, `util/`: modified RenderDoc source and build files, updated to upstream `v1.x` at `4924d00` for Kiana 1.47 v12.
- `kiana/`: Kiana capture bridge, MCP server, packaging scripts, and tests for the modified RenderDoc runtime.
- `studio/`: Kiana Studio Electron/React/TypeScript workbench. Its original instructions are in [`studio/README.md`](studio/README.md).
- `studio/.agents/skills/`: reusable RDC and Unity investigation scripts and skill documentation.
- `studio/docs/`: text reports and machine-readable analysis manifests. Large validation screenshots and capture outputs are intentionally kept out of Git.

## Kiana v12 capture configuration

The 2026-10-08 update integrates the tested Kiana v12 source snapshot (`fce519bc0fbd8d9aa9bf0a0735cc48df32641ec3`) into the existing `main` tree at `96cb6fe`. It preserves Kiana Studio, its capture launcher protocol, and the event-specific vertex-stage and OBJ exports already on `main`. The local upstream checkout and this repository use different source histories, so the update is applied as a source snapshot on top of `main`.

- [Default launch arguments and environment variables for all five games](kiana/GAME_LAUNCH_PRESETS.md)
- [Build, regression, and actual capture validation](kiana/VALIDATION_V12.md)
- [Capture and startup diagnostics](kiana/DEBUGGING_AND_USAGE_CN.md)
- [Native graphics-hook regression instructions](util/test/hooks/README.md)

Star Rail and Honkai Impact 3rd use `launch-export-identity.cmd`; Genshin uses `launch-genshin-capture.cmd`. The compatibility switches are opt-in. Star Rail D3D12 currently produces a black final image, and Genshin's D3D12 argument still selects D3D11 in the tested installation; use the documented D3D11 defaults for those games.

## Build the workbench

```powershell
cd studio
npm ci
npm run typecheck
npm run build
```

For the desktop development app, run `npm run dev`. The workbench expects a locally built Kiana RenderDoc runtime; see [`kiana/README.md`](kiana/README.md) and the original RenderDoc [Windows build instructions](docs/CONTRIBUTING/Compiling.md). The Git repository contains source and required checked-in assets, not a compiled installer or an RDC capture.

The RenderDoc portions retain their original [MIT license](LICENSE.md). Check component-specific notices under `kiana/` and `studio/` for bundled dependencies.
