param(
  [string]$Destination = 'E:\renderdoc\dist\Kiana-1.47-v12-release-x64',
  [string]$PythonRuntime = 'C:\Users\rentian\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$build = Join-Path $repo 'x64\Development'
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$required = @('kiana_qrenderdoc.exe','kiana_renderdoc.dll','kiana_renderdoccmd.exe',
  'kiana_renderdocshim64.dll','kiana_renderdocui.exe','kiana_renderdoc.json',
  'python36.dll','python36.zip','_ctypes.pyd','d3dcompiler_47.dll','dbghelp.dll',
  'symsrv.dll','Qt5Core.dll','Qt5Gui.dll','Qt5Widgets.dll','Qt5Network.dll','Qt5Svg.dll','renderdoc_app.h')
foreach ($name in $required) {
  Copy-Item -LiteralPath (Join-Path $build $name) -Destination $Destination -Force
}
foreach ($name in @('pymodules','qtplugins')) {
  Copy-Item -LiteralPath (Join-Path $build $name) -Destination $Destination -Recurse -Force
}
foreach ($name in @('extensions','mcp','requirements.txt','requirements.lock.txt','README.md','VALIDATION.md','VALIDATION_V12.md','GAME_LAUNCH_PRESETS.md','DEBUGGING_AND_USAGE_CN.md','LICENSE.RenderDocMCP2','configure_mcp.cmd','launch-export-identity.cmd','launch-genshin-capture.cmd')) {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $Destination -Recurse -Force
}
$gfxDest = Join-Path $Destination 'tools\gfxreconstruct'
New-Item -ItemType Directory -Force -Path $gfxDest | Out-Null
Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'thirdparty\gfxreconstruct') |
  Copy-Item -Destination $gfxDest -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repo 'LICENSE.md') -Destination $Destination
Copy-Item -LiteralPath (Join-Path $repo 'renderdoc\3rdparty\minhook\LICENSE.txt') -Destination (Join-Path $Destination 'LICENSE.MinHook.txt')
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vs = & $vswhere -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$crt = Get-ChildItem (Join-Path $vs 'VC/Redist/MSVC') -Directory | Sort-Object Name -Descending |
  ForEach-Object { Join-Path $_.FullName 'x64/Microsoft.VC145.CRT' } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (!$crt) { throw 'MSVC x64 redistributable runtime not found' }
Get-ChildItem -LiteralPath $crt -Filter '*.dll' | Copy-Item -Destination $Destination -Force
$licenses = Join-Path $Destination 'licenses'
New-Item -ItemType Directory -Force $licenses | Out-Null
foreach ($component in @('qt','python','scintilla','toolwindowmanager')) {
  $componentDir = Join-Path $repo "qrenderdoc/3rdparty/$component"
  Get-ChildItem -LiteralPath $componentDir -File | Where-Object { $_.Name -match '^(LICENSE|COPYING)' } |
    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $licenses ($component + '-' + $_.Name)) }
}
$runtimeDest = Join-Path $Destination 'python_mcp'
if (!(Test-Path -LiteralPath $runtimeDest)) {
  Copy-Item -LiteralPath $PythonRuntime -Destination $runtimeDest -Recurse
}
& uv pip install --python (Join-Path $runtimeDest 'python.exe') --break-system-packages -r (Join-Path $Destination 'requirements.lock.txt')
if ($LASTEXITCODE) { throw 'MCP dependency installation failed' }
$clientConfig = @{mcpServers = @{kiana = @{
  command = (Join-Path $runtimeDest 'python.exe')
  args = @((Join-Path $Destination 'mcp\launch.py'))
  env = @{PYTHONUTF8='1';KIANA_HOME=$Destination}
}}}
$clientConfig | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Destination 'mcp-client.json') -Encoding UTF8
Write-Output "Packaged Kiana at $Destination"
& (Join-Path $runtimeDest 'python.exe') (Join-Path $Destination 'mcp\configure.py')
