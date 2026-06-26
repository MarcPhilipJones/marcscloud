# Create Pi Health & Automation Observability Dashboard
# Usage: .\scripts\create_pi_health_dashboard.ps1
# Requires: HA_TOKEN env var or .env file with HA_TOKEN

param(
    [string]$Token = $env:HA_TOKEN,
    [string]$BaseUrl = "http://192.168.0.111:8123"
)

if (-not $Token) {
    # Try loading from .env
    $envFile = Join-Path $PSScriptRoot ".." ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^HA_TOKEN=(.+)$') { $Token = $Matches[1] }
        }
    }
}

if (-not $Token) {
    Write-Error "No HA_TOKEN found. Set HA_TOKEN env var or add to .env file."
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type"  = "application/json"
}

# --- Get automation entity IDs for the logbook cards ---
Write-Host "Fetching automation list..."
$automations = Invoke-RestMethod -Uri "$BaseUrl/api/states" -Headers $headers -Method Get |
    Where-Object { $_.entity_id -like "automation.*" } |
    Select-Object -ExpandProperty entity_id

Write-Host "Found $($automations.Count) automations"

# --- Build automation history cards ---
$automationCards = @()
foreach ($auto in $automations) {
    $friendlyName = ($auto -replace '^automation\.', '' -replace '_', ' ')
    $automationCards += @{
        type = "logbook"
        entity = $auto
        hours_to_show = 168  # 7 days
        title = $friendlyName
    }
}

# --- Dashboard configuration ---
$dashboardConfig = @{
    views = @(
        @{
            title = "Pi Health"
            path = "pi-health"
            icon = "mdi:raspberry-pi"
            type = "sections"
            max_columns = 4
            sections = @(
                @{
                    type = "grid"
                    cards = @(
                        @{ type = "heading"; heading = "CPU & Memory"; heading_style = "title" }
                        @{
                            type = "gauge"
                            entity = "sensor.pi_cpu_temperature"
                            name = "CPU Temperature"
                            unit = "°C"
                            min = 0
                            max = 85
                            severity = @{
                                green = 0
                                yellow = 55
                                red = 70
                            }
                        }
                        @{
                            type = "gauge"
                            entity = "sensor.pi_cpu_load"
                            name = "CPU Load (1m avg)"
                            min = 0
                            max = 4
                            severity = @{
                                green = 0
                                yellow = 2
                                red = 3
                            }
                        }
                        @{
                            type = "gauge"
                            entity = "sensor.pi_memory_used_percent"
                            name = "Memory Usage"
                            min = 0
                            max = 100
                            severity = @{
                                green = 0
                                yellow = 60
                                red = 80
                            }
                        }
                        @{
                            type = "gauge"
                            entity = "sensor.pi_disk_used_percent"
                            name = "Disk Usage"
                            min = 0
                            max = 100
                            severity = @{
                                green = 0
                                yellow = 70
                                red = 90
                            }
                        }
                    )
                }
                @{
                    type = "grid"
                    cards = @(
                        @{ type = "heading"; heading = "Trends (24h)"; heading_style = "title" }
                        @{
                            type = "history-graph"
                            hours_to_show = 24
                            entities = @(
                                @{ entity = "sensor.pi_cpu_temperature"; name = "CPU Temp" }
                            )
                        }
                        @{
                            type = "history-graph"
                            hours_to_show = 24
                            entities = @(
                                @{ entity = "sensor.pi_cpu_load"; name = "CPU Load" }
                                @{ entity = "sensor.pi_memory_used_percent"; name = "Memory %" }
                            )
                        }
                        @{
                            type = "sensor"
                            entity = "sensor.pi_uptime"
                            name = "Uptime"
                            graph = "none"
                        }
                    )
                }
            )
        }
        @{
            title = "Automation Activity"
            path = "automation-activity"
            icon = "mdi:robot"
            type = "sections"
            max_columns = 4
            sections = @(
                @{
                    type = "grid"
                    cards = @(
                        @{ type = "heading"; heading = "Automation Log (7 days)"; heading_style = "title" }
                        @{
                            type = "logbook"
                            entities = $automations
                            hours_to_show = 168
                        }
                    )
                }
                @{
                    type = "grid"
                    cards = @(
                        @{ type = "heading"; heading = "Individual Automations"; heading_style = "title" }
                    ) + $automationCards
                }
            )
        }
    )
} | ConvertTo-Json -Depth 20

# --- Create the dashboard via REST API ---
$dashboardId = "pi_health"
$dashboardUrl = "pi-health"

# First try to create the dashboard entry
$dashboardPayload = @{
    id = $dashboardId
    url_path = $dashboardUrl
    title = "Pi Health"
    icon = "mdi:raspberry-pi"
    require_admin = $false
    show_in_sidebar = $true
    mode = "storage"
} | ConvertTo-Json

Write-Host "Creating/updating Pi Health dashboard..."

# Save the dashboard config via the REST API
# The config is saved using POST to the automation config endpoint pattern
try {
    $result = Invoke-RestMethod -Uri "$BaseUrl/api/config/dashboard/config/$dashboardId" `
        -Headers $headers -Method Post -Body $dashboardConfig
    Write-Host "Dashboard config saved successfully" -ForegroundColor Green
} catch {
    Write-Host "Note: Dashboard config endpoint returned: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "The dashboard may need to be created via the HA UI first, then updated." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Copy the JSON config below and paste into a new dashboard:" -ForegroundColor Cyan
    Write-Host $dashboardConfig
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Green
Write-Host "Pi health sensors added to configuration.yaml:" -ForegroundColor White
Write-Host "  - sensor.pi_cpu_temperature (°C, every 60s)"
Write-Host "  - sensor.pi_memory_used_percent (%, every 60s)"
Write-Host "  - sensor.pi_disk_used_percent (%, every 5min)"
Write-Host "  - sensor.pi_cpu_load (1m load avg, every 60s)"
Write-Host "  - sensor.pi_uptime (every 5min)"
Write-Host ""
Write-Host "To deploy:" -ForegroundColor White
Write-Host "  1. Push configuration.yaml to Pi: scp ha-config-backup/configuration.yaml pi5:~/homeassistant/configuration.yaml"
Write-Host "  2. Check config: Invoke-RestMethod '$BaseUrl/api/config/core/check_config' -Headers `$headers -Method Post"
Write-Host "  3. Restart HA:   Invoke-RestMethod '$BaseUrl/api/services/homeassistant/restart' -Headers `$headers -Method Post"
