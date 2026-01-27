[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$controlsDir = Join-Path $root "controls"

if (-not (Test-Path $controlsDir)) {
    throw "Controls directory not found: $controlsDir"
}

$controlFolders = Get-ChildItem -Path $controlsDir -Directory -ErrorAction SilentlyContinue
if (-not $controlFolders -or $controlFolders.Count -eq 0) {
    Write-Host "No controls found under: $controlsDir" -ForegroundColor Yellow
    exit 0
}

foreach ($folder in $controlFolders) {
    $packageJson = Join-Path $folder.FullName "package.json"
    if (-not (Test-Path $packageJson)) {
        continue
    }

    Write-Host "Building: $($folder.Name)" -ForegroundColor Cyan
    Push-Location $folder.FullName
    try {
        if (-not $SkipInstall) {
            npm install
        }
        npm run build
    }
    finally {
        Pop-Location
    }
}

Write-Host "Build complete." -ForegroundColor Green
