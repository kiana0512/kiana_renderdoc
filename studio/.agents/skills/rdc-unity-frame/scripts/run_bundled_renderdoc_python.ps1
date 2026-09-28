param(
    [Parameter(Mandatory = $true)]
    [string] $ScriptPath,
    [string[]] $ScriptArgs = @()
)

$runtimeCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Kiana RenderDoc'),
    (Join-Path (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path 'release-next\win-unpacked\resources\kiana-runtime'),
    'F:/KianaStudioElectron/release-next/win-unpacked/resources/kiana-runtime'
)
$runtimeDir = $runtimeCandidates |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ 'python36.dll') } |
    Select-Object -First 1
if (-not $runtimeDir) { throw 'Kiana RenderDoc bundled Python runtime was not found.' }
$runtimeDir = (Resolve-Path -LiteralPath $runtimeDir).Path
$scriptFullPath = (Resolve-Path -LiteralPath $ScriptPath).Path
$previousPath = $env:PATH
$previousPythonHome = $env:PYTHONHOME
$previousPythonPath = $env:PYTHONPATH
$env:PATH = "$runtimeDir;$runtimeDir/pymodules;$env:PATH"
$env:PYTHONHOME = $runtimeDir
$env:PYTHONPATH = "$runtimeDir/pymodules;$runtimeDir/python36.zip"

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class KianaPython36Host
{
    [DllImport("python36.dll", CharSet = CharSet.Unicode, CallingConvention = CallingConvention.Cdecl)]
    public static extern int Py_Main(int argc, IntPtr argv);
}
'@

$arguments = @('python36', $scriptFullPath) + $ScriptArgs
$stringPointers = @($arguments | ForEach-Object { [Runtime.InteropServices.Marshal]::StringToHGlobalUni($_) })
$arrayPointer = [Runtime.InteropServices.Marshal]::AllocHGlobal([IntPtr]::Size * $stringPointers.Count)
try {
    for ($index = 0; $index -lt $stringPointers.Count; $index++) {
        [Runtime.InteropServices.Marshal]::WriteIntPtr($arrayPointer, $index * [IntPtr]::Size, $stringPointers[$index])
    }
    $pythonExitCode = [KianaPython36Host]::Py_Main($stringPointers.Count, $arrayPointer)
    exit $pythonExitCode
} finally {
    [Runtime.InteropServices.Marshal]::FreeHGlobal($arrayPointer)
    foreach ($pointer in $stringPointers) {
        [Runtime.InteropServices.Marshal]::FreeHGlobal($pointer)
    }
    $env:PATH = $previousPath
    $env:PYTHONHOME = $previousPythonHome
    $env:PYTHONPATH = $previousPythonPath
}
