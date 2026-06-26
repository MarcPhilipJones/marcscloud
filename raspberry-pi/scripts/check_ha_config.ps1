<#
.SYNOPSIS
    Validate Home Assistant configuration before restarting.
.DESCRIPTION
    Calls the HA config check API and reports any errors.
    Use this before restarting HA after editing YAML files.
.EXAMPLE
    .\scripts\check_ha_config.ps1
#>

$tokenFile = Join-Path $PSScriptRoot ".." ".vscode" "mcp.json"
$mcp = Get-Content $tokenFile | ConvertFrom-Json
$token = $mcp.servers.homeassistant.env.HASS_TOKEN
$baseUrl = "http://192.168.0.111:8123"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

Write-Host "Checking HA configuration..." -ForegroundColor Cyan

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/config/core/check_config" -Headers $headers -Method Post
    if ($result.result -eq "valid") {
        Write-Host "Configuration is VALID" -ForegroundColor Green
        Write-Host "  Errors: $($result.errors)" -ForegroundColor Gray
    } else {
        Write-Host "Configuration is INVALID" -ForegroundColor Red
        Write-Host "  Result: $($result.result)" -ForegroundColor Red
        Write-Host "  Errors: $($result.errors)" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "Failed to reach HA API: $_" -ForegroundColor Red
    exit 1
}

$restart = Read-Host "Restart Home Assistant? (y/N)"
if ($restart -eq "y") {
    Write-Host "Restarting..." -ForegroundColor Cyan
    ssh pi5 "docker restart homeassistant"
    Write-Host "Restart triggered. HA will be back in ~30 seconds." -ForegroundColor Green
}
