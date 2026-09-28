param(
    [Parameter(Mandatory = $true)]
    [string] $Capture,
    [Parameter(Mandatory = $true)]
    [int[]] $EventIds,
    [Parameter(Mandatory = $true)]
    [string] $OutputDirectory,
    [string] $Decompiler = 'E:\KianaTools\d3dasm\target\release\d3dasm.exe'
)

$ErrorActionPreference = 'Stop'
$capturePath = (Resolve-Path -LiteralPath $Capture).Path
$scriptRoot = $PSScriptRoot
$exporter = Join-Path $scriptRoot 'export_shader_raw_batch.py'
$hostScript = Join-Path $scriptRoot 'run_bundled_renderdoc_python.ps1'
if (-not (Test-Path -LiteralPath $Decompiler)) {
    throw "Pinned d3dasm executable not found: $Decompiler. See references/dxbc-to-hlsl.md."
}

$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
$configPath = Join-Path $outputPath 'shader-export-config.json'
@{
    capture = $capturePath
    event_ids = $EventIds
    output_dir = $outputPath
} | ConvertTo-Json | Set-Content -LiteralPath $configPath -Encoding UTF8

& $hostScript -ScriptPath $exporter -ScriptArgs @($configPath)
if ($LASTEXITCODE -ne 0) { throw "RenderDoc shader export failed with exit code $LASTEXITCODE" }

$outputs = @()
foreach ($eventId in $EventIds) {
    foreach ($stage in @('VS', 'PS')) {
        $dxbc = Join-Path $outputPath "EID$eventId-$stage.dxbc"
        if (-not (Test-Path -LiteralPath $dxbc)) { continue }
        $hlsl = Join-Path $outputPath "EID$eventId-$stage.hlsl"
        & $Decompiler --emit hlsl -o $hlsl $dxbc
        if ($LASTEXITCODE -ne 0) { throw "d3dasm failed for EID $eventId $stage" }
        $outputs += @{
            eventId = $eventId
            stage = $stage
            dxbc = $dxbc
            dxbcSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dxbc).Hash
            hlsl = $hlsl
            hlslSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $hlsl).Hash
        }
    }
}

$d3dasmRoot = Split-Path (Split-Path (Split-Path $Decompiler -Parent) -Parent) -Parent
$d3dasmCommit = (& git -C $d3dasmRoot rev-parse HEAD 2>$null)
$cfglibRoot = 'E:\napbat\cfglib'
$cfglibCommit = if (Test-Path -LiteralPath $cfglibRoot) {
    (& git -C $cfglibRoot rev-parse HEAD 2>$null)
} else { $null }

@{
    capture = $capturePath
    captureSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $capturePath).Hash
    decompiler = (Resolve-Path -LiteralPath $Decompiler).Path
    d3dasmCommit = $d3dasmCommit
    cfglibCommit = $cfglibCommit
    shaders = $outputs
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (
    Join-Path $outputPath 'shader-decompile-manifest.json') -Encoding UTF8

Write-Output (Join-Path $outputPath 'shader-decompile-manifest.json')
