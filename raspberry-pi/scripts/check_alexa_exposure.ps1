# Check whether script.prepare_the_tesla is exposed to Alexa via HA Cloud
$ErrorActionPreference = 'Continue'

$envFile = "C:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi\.env"
$envText = Get-Content $envFile -Raw
$token = ([regex]::Match($envText, "(?m)^HA_TOKEN=(.+)$")).Groups[1].Value.Trim()
if (-not $token) { Write-Error "No HA_TOKEN in .env"; exit 1 }

$h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$base = "http://192.168.0.111:8123"

Write-Host "=== 1. Script state ==="
try {
    $s = Invoke-RestMethod -Uri "$base/api/states/script.prepare_the_tesla" -Headers $h
    Write-Host "state: $($s.state)"
    Write-Host "last_triggered: $($s.attributes.last_triggered)"
    Write-Host "friendly_name: $($s.attributes.friendly_name)"
} catch { Write-Host "ERR: $($_.Exception.Message)" }

Write-Host "`n=== 2. Cloud status ==="
try {
    $cloud = Invoke-RestMethod -Uri "$base/api/cloud/status" -Headers $h -ErrorAction Stop
    $cloud | ConvertTo-Json -Depth 6
} catch { Write-Host "cloud/status not available via REST: $($_.Exception.Message)" }

# Use websocket-style endpoints via the supervisor proxy if available
Write-Host "`n=== 3. Get Alexa exposed entities via websocket API ==="
# HA exposes the cloud config under /api/cloud/* — try common endpoints
$candidates = @(
    "/api/cloud/google_actions/entities",
    "/api/cloud/alexa/entities",
    "/api/cloud/alexa/sync"
)
foreach ($c in $candidates) {
    try {
        $r = Invoke-RestMethod -Uri "$base$c" -Headers $h -ErrorAction Stop
        Write-Host "OK $c"
        $r | ConvertTo-Json -Depth 5 | Out-String | Write-Host
    } catch {
        Write-Host "MISS $c -> $($_.Exception.Message)"
    }
}
