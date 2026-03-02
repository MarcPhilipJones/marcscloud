# Check Code App CSP settings using Power Platform API
# Uses MSAL.PS for interactive browser authentication with PAC CLI client ID

$ErrorActionPreference = "Stop"

$tenantId = "996f568a-cc69-450a-b684-ae784069e679"
$clientId = "9cee029c-6210-4654-90bb-17e6e9d36617"  # Power Platform CLI client ID
$envId = "08690526-047d-ed9d-ab35-4528a98c0f4f"     # MJCC2024
$resource = "https://api.powerplatform.com/"
$scope = "$($resource).default"

# --- Use MSAL via Python (inline) to get token ---
$pythonScript = @"
import msal, json, sys

app = msal.PublicClientApplication(
    '$clientId',
    authority='https://login.microsoftonline.com/$tenantId'
)

# Try silent first
accounts = app.get_accounts()
result = None
if accounts:
    result = app.acquire_token_silent(['$scope'], account=accounts[0])

if not result or 'access_token' not in result:
    # Interactive browser flow
    result = app.acquire_token_interactive(
        scopes=['$scope'],
        prompt='select_account'
    )

if 'access_token' in result:
    print(result['access_token'])
else:
    print('ERROR:' + str(result.get('error_description', result)), file=sys.stderr)
    sys.exit(1)
"@

Write-Host "Authenticating via browser (Power Platform CLI app)..." -ForegroundColor Cyan
$token = .\.venv\Scripts\python.exe -c $pythonScript

if ($LASTEXITCODE -ne 0 -or -not $token) {
    Write-Host "Authentication failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Authenticated!" -ForegroundColor Green

# --- Query the CSP settings ---
$settingsUri = "$($resource)environmentmanagement/environments/$envId/settings?api-version=2022-03-01-preview&`$select=PowerApps_CSPReportingEndpoint,PowerApps_CSPEnabledCodeApps,PowerApps_CSPConfigCodeApps"

$headers = @{
    Authorization = "Bearer $token"
    Accept        = "application/json"
}

Write-Host "`nQuerying Code App CSP settings..." -ForegroundColor Cyan

try {
    $resp = Invoke-RestMethod -Uri $settingsUri -Method Get -Headers $headers
    $data = $resp.objectResult[0]

    Write-Host "`n$('=' * 60)" -ForegroundColor Yellow
    Write-Host "CODE APP CSP SETTINGS - MJCC2024" -ForegroundColor Yellow
    Write-Host "$('=' * 60)" -ForegroundColor Yellow

    $enabled = $data.PowerApps_CSPEnabledCodeApps
    $config = $data.PowerApps_CSPConfigCodeApps
    $report = $data.PowerApps_CSPReportingEndpoint

    Write-Host "CSP Enforcement:     $(if ($null -eq $enabled) { 'Not set (default: true)' } else { $enabled })"
    Write-Host "Reporting Endpoint:  $(if ($report) { $report } else { '(not configured)' })"
    Write-Host "CSP Directives:      $(if ($config) { $config } else { '(not configured - using defaults)' })"

    if ($config) {
        $parsed = $config | ConvertFrom-Json -Depth 10
        Write-Host "`nParsed directives:" -ForegroundColor Cyan
        $parsed | ConvertTo-Json -Depth 10
    }

    Write-Host "`n--- Defaults (when not configured) ---" -ForegroundColor DarkGray
    Write-Host "frame-ancestors: 'self' https://*.powerapps.com" -ForegroundColor DarkGray
    Write-Host "--- To embed in D365, need to ADD ---" -ForegroundColor Green
    Write-Host "https://*.dynamics.com" -ForegroundColor Green
    Write-Host "$('=' * 60)" -ForegroundColor Yellow

    # Save results for later use
    $results = @{
        Enabled = $enabled
        Config  = $config
        Report  = $report
        Token   = $token
        EnvId   = $envId
    }
    $results | ConvertTo-Json | Set-Content scripts\csp_current_state.json
    Write-Host "`nSaved current state to scripts\csp_current_state.json" -ForegroundColor DarkGray
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
}
