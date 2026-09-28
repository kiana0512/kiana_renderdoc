# Kiana source layout

This is a source snapshot of the local Kiana workbench and modified RenderDoc tree.

- `renderdoc/`, `qrenderdoc/`, `renderdoccmd/`, `renderdocshim/`, `util/`: modified RenderDoc source and build files, based on upstream `v1.x` at `755ab65`.
- `kiana/`: Kiana capture bridge, MCP server, packaging scripts, and tests for the modified RenderDoc runtime.
- `studio/`: Kiana Studio Electron/React/TypeScript workbench. Its original instructions are in [`studio/README.md`](studio/README.md).
- `studio/.agents/skills/`: reusable RDC and Unity investigation scripts and skill documentation.
- `studio/docs/`: text reports and machine-readable analysis manifests. Large validation screenshots and capture outputs are intentionally kept out of Git.

## Build the workbench

```powershell
cd studio
npm ci
npm run typecheck
npm run build
```

For the desktop development app, run `npm run dev`. The workbench expects a locally built Kiana RenderDoc runtime; see [`kiana/README.md`](kiana/README.md) and the original RenderDoc [Windows build instructions](docs/CONTRIBUTING/Compiling.md). The Git repository contains source and required checked-in assets, not a compiled installer or an RDC capture.

The RenderDoc portions retain their original [MIT license](LICENSE.md). Check component-specific notices under `kiana/` and `studio/` for bundled dependencies.
