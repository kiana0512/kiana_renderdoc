param(
  [string]$CaptureDll = "$PSScriptRoot/../../../x64/Development/kiana_renderdoc.dll"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../../..").Path
$capture = (Resolve-Path $CaptureDll).Path
$build = Join-Path $repo 'build-crash-diagnostics'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vs = & $vswhere -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$vs) { throw 'MSVC x64 tools not found' }
$compile = @"
@echo off
call "$vs\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /EHsc /MD "$PSScriptRoot\crash_diagnostics.cpp" /Fe:"$build\crash_diagnostics.exe" /Fo:"$build\crash_diagnostics.obj"
exit /b %errorlevel%
"@
$batch = Join-Path $build 'compile.cmd'
Set-Content -LiteralPath $batch -Value $compile -Encoding ascii
$saved = @{}
foreach ($name in @('KIANA_UNITY_SAFE_MODE', 'KIANA_CRASH_DIAGNOSTICS', 'KIANA_CRASH_LOG')) {
  $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
Push-Location $build
try {
  & $env:ComSpec /d /c $batch
  if ($LASTEXITCODE -ne 0) { throw 'Diagnostic fixture build failed' }
  $env:KIANA_UNITY_SAFE_MODE = '1'
  foreach ($mode in @('off', 'on')) {
    # Every run gets a fresh path, so a previous log cannot satisfy this assertion.
    $log = Join-Path $build ("fixture-$mode-" + [guid]::NewGuid().ToString('N') + '.log')
    $env:KIANA_CRASH_DIAGNOSTICS = $(if ($mode -eq 'on') { '1' } else { '0' })
    $env:KIANA_CRASH_LOG = $log
    $process = Start-Process -FilePath "$build/crash_diagnostics.exe" -ArgumentList "`"$capture`"" -PassThru -WindowStyle Hidden
    if (!$process.WaitForExit(30000)) {
      $process.Kill()
      throw "$mode diagnostic test timed out"
    }
    if ($process.ExitCode -ne 999) { throw "$mode changed exit code to $($process.ExitCode)" }
    if ($mode -eq 'on') {
      $text = Get-Content -LiteralPath $log -Raw
      if ($text -notmatch 'first-chance exception code=0xc0000005' -or
          $text -notmatch 'ExitProcess code=0x000003e7 \(999\)') {
        throw 'Observer did not record the exception and original exit'
      }
    } elseif (Test-Path -LiteralPath $log) {
      throw 'Disabled diagnostics unexpectedly wrote a log'
    }
    Write-Output "PASS: diagnostics $mode, SEH continues, exit code remains 999"
  }
} finally {
  Pop-Location
  foreach ($name in $saved.Keys) {
    [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process')
  }
}
