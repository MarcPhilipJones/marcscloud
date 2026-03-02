<#
.SYNOPSIS
    Setup and manage a Power Apps Code App project.

.DESCRIPTION
    This script helps with common Power Apps Code Apps tasks:
    - Install npm dependencies
    - Authenticate PAC CLI
    - Initialise the code app
    - Add data sources (Dataverse tables, connectors)
    - Build and deploy to Power Apps

.NOTES
    Prerequisites:
    - Node.js LTS installed
    - Power Platform CLI (pac) installed
    - Code Apps enabled on your Power Platform environment

.EXAMPLE
    .\Setup-CodeApp.ps1 -Init -DisplayName "My First Code App"
    Installs dependencies and initialises the code app.

.EXAMPLE
    .\Setup-CodeApp.ps1 -AddDataverse -TableName "account"
    Adds the Dataverse account table as a data source.

.EXAMPLE
    .\Setup-CodeApp.ps1 -Deploy
    Builds and deploys the app to Power Apps.
#>

[CmdletBinding()]
param(
    [switch]$Init,
    [string]$DisplayName = "Code Apps Experiment",

    [switch]$AddDataverse,
    [string]$TableName,

    [switch]$AddConnector,
    [string]$ApiName,
    [string]$ConnectionId,
    [string]$TableId,
    [string]$DatasetName,

    [switch]$ListConnections,
    [switch]$Deploy,
    [string]$SolutionName,

    [switch]$Dev,
    [switch]$CheckPrereqs
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n>>> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# --- Check Prerequisites ---
if ($CheckPrereqs -or $Init) {
    Write-Step "Checking prerequisites..."

    # Node.js
    if (Test-Command "node") {
        $nodeVersion = & node --version
        Write-Success "Node.js: $nodeVersion"
    } else {
        Write-Error "Node.js is not installed. Download from https://nodejs.org/"
    }

    # npm
    if (Test-Command "npm") {
        $npmVersion = & npm --version
        Write-Success "npm: $npmVersion"
    } else {
        Write-Error "npm is not available."
    }

    # PAC CLI
    if (Test-Command "pac") {
        $pacVersion = & pac --version 2>&1
        Write-Success "PAC CLI: $pacVersion"
    } else {
        Write-Error "Power Platform CLI (pac) is not installed. See: https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction"
    }

    # Git
    if (Test-Command "git") {
        $gitVersion = & git --version
        Write-Success "Git: $gitVersion"
    } else {
        Write-Warn "Git is not installed (optional but recommended)."
    }

    if ($CheckPrereqs -and -not $Init) {
        Write-Host "`nAll prerequisite checks complete." -ForegroundColor Green
        return
    }
}

# --- Initialise ---
if ($Init) {
    Push-Location $ProjectRoot
    try {
        Write-Step "Installing npm dependencies..."
        & npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
        Write-Success "Dependencies installed"

        Write-Step "Initialising code app: '$DisplayName'..."
        & pac code init --displayname $DisplayName
        if ($LASTEXITCODE -ne 0) { throw "pac code init failed" }
        Write-Success "Code app initialised. power.config.json created."

        Write-Host "`n--- Setup Complete ---" -ForegroundColor Green
        Write-Host "Next steps:"
        Write-Host "  1. Run 'npm run dev' to start local development"
        Write-Host "  2. Open the Local Play URL in your Power Platform browser profile"
        Write-Host "  3. Add data sources with: pac code add-data-source"
        Write-Host "  4. Deploy with: npm run deploy"
    } finally {
        Pop-Location
    }
    return
}

# --- Add Dataverse Table ---
if ($AddDataverse) {
    if (-not $TableName) {
        Write-Error "Please specify -TableName <logical-name> (e.g., 'account', 'contact', 'msdyn_workorder')"
    }

    Push-Location $ProjectRoot
    try {
        Write-Step "Adding Dataverse table '$TableName' as data source..."
        & pac code add-data-source -a dataverse -t $TableName
        if ($LASTEXITCODE -ne 0) { throw "Failed to add Dataverse data source" }
        Write-Success "Dataverse table '$TableName' added. Check src/generated/ for typed models and services."
    } finally {
        Pop-Location
    }
    return
}

# --- Add Connector ---
if ($AddConnector) {
    if (-not $ApiName -or -not $ConnectionId) {
        Write-Error "Please specify -ApiName and -ConnectionId. Use -ListConnections to find these values."
    }

    Push-Location $ProjectRoot
    try {
        $args = @("code", "add-data-source", "-a", $ApiName, "-c", $ConnectionId)
        if ($TableId) { $args += "-t", $TableId }
        if ($DatasetName) { $args += "-d", $DatasetName }

        Write-Step "Adding connector '$ApiName' as data source..."
        & pac @args
        if ($LASTEXITCODE -ne 0) { throw "Failed to add data source" }
        Write-Success "Connector '$ApiName' added. Check src/generated/ for typed models and services."
    } finally {
        Pop-Location
    }
    return
}

# --- List Connections ---
if ($ListConnections) {
    Write-Step "Listing available connections..."
    & pac connection list
    return
}

# --- Deploy ---
if ($Deploy) {
    Push-Location $ProjectRoot
    try {
        Write-Step "Building and deploying to Power Apps..."

        & npm run build
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
        Write-Success "Build complete"

        $pushArgs = @("code", "push")
        if ($SolutionName) {
            $pushArgs += "--solutionName", $SolutionName
        }

        & pac @pushArgs
        if ($LASTEXITCODE -ne 0) { throw "pac code push failed" }
        Write-Success "App deployed to Power Apps!"
    } finally {
        Pop-Location
    }
    return
}

# --- Run Dev Server ---
if ($Dev) {
    Push-Location $ProjectRoot
    try {
        Write-Step "Starting local development server..."
        & npm run dev
    } finally {
        Pop-Location
    }
    return
}

# --- No flags provided ---
Write-Host @"

Power Apps Code Apps - Setup Script
====================================

Usage:
  .\Setup-CodeApp.ps1 -CheckPrereqs                        Check required tools are installed
  .\Setup-CodeApp.ps1 -Init [-DisplayName "name"]          Install deps & initialise code app
  .\Setup-CodeApp.ps1 -Dev                                 Start local development server
  .\Setup-CodeApp.ps1 -ListConnections                     List Power Platform connections
  .\Setup-CodeApp.ps1 -AddDataverse -TableName "account"   Add a Dataverse table
  .\Setup-CodeApp.ps1 -AddConnector -ApiName "shared_office365users" -ConnectionId "abc123"
  .\Setup-CodeApp.ps1 -Deploy [-SolutionName "MySolution"] Build and push to Power Apps

Examples:
  .\Setup-CodeApp.ps1 -Init -DisplayName "My First Code App"
  .\Setup-CodeApp.ps1 -AddDataverse -TableName "msdyn_workorder"
  .\Setup-CodeApp.ps1 -AddConnector -ApiName "shared_sql" -ConnectionId "abc" -TableId "[dbo].[Assets]" -DatasetName "server.db.net,mydb"
  .\Setup-CodeApp.ps1 -Deploy -SolutionName "ContosoSolution"

"@ -ForegroundColor White
