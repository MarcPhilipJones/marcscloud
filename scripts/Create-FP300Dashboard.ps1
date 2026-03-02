$token = Get-Content "c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\Personal\home_assistant\HomeAssistant\.env" |
Where-Object { $_ -match '^HA_TOKEN=' } |
ForEach-Object { $_ -replace '^HA_TOKEN=', '' }

$headers = @{
    Authorization  = "Bearer $token"
    "Content-Type" = "application/json"
}
$haUrl = "http://192.168.0.111:8123"

# Step 1: Create the dashboard
Write-Output "Creating FP300 dashboard..."
$dashBody = @{
    mode            = "storage"
    title           = "FP300"
    url_path        = "fp300"
    icon            = "mdi:motion-sensor"
    require_admin   = $false
    show_in_sidebar = $true
} | ConvertTo-Json -Depth 5

try {
    $result = Invoke-RestMethod -Uri "$haUrl/api/config/lovelace/dashboards" -Method Post -Headers $headers -Body $dashBody
    Write-Output "Dashboard created successfully: $($result | ConvertTo-Json -Depth 3 -Compress)"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 400) {
        Write-Output "Dashboard may already exist (400). Continuing with config..."
    }
    else {
        Write-Output "Error creating dashboard: $($_.Exception.Message)"
    }
}

# Step 2: Set the dashboard configuration with all FP300 cards
Write-Output "`nConfiguring dashboard cards..."

$config = @{
    title = "FP300 Presence Sensor"
    views = @(
        @{
            title = "FP300 Monitor"
            path  = "fp300-monitor"
            icon  = "mdi:motion-sensor"
            cards = @(
                # Row 1: Occupancy status (big)
                @{
                    type   = "entity"
                    entity = "binary_sensor.presence_multi_sensor_fp300_occupancy"
                    name   = "Occupancy"
                    icon   = "mdi:motion-sensor"
                },
                # Row 2: Key readings as horizontal stack
                @{
                    type  = "horizontal-stack"
                    cards = @(
                        @{
                            type          = "sensor"
                            entity        = "sensor.presence_multi_sensor_fp300_temperature"
                            name          = "Temperature"
                            graph         = "line"
                            hours_to_show = 24
                            detail        = 2
                        },
                        @{
                            type          = "sensor"
                            entity        = "sensor.presence_multi_sensor_fp300_humidity"
                            name          = "Humidity"
                            graph         = "line"
                            hours_to_show = 24
                            detail        = 2
                        },
                        @{
                            type          = "sensor"
                            entity        = "sensor.presence_multi_sensor_fp300_illuminance"
                            name          = "Light Level"
                            graph         = "line"
                            hours_to_show = 24
                            detail        = 2
                        }
                    )
                },
                # Row 3: Occupancy history (key for detecting false positives)
                @{
                    type          = "history-graph"
                    title         = "Occupancy History (48h)"
                    hours_to_show = 48
                    entities      = @(
                        @{
                            entity = "binary_sensor.presence_multi_sensor_fp300_occupancy"
                            name   = "Occupancy"
                        }
                    )
                },
                # Row 4: Light level history (correlates with actual presence)
                @{
                    type          = "history-graph"
                    title         = "Light Level History (48h)"
                    hours_to_show = 48
                    entities      = @(
                        @{
                            entity = "sensor.presence_multi_sensor_fp300_illuminance"
                            name   = "Illuminance (lux)"
                        }
                    )
                },
                # Row 5: Temperature history (shows human heat signature)
                @{
                    type          = "history-graph"
                    title         = "Temperature History (48h)"
                    hours_to_show = 48
                    entities      = @(
                        @{
                            entity = "sensor.presence_multi_sensor_fp300_temperature"
                            name   = "Temperature"
                        }
                    )
                },
                # Row 6: Combined occupancy + light overlay for false positive analysis
                @{
                    type          = "history-graph"
                    title         = "Occupancy vs Light (False Positive Check)"
                    hours_to_show = 48
                    entities      = @(
                        @{
                            entity = "binary_sensor.presence_multi_sensor_fp300_occupancy"
                            name   = "Occupancy"
                        },
                        @{
                            entity = "sensor.presence_multi_sensor_fp300_illuminance"
                            name   = "Light (lux)"
                        }
                    )
                },
                # Row 7: Sensor settings and battery
                @{
                    type     = "entities"
                    title    = "Sensor Settings & Status"
                    entities = @(
                        @{ entity = "select.presence_multi_sensor_fp300_sensitivity"; name = "Sensitivity" },
                        @{ entity = "number.presence_multi_sensor_fp300_hold_time"; name = "Hold Time (seconds)" },
                        @{ entity = "sensor.presence_multi_sensor_fp300_battery"; name = "Battery %" },
                        @{ entity = "sensor.presence_multi_sensor_fp300_battery_voltage"; name = "Battery Voltage" },
                        @{ entity = "update.presence_multi_sensor_fp300_firmware"; name = "Firmware Update" }
                    )
                },
                # Row 8: Office plug status (for correlation)
                @{
                    type          = "history-graph"
                    title         = "Office Plug (Correlation)"
                    hours_to_show = 48
                    entities      = @(
                        @{
                            entity = "switch.smart_wi_fi_plug"
                            name   = "Tapo Plug"
                        }
                    )
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $result = Invoke-RestMethod -Uri "$haUrl/api/config/lovelace/config/fp300" -Method Post -Headers $headers -Body $config
    Write-Output "Dashboard configured successfully!"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Output "Error configuring dashboard: Status $statusCode - $($_.Exception.Message)"
    try {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Output "Response: $($reader.ReadToEnd())"
        $reader.Dispose()
    }
    catch {}
}

Write-Output "`nDashboard URL: $haUrl/fp300/fp300-monitor"
Write-Output "Done!"
