param(
  [string]$CaptureDll = "$PSScriptRoot/../../../x64/Development/kiana_renderdoc.dll"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../../..").Path
$capture = (Resolve-Path $CaptureDll).Path
$build = Join-Path $repo 'build-early-exports'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vs = & $vswhere -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$vs) { throw 'MSVC x64 tools not found' }
$compile = @"
@echo off
call "$vs\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /EHsc /MD /guard:cf /I"$repo" "$PSScriptRoot\early_exports.cpp" /Fe:"$build\early_exports.exe" /Fo:"$build\early_exports.obj" /link dxguid.lib /guard:cf
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /EHsc /MD /guard:cf /LD "$PSScriptRoot\early_exports_consumer.cpp" /Fe:"$build\early_exports_consumer.dll" /Fo:"$build\early_exports_consumer.obj" /link d3d12.lib /guard:cf
exit /b %errorlevel%
"@
$batch = Join-Path $build 'compile.cmd'
Set-Content -LiteralPath $batch -Value $compile -Encoding ascii
Push-Location $build
try {
  & $env:ComSpec /d /c $batch
  if ($LASTEXITCODE -ne 0) { throw 'Regression fixture build failed' }
  foreach ($mode in @('cold', 'warm')) {
    $stdout = Join-Path $build "$mode.stdout.txt"
    $stderr = Join-Path $build "$mode.stderr.txt"
    $process = Start-Process -FilePath "$build/early_exports.exe" -ArgumentList @(
      "`"$capture`"", "`"$build\early_exports_consumer.dll`"", $mode
    ) -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (!$process.WaitForExit(60000)) {
      $process.Kill()
      throw "$mode test timed out"
    }
    $process.WaitForExit()
    Get-Content -LiteralPath $stdout
    Get-Content -LiteralPath $stderr
    if ($process.ExitCode -ne 0) { throw "$mode test failed with exit code $($process.ExitCode)" }
  }
} finally {
  Pop-Location
}
