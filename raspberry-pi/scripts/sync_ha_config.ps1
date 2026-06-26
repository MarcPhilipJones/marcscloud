<#
.SYNOPSIS
    Sync key Home Assistant config files from the Pi into this repo for version control.
.DESCRIPTION
    Downloads configuration.yaml, automations, dashboards, and other key files
    from the Pi into ha-config-backup/ for git tracking.
.EXAMPLE
    .\scripts\sync_ha_config.ps1
#>

$backupDir = Join-Path $PSScriptRoot ".." "ha-config-backup"
$piHost = "pi5"
$haConfigPath = "/home/admin/homeassistant"

# Ensure backup directory exists
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backupDir "storage") | Out-Null

Write-Host "Syncing HA config from Pi..." -ForegroundColor Cyan

# Core config files
$coreFiles = @(
    "configuration.yaml",
    "automations.yaml",
    "scripts.yaml",
    "scenes.yaml",
    "customize.yaml"
)

foreach ($file in $coreFiles) {
    $remotePath = "$haConfigPath/$file"
    $localPath = Join-Path $backupDir $file
    Write-Host "  $file" -ForegroundColor Gray -NoNewline
    try {
        scp "${piHost}:${remotePath}" "$localPath" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK" -ForegroundColor Green
        } else {
            Write-Host " SKIP (not found)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " SKIP" -ForegroundColor Yellow
    }
}

# Dashboard registry + dashboard configs
Write-Host "  Dashboard registry" -ForegroundColor Gray -NoNewline
scp "${piHost}:${haConfigPath}/.storage/lovelace_dashboards" (Join-Path $backupDir "storage" "lovelace_dashboards") 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host " OK" -ForegroundColor Green } else { Write-Host " FAIL" -ForegroundColor Red }

# Dashboard data files
$dashboardFiles = ssh $piHost "ls $haConfigPath/.storage/lovelace.* 2>/dev/null" 2>$null
if ($dashboardFiles) {
    foreach ($remotePath in ($dashboardFiles -split "`n")) {
        $fileName = Split-Path $remotePath -Leaf
        if ($fileName -match "\.bak$|\.corrupt") { continue }
        Write-Host "  $fileName" -ForegroundColor Gray -NoNewline
        scp "${piHost}:${remotePath}" (Join-Path $backupDir "storage" $fileName) 2>$null
        if ($LASTEXITCODE -eq 0) { Write-Host " OK" -ForegroundColor Green } else { Write-Host " FAIL" -ForegroundColor Red }
    }
}

Write-Host "`nSync complete. Review changes with: git diff ha-config-backup/" -ForegroundColor Cyan
