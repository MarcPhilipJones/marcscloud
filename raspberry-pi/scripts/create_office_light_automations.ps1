$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhYzNkMDU3MjAwOWY0NzA4YmZkMjdjNzIwODQwYTVhYyIsImlhdCI6MTc3MzMwNTg3NiwiZXhwIjoyMDg4NjY1ODc2fQ.-g57WZvkMKrppYttWN4Uwy5LU1vDbXkM0w2AFFFwxSw"
$baseUrl = "http://192.168.0.111:8123"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

# ============================================================
# Automation 1: Office Light Auto-On (Occupied + Low Light)
# Triggers when: occupancy detected OR illuminance drops below 200
# Conditions: occupied AND illuminance < 200
# ============================================================
Write-Host "=== Creating Automation 1: Office Light Auto-On ===" -ForegroundColor Cyan

$autoOn = @{
    alias       = "Office Light Auto-On (Occupied + Low Light)"
    description = "Turn on office Tapo bulb when FP300 detects occupancy and illuminance is below 200 lux"
    mode        = "single"
    trigger     = @(
        @{
            platform  = "state"
            entity_id = "binary_sensor.presence_multi_sensor_fp300_occupancy"
            to        = "on"
        },
        @{
            platform  = "numeric_state"
            entity_id = "sensor.presence_multi_sensor_fp300_illuminance"
            below     = 200
        }
    )
    condition   = @(
        @{
            condition = "state"
            entity_id = "binary_sensor.presence_multi_sensor_fp300_occupancy"
            state     = "on"
        },
        @{
            condition = "numeric_state"
            entity_id = "sensor.presence_multi_sensor_fp300_illuminance"
            below     = 200
        }
    )
    action      = @(
        @{
            service = "light.turn_on"
            target  = @{
                entity_id = "light.smart_multicolor_bulb"
            }
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $result1 = Invoke-RestMethod -Uri "$baseUrl/api/services/automation/reload" -Headers $headers -Method Post -Body "{}"
    Write-Host "Reloaded automations first" -ForegroundColor Green
}
catch {
    Write-Host "Reload note: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Use the config/automation/config endpoint to create
# First get existing automations to find next available ID
try {
    $result1 = Invoke-WebRequest -Uri "$baseUrl/api/services/automation/reload" -Headers $headers -Method Post -Body "{}" -UseBasicParsing
    Write-Host "Automation reload: $($result1.StatusCode)" -ForegroundColor Green
}
catch {
    Write-Host "Note: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create automation via WebSocket-like approach using the config API
# HA 2024+ supports POST /api/config/automation/config/<id>
$autoOnId = "office_light_auto_on_occupied_low_light"
try {
    $result = Invoke-WebRequest -Uri "$baseUrl/api/config/automation/config/$autoOnId" -Headers $headers -Method Post -Body $autoOn -UseBasicParsing
    Write-Host "Auto-On created: Status $($result.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($result.Content)" -ForegroundColor Gray
}
catch {
    Write-Host "Auto-On FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Red
    }
}

# ============================================================
# Automation 2: Office Light Auto-Off (No Occupancy)
# Triggers when: occupancy changes to off
# No conditions needed
# ============================================================
Write-Host ""
Write-Host "=== Creating Automation 2: Office Light Auto-Off ===" -ForegroundColor Cyan

$autoOff = @{
    alias       = "Office Light Auto-Off (No Occupancy)"
    description = "Turn off office Tapo bulb when FP300 detects no occupancy"
    mode        = "single"
    trigger     = @(
        @{
            platform  = "state"
            entity_id = "binary_sensor.presence_multi_sensor_fp300_occupancy"
            to        = "off"
        }
    )
    condition   = @()
    action      = @(
        @{
            service = "light.turn_off"
            target  = @{
                entity_id = "light.smart_multicolor_bulb"
            }
        }
    )
} | ConvertTo-Json -Depth 10

$autoOffId = "office_light_auto_off_no_occupancy"
try {
    $result = Invoke-WebRequest -Uri "$baseUrl/api/config/automation/config/$autoOffId" -Headers $headers -Method Post -Body $autoOff -UseBasicParsing
    Write-Host "Auto-Off created: Status $($result.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($result.Content)" -ForegroundColor Gray
}
catch {
    Write-Host "Auto-Off FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Red
    }
}

# ============================================================
# Reload automations so they take effect
# ============================================================
Write-Host ""
Write-Host "=== Reloading automations ===" -ForegroundColor Cyan
try {
    $result = Invoke-WebRequest -Uri "$baseUrl/api/services/automation/reload" -Headers $headers -Method Post -Body "{}" -UseBasicParsing
    Write-Host "Reload: Status $($result.StatusCode)" -ForegroundColor Green
}
catch {
    Write-Host "Reload failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================
# Verify - list all automations
# ============================================================
Write-Host ""
Write-Host "=== Verifying automations ===" -ForegroundColor Cyan
$states = Invoke-RestMethod -Uri "$baseUrl/api/states" -Headers $headers
$automations = $states | Where-Object { $_.entity_id -match "automation\." } | ForEach-Object {
    "$($_.entity_id) | state=$($_.state) | last_triggered=$($_.attributes.last_triggered)"
}
$automations | ForEach-Object { Write-Host $_ }
