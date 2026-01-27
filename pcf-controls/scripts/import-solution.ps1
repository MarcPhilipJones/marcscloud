[CmdletBinding()]
param(
    [ValidateSet("Release", "Debug")]
    [string]$Configuration = "Release",

    [switch]$PublishAll,

    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$solutionDir = Join-Path $root "solutions\MarcJonesPCFControls"
$solutionZip = Join-Path $solutionDir "bin\$Configuration\MarcJonesPCFControls.zip"

# Build if not skipping
if (-not $SkipBuild) {
    Write-Host "Building solution ($Configuration)..." -ForegroundColor Cyan
    Push-Location $solutionDir
    try {
        dotnet build --configuration $Configuration
        if ($LASTEXITCODE -ne 0) {
            throw "dotnet build failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path $solutionZip)) {
    throw "Solution zip not found: $solutionZip"
}

# Import solution (without --publish-changes to avoid publishing ALL customizations)
Write-Host "Importing solution..." -ForegroundColor Cyan
pac solution import --path $solutionZip

if ($LASTEXITCODE -ne 0) {
    throw "pac solution import failed with exit code $LASTEXITCODE"
}

Write-Host "Solution imported successfully." -ForegroundColor Green

# Optionally publish all (slow) - otherwise PCF controls are available immediately
if ($PublishAll) {
    Write-Host "Publishing all customizations (this may take a while)..." -ForegroundColor Yellow
    pac solution publish
    Write-Host "Published." -ForegroundColor Green
} else {
    Write-Host "Skipped 'publish all'. PCF controls are typically available immediately after import." -ForegroundColor Gray
    Write-Host "If you need to publish, run: pac solution publish" -ForegroundColor Gray
}
