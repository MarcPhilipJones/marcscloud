<#
.SYNOPSIS
    Launch the AI Café Presenter in VS Code's Simple Browser or in Chrome.

.DESCRIPTION
    Opens presenter.html using VS Code's Simple Browser (if running inside VS Code)
    or falls back to Chrome with the correct profile.

.PARAMETER Browser
    Force a specific browser: 'vscode', 'chrome', or 'edge'. Default: auto-detect.

.PARAMETER Port
    If using a local HTTP server, specify the port. Default: opens file:// directly.

.EXAMPLE
    .\Start-Presenter.ps1
    .\Start-Presenter.ps1 -Browser chrome
#>

param(
    [ValidateSet('auto', 'vscode', 'chrome', 'edge')]
    [string]$Browser = 'auto'
)

$ErrorActionPreference = 'Stop'

$htmlFile = Join-Path $PSScriptRoot '..\src\presenter.html'
$htmlFile = (Resolve-Path $htmlFile).Path
$fileUri = "file:///$($htmlFile.Replace('\', '/'))"

Write-Host ''
Write-Host '  ☕ AI Café Presenter — Launcher' -ForegroundColor DarkCyan
Write-Host "  File: $htmlFile" -ForegroundColor Gray
Write-Host ''

# Detect environment
$inVsCode = $null -ne $env:TERM_PROGRAM -and $env:TERM_PROGRAM -eq 'vscode'

if ($Browser -eq 'auto') {
    if ($inVsCode) {
        $Browser = 'vscode'
    }
    else {
        $Browser = 'chrome'
    }
}

switch ($Browser) {
    'vscode' {
        Write-Host '  Opening in VS Code Simple Browser...' -ForegroundColor Green
        # Use the VS Code CLI to open the Simple Browser
        # This sends a command to the running VS Code instance
        try {
            # The VS Code command to open Simple Browser
            code --open-url $fileUri 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw 'code command failed'
            }
        }
        catch {
            Write-Host '  VS Code CLI not available. Use Ctrl+Shift+P → "Simple Browser: Show" and paste:' -ForegroundColor Yellow
            Write-Host "  $fileUri" -ForegroundColor White
        }
        Write-Host ''
        Write-Host '  TIP: In VS Code, press Ctrl+Shift+P and type "Simple Browser: Show"' -ForegroundColor Gray
        Write-Host "  Then enter: $fileUri" -ForegroundColor Gray
    }
    'chrome' {
        Write-Host '  Opening in Chrome (Default profile)...' -ForegroundColor Green
        Start-Process 'chrome.exe' -ArgumentList "--profile-directory=`"Default`"", $fileUri
    }
    'edge' {
        Write-Host '  Opening in Microsoft Edge...' -ForegroundColor Green
        Start-Process 'msedge.exe' -ArgumentList $fileUri
    }
}

Write-Host ''
Write-Host '  Done. Presenter should be loading.' -ForegroundColor Green
Write-Host '  NOTE: Start ppt-controller.ps1 separately for PowerPoint control.' -ForegroundColor Gray
Write-Host ''
