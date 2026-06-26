# Set office light to max brightness + 5000K via HA REST API
$token = if ($args[0]) { $args[0] } else { $env:HA_TOKEN }
if (-not $token) { Write-Error "No token: pass as arg or set `$env:HA_TOKEN"; exit 1 }
$baseUrl = "http://192.168.0.111:8123"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

$body = @{
    entity_id = "light.smart_multicolor_bulb"
    brightness = 255
    color_temp_kelvin = 5000
} | ConvertTo-Json

Write-Host "Setting office bulb: brightness=255, color_temp=5000K..."
$response = Invoke-RestMethod -Uri "$baseUrl/api/services/light/turn_on" -Headers $headers -Method Post -Body $body
Write-Host "Response: $($response | ConvertTo-Json -Depth 3)"

# Verify the state
Start-Sleep -Seconds 2
Write-Host "`nVerifying current state..."
$state = Invoke-RestMethod -Uri "$baseUrl/api/states/light.smart_multicolor_bulb" -Headers $headers -Method Get
Write-Host "State: $($state.state)"
Write-Host "Brightness: $($state.attributes.brightness)"
Write-Host "Color Temp: $($state.attributes.color_temp_kelvin)K"

# Check illuminance
$lux = Invoke-RestMethod -Uri "$baseUrl/api/states/sensor.presence_multi_sensor_fp300_illuminance" -Headers $headers -Method Get
Write-Host "`nCurrent illuminance: $($lux.state) lx"
