# Early Windows graphics hooks regression

Run `./util/test/hooks/test_early_exports.ps1` from the repository after building the
x64 Development capture DLL, or specify `-CaptureDll <absolute DLL path>`.
Requires MSVC, Windows 10 with D3D12/WARP, and the capture DLL's dependencies.

The fixture loads the capture DLL before a consumer DLL, using cached native loader
and resolver functions to bypass the ordinary post-LoadLibrary IAT scan. The consumer
calls D3D12CreateDevice in both its TLS callback and DllMain. Tests cover:

- Cold and already-loaded D3D12 providers, and consumer unload/reload.
- Import resolution and dynamic lookup by name/ordinal; missing exports remain absent.
- D3D12 SDK configuration and DXGI factory creation.
- A real WARP device registered with the capture API, including capture start/discard.
- Original instruction restoration, cached export pointers, and repeated RemoveHooks.

Both test binaries are compiled with CFG. The deliberately cached native GetProcAddress
call alone uses a `guard(nocf)` helper because this system resolver is CFG-suppressed on
the test OS; graphics calls retain CFG checks. No process or system mitigations are changed.
The invalid-interface probes also verify that an early rejected device query does not
leave the D3D12 wrapper's recursion guard set for the following valid device creation.

Build products and per-process stdout/stderr are in ignored `build-early-exports/`.
This is a local regression test; it does not launch or validate a game.

## Kiana v12 compatibility and diagnostics

To exercise graphics export address identity and D3D11 outputs, run from a fresh
PowerShell process after building:

```powershell
$env:KIANA_UNITY_SAFE_MODE = '1'
$env:KIANA_EXPORT_IDENTITY = '1'
$env:KIANA_D3D11_CAPTURE_OVERRIDE = '0'
./util/test/hooks/test_early_exports.ps1
$env:KIANA_D3D11_CAPTURE_OVERRIDE = '1'
./util/test/hooks/test_early_exports.ps1
./util/test/hooks/test_crash_diagnostics.ps1
```

The export fixture checks DXGI/D3D11/D3D12 resolver identity, wrapped D3D11 WARP
capture, and both device/context and context-only outputs with device wrapping
disabled or explicitly enabled. The diagnostic fixture verifies that observation
does not consume an SEH exception or change `ExitProcess(999)`; disabled diagnostics
must not write a log. Its outputs are in ignored `build-crash-diagnostics/`.
