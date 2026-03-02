<#
.SYNOPSIS
    Start the PowerPoint WebSocket controller for AI Café Presenter.

.DESCRIPTION
    Launches ppt-controller.ps1 which listens on port 8080 for WebSocket
    connections from the presenter HTML app.

.PARAMETER Port
    Port to listen on. Default: 8080.

.EXAMPLE
    .\Start-PptController.ps1
    .\Start-PptController.ps1 -Port 9090
#>

param(
    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

$script = Join-Path $PSScriptRoot '..\src\ppt-controller.ps1'
$script = (Resolve-Path $script).Path

Write-Host ''
Write-Host '  ☕ Starting PPT Controller...' -ForegroundColor DarkCyan
Write-Host "  Script: $script" -ForegroundColor Gray
Write-Host "  Port: $Port" -ForegroundColor Gray
Write-Host ''

# Check if port is already in use
$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq 'Listen' }

if ($existing) {
    Write-Host "  WARNING: Port $Port is already in use!" -ForegroundColor Yellow
    $existing | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  PID $($_.OwningProcess) ($($proc.ProcessName))" -ForegroundColor Yellow
    }
    Write-Host ''
    $confirm = Read-Host '  Kill existing process and continue? (y/N)'
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        $existing | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 500
    } else {
        Write-Host '  Aborted.' -ForegroundColor Red
        return
    }
}

# Run the controller
& $script -Port $Port
