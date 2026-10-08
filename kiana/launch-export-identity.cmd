@echo off
setlocal
set "KIANA_UNITY_SAFE_MODE=1"
set "KIANA_EXPORT_IDENTITY=1"
set "KIANA_D3D11_CAPTURE_OVERRIDE=0"
start "Kiana RenderDoc - export identity compatibility" "%~dp0kiana_qrenderdoc.exe" %*
endlocal
