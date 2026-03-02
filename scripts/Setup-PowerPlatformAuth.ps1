<#
.SYNOPSIS
    Sets up Power Platform CLI (PAC) authentication using service principal credentials
    from the MCP Dataverse Server configuration.

.DESCRIPTION
    This script reads the existing service principal credentials from mcp-dataverse-server/.env
    and uses them to:
    1. Create a PAC CLI authentication profile
    2. Optionally set environment variables for other tools

.EXAMPLE
    .\Setup-PowerPlatformAuth.ps1
    
.EXAMPLE
    .\Setup-PowerPlatformAuth.ps1 -SetEnvVars -Persist
#>

[CmdletBinding()]
param(
    [switch]$SetEnvVars,     # Also set PAC_* environment variables
    [switch]$Persist,        # Persist env vars to user profile (requires SetEnvVars)
    [switch]$Force           # Overwrite existing PAC auth profile
)

$ErrorActionPreference = "Stop"

# Paths
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $WorkspaceRoot "mcp-dataverse-server\.env"

Write-Host "Power Platform Authentication Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check for .env file
if (-not (Test-Path $EnvFile)) {
    Write-Error "MCP Dataverse Server .env file not found at: $EnvFile"
    exit 1
}

Write-Host "Reading credentials from: $EnvFile" -ForegroundColor Yellow

# Parse .env file
$envContent = Get-Content $EnvFile -Raw
$credentials = @{}

foreach ($line in $envContent -split "`n") {
    $line = $line.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
        $key = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        # Remove quotes if present
        $value = $value -replace '^["'']|["'']$', ''
        $credentials[$key] = $value
    }
}

# Map the credential keys (handle both naming conventions)
$TenantId = $credentials["DATAVERSE_TENANT_ID"] ?? $credentials["AZURE_TENANT_ID"]
$ClientId = $credentials["DATAVERSE_CLIENT_ID"] ?? $credentials["AZURE_CLIENT_ID"]
$ClientSecret = $credentials["DATAVERSE_CLIENT_SECRET"] ?? $credentials["AZURE_CLIENT_SECRET"]
$DataverseUrl = $credentials["DATAVERSE_BASE_URL"] ?? $credentials["DATAVERSE_URL"]

# Validate required values
$missing = @()
if (-not $TenantId) { $missing += "DATAVERSE_TENANT_ID" }
if (-not $ClientId) { $missing += "DATAVERSE_CLIENT_ID" }
if (-not $ClientSecret) { $missing += "DATAVERSE_CLIENT_SECRET" }
if (-not $DataverseUrl) { $missing += "DATAVERSE_BASE_URL" }

if ($missing.Count -gt 0) {
    Write-Error "Missing required credentials in .env file: $($missing -join ', ')"
    exit 1
}

Write-Host "  Tenant ID:     $TenantId" -ForegroundColor Gray
Write-Host "  Client ID:     $($ClientId.Substring(0,8))..." -ForegroundColor Gray
Write-Host "  Environment:   $DataverseUrl" -ForegroundColor Gray
Write-Host ""

# Check if PAC CLI is installed
$pacPath = Get-Command pac -ErrorAction SilentlyContinue
if (-not $pacPath) {
    Write-Host "PAC CLI not found. Installing via dotnet tool..." -ForegroundColor Yellow
    & dotnet tool install --global Microsoft.PowerApps.CLI.Tool
    
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + 
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    
    $pacPath = Get-Command pac -ErrorAction SilentlyContinue
    if (-not $pacPath) {
        Write-Error "Failed to install PAC CLI. Please install manually: https://learn.microsoft.com/power-platform/developer/cli/introduction"
        exit 1
    }
    Write-Host "PAC CLI installed successfully" -ForegroundColor Green
}

Write-Host "PAC CLI found at: $($pacPath.Source)" -ForegroundColor Gray
Write-Host ""

# Check existing auth profiles
Write-Host "Checking existing PAC auth profiles..." -ForegroundColor Yellow
$authList = & pac auth list 2>&1 | Out-String

$profileName = "Dataverse-ServicePrincipal"

if ($authList -match $profileName -and -not $Force) {
    Write-Host "Auth profile '$profileName' already exists. Use -Force to overwrite." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Current auth profiles:" -ForegroundColor Gray
    & pac auth list
} else {
    # Create the auth profile (service principal is inferred from applicationId + clientSecret)
    Write-Host "Creating PAC auth profile: $profileName" -ForegroundColor Yellow
    
    & pac auth create `
        --name $profileName `
        --tenant $TenantId `
        --applicationId $ClientId `
        --clientSecret $ClientSecret `
        --environment $DataverseUrl
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PAC auth profile created successfully!" -ForegroundColor Green
    } else {
        Write-Error "Failed to create PAC auth profile"
        exit 1
    }
}

Write-Host ""

# Set environment variables if requested
if ($SetEnvVars) {
    Write-Host "Setting environment variables..." -ForegroundColor Yellow
    
    $env:PAC_TENANT_ID = $TenantId
    $env:PAC_CLIENT_ID = $ClientId
    $env:PAC_CLIENT_SECRET = $ClientSecret
    $env:DATAVERSE_URL = $DataverseUrl
    
    Write-Host "  PAC_TENANT_ID set" -ForegroundColor Gray
    Write-Host "  PAC_CLIENT_ID set" -ForegroundColor Gray
    Write-Host "  PAC_CLIENT_SECRET set" -ForegroundColor Gray
    Write-Host "  DATAVERSE_URL set" -ForegroundColor Gray
    
    if ($Persist) {
        Write-Host ""
        Write-Host "Persisting to user environment..." -ForegroundColor Yellow
        
        [Environment]::SetEnvironmentVariable("PAC_TENANT_ID", $TenantId, "User")
        [Environment]::SetEnvironmentVariable("PAC_CLIENT_ID", $ClientId, "User")
        [Environment]::SetEnvironmentVariable("PAC_CLIENT_SECRET", $ClientSecret, "User")
        [Environment]::SetEnvironmentVariable("DATAVERSE_URL", $DataverseUrl, "User")
        
        Write-Host "Environment variables persisted to user profile" -ForegroundColor Green
        Write-Host ""
        Write-Host "WARNING: Credentials are now stored in your user environment variables." -ForegroundColor DarkYellow
        Write-Host "         Run 'rundll32 sysdm.cpl,EditEnvironmentVariables' to manage them." -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now use PAC CLI commands without interactive login:" -ForegroundColor Cyan
Write-Host "  pac solution list" -ForegroundColor White
Write-Host "  pac env list" -ForegroundColor White
Write-Host "  pac auth select --name $profileName" -ForegroundColor White
Write-Host ""

# Show current auth status
Write-Host "Current PAC auth profiles:" -ForegroundColor Yellow
& pac auth list
