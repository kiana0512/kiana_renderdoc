@echo off
setlocal
set "KIANA_UNITY_SAFE_MODE=1"
set "KIANA_EXPORT_IDENTITY=1"
set "KIANA_D3D11_CAPTURE_OVERRIDE=1"
start "Kiana RenderDoc - Genshin capture" "%~dp0kiana_qrenderdoc.exe" %*
endlocal
