[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ControlName,

    [ValidateNotNullOrEmpty()]
    [string]$Namespace = "MarcJonesPCF",

    [ValidateSet("field", "dataset")]
    [string]$Template = "field",

    [ValidateNotNullOrEmpty()]
    [string]$SolutionName = "MarcJonesPCFControls",

    [ValidateNotNullOrEmpty()]
    [string]$PublisherName = "MarcJonesPCFControls",

    [ValidatePattern("^[a-zA-Z]{2,8}$")]
    [string]$PublisherPrefix = "mjpcf"
)

$ErrorActionPreference = "Stop"

function Assert-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

Assert-CommandExists -Name "pac"
Assert-CommandExists -Name "node"
Assert-CommandExists -Name "npm"

$root = Split-Path -Parent $PSScriptRoot
$controlsDir = Join-Path $root "controls"
$solutionsDir = Join-Path $root "solutions"
$controlDir = Join-Path $controlsDir $ControlName
$solutionDir = Join-Path $solutionsDir $SolutionName

if (Test-Path $controlDir) {
    throw "Control folder already exists: $controlDir"
}

New-Item -ItemType Directory -Force -Path $controlsDir | Out-Null
New-Item -ItemType Directory -Force -Path $solutionsDir | Out-Null

Write-Host "Creating PCF control '$ControlName' (template: $Template)" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $controlDir | Out-Null

Push-Location $controlDir
try {
    pac pcf init --name $ControlName --namespace $Namespace --template $Template
    npm install
    npm run build
}
finally {
    Pop-Location
}

if (-not (Test-Path $solutionDir)) {
    Write-Host "Creating solution '$SolutionName'" -ForegroundColor Cyan
    Push-Location $solutionsDir
    try {
        pac solution init --publisher-name $PublisherName --publisher-prefix $PublisherPrefix --outputDirectory $SolutionName
    }
    finally {
        Pop-Location
    }
}

Write-Host "Adding control reference to solution '$SolutionName'" -ForegroundColor Cyan
Push-Location $solutionDir
try {
    pac solution add-reference --path $controlDir
}
finally {
    Pop-Location
}

Write-Host "Done." -ForegroundColor Green
Write-Host "- Control:  $controlDir"
Write-Host "- Solution: $solutionDir"
