# Check and configure Code App CSP settings via Power Platform API
# API: https://api.powerplatform.com/environmentmanagement/environments/{envId}/settings
# Docs: https://learn.microsoft.com/en-us/power-apps/developer/code-apps/how-to/content-security-policy

$ErrorActionPreference = "Stop"

# Ensure Azure CLI is on PATH
$env:PATH = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin;$env:PATH"

$envId = "08690526-047d-ed9d-ab35-4528a98c0f4f"  # MJCC2024

# ── Step 1: Get a token for the Power Platform API ────────────────
Write-Host "Getting access token for Power Platform API..." -ForegroundColor Cyan
$tokenJson = az account get-access-token --resource "https://api.powerplatform.com/" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to get token. Trying az login first..." -ForegroundColor Yellow
    az login
    $tokenJson = az account get-access-token --resource "https://api.powerplatform.com/"
}
$tokenObj = $tokenJson | ConvertFrom-Json
$token = $tokenObj.accessToken
Write-Host "Token acquired (expires: $($tokenObj.expiresOn))" -ForegroundColor Green

# ── Step 2: Query current Code App CSP settings ──────────────────
$baseUri = "https://api.powerplatform.com"
$settingsUri = "$baseUri/environmentmanagement/environments/$envId/settings?api-version=2022-03-01-preview&`$select=PowerApps_CSPReportingEndpoint,PowerApps_CSPEnabledCodeApps,PowerApps_CSPConfigCodeApps"

$headers = @{
    Authorization  = "Bearer $token"
    Accept         = "application/json"
    "Content-Type" = "application/json"
}

Write-Host "`nQuerying Code App CSP settings..." -ForegroundColor Cyan
Write-Host "URI: $settingsUri"

try {
    $resp = Invoke-RestMethod -Uri $settingsUri -Method Get -Headers $headers
    $data = $resp.objectResult[0]

    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host "Code App CSP Settings (MJCC2024)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "CSP Enabled (enforced): $($data.PowerApps_CSPEnabledCodeApps)"
    Write-Host "Reporting Endpoint:     $($data.PowerApps_CSPReportingEndpoint)"
    Write-Host "CSP Config (raw):       $($data.PowerApps_CSPConfigCodeApps)"

    if ($null -ne $data.PowerApps_CSPConfigCodeApps -and $data.PowerApps_CSPConfigCodeApps -ne "") {
        $parsed = $data.PowerApps_CSPConfigCodeApps | ConvertFrom-Json -Depth 10
        Write-Host "`nParsed directives:" -ForegroundColor Cyan
        $parsed | ConvertTo-Json -Depth 10 | Write-Host
    }
    else {
        Write-Host "`nNo custom directives configured (using defaults)" -ForegroundColor DarkGray
    }

    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host "Default frame-ancestors for Code Apps:" -ForegroundColor Yellow
    Write-Host "  'self' https://*.powerapps.com" -ForegroundColor DarkGray
    Write-Host "`nTo embed in D365, need to ADD:" -ForegroundColor Green
    Write-Host "  https://*.dynamics.com" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Yellow

}
catch {
    Write-Host "Error querying CSP settings:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host $_.ErrorDetails.Message
}
