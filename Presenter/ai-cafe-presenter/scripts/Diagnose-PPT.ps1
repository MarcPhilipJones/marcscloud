<#
.SYNOPSIS
    Diagnoses PowerPoint COM automation issues for ppt-controller.ps1
.DESCRIPTION
    Checks bitness, running PowerPoint instances, slideshow state,
    and COM object accessibility.
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PPT Controller Diagnostic Report" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# --- 1. PowerShell Bitness ---
Write-Host "[1] PowerShell Environment" -ForegroundColor Yellow
Write-Host "    PowerShell Version : $($PSVersionTable.PSVersion)"
Write-Host "    PowerShell Edition : $($PSVersionTable.PSEdition)"
Write-Host "    64-bit Process     : $([Environment]::Is64BitProcess)"
Write-Host "    64-bit OS          : $([Environment]::Is64BitOperatingSystem)"
Write-Host "    Executable         : $($PSHome)\powershell.exe"
Write-Host ""

# --- 2. PowerPoint Process ---
Write-Host "[2] PowerPoint Processes" -ForegroundColor Yellow
$pptProcesses = Get-Process -Name POWERPNT -ErrorAction SilentlyContinue
if ($pptProcesses) {
    foreach ($proc in $pptProcesses) {
        $is64 = $false
        try {
            $path = $proc.Path
            if ($path -match "Program Files\\" -and $path -notmatch "Program Files \(x86\)\\") { $is64 = $true }
            elseif ($path -match "Program Files \(x86\)\\") { $is64 = $false }
        }
        catch {
            $path = "(access denied)"
        }
        Write-Host "    PID: $($proc.Id) | Title: '$($proc.MainWindowTitle)' | Path: $path"
        Write-Host "    Likely 64-bit: $is64"
    }
    Write-Host "    Total PowerPoint processes: $($pptProcesses.Count)"
}
else {
    Write-Host "    *** NO PowerPoint process found! ***" -ForegroundColor Red
    Write-Host "    Start PowerPoint and enter slideshow mode first."
}
Write-Host ""

# --- 3. Bitness Match Check ---
Write-Host "[3] Bitness Compatibility Check" -ForegroundColor Yellow
if ($pptProcesses) {
    $pptPath = $pptProcesses[0].Path
    $ppt64 = $pptPath -match "Program Files\\" -and $pptPath -notmatch "Program Files \(x86\)\\"
    $ps64 = [Environment]::Is64BitProcess

    if ($ppt64 -eq $ps64) {
        Write-Host "    MATCH - Both are $(if($ps64){'64-bit'}else{'32-bit'})" -ForegroundColor Green
    }
    else {
        Write-Host "    MISMATCH!" -ForegroundColor Red
        Write-Host "       PowerPoint is $(if($ppt64){'64-bit'}else{'32-bit'})" -ForegroundColor Red
        Write-Host "       PowerShell is $(if($ps64){'64-bit'}else{'32-bit'})" -ForegroundColor Red
        Write-Host ""
        Write-Host "    FIX: Run ppt-controller.ps1 from the matching PowerShell:" -ForegroundColor Yellow
        if ($ppt64) {
            Write-Host "      C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -ForegroundColor White
        }
        else {
            Write-Host "      C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -ForegroundColor White
        }
    }
}
else {
    Write-Host "    (skipped - no PowerPoint process)" -ForegroundColor DarkGray
}
Write-Host ""

# --- 4. COM Object Access ---
Write-Host "[4] COM Object Access (GetActiveObject)" -ForegroundColor Yellow
$pptApp = $null
try {
    Add-Type -AssemblyName Microsoft.Office.Interop.PowerPoint -ErrorAction SilentlyContinue
}
catch {}

try {
    $pptApp = [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')
    Write-Host "    GetActiveObject succeeded" -ForegroundColor Green
    Write-Host "    Application Name   : $($pptApp.Name)"
    Write-Host "    Version            : $($pptApp.Version)"
    Write-Host "    Presentations Open : $($pptApp.Presentations.Count)"
}
catch {
    Write-Host "    GetActiveObject FAILED: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "    Trying New-Object fallback..." -ForegroundColor Yellow
    try {
        $pptApp = New-Object -ComObject PowerPoint.Application
        Write-Host "    New-Object works but gets a NEW instance (not the running one)" -ForegroundColor DarkYellow
        Write-Host "    This means GetActiveObject can't find the existing PowerPoint." -ForegroundColor DarkYellow
        Write-Host "    Likely a bitness mismatch or elevation mismatch." -ForegroundColor DarkYellow
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pptApp) | Out-Null
        $pptApp = $null
    }
    catch {
        Write-Host "    New-Object also failed: $_" -ForegroundColor Red
    }
}
Write-Host ""

# --- 5. SlideShow Windows ---
Write-Host "[5] SlideShow Window Check" -ForegroundColor Yellow
if ($pptApp) {
    try {
        $ssCount = $pptApp.SlideShowWindows.Count
        Write-Host "    SlideShowWindows.Count: $ssCount"

        if ($ssCount -gt 0) {
            Write-Host "    Slideshow IS running" -ForegroundColor Green
            try {
                $view = $pptApp.SlideShowWindows(1).View
                $currentSlide = $view.CurrentShowPosition
                Write-Host "    Current Slide Position: $currentSlide"
                Write-Host ""

                # Test navigation
                Write-Host "    Testing Next slide..." -ForegroundColor Yellow
                try {
                    $view.Next()
                    Start-Sleep -Milliseconds 500
                    $newSlide = $view.CurrentShowPosition
                    Write-Host "    Next() succeeded - now on slide $newSlide" -ForegroundColor Green

                    # Go back
                    $view.Previous()
                    Start-Sleep -Milliseconds 500
                    Write-Host "    Previous() succeeded - back on slide $($view.CurrentShowPosition)" -ForegroundColor Green
                }
                catch {
                    Write-Host "    Navigation failed: $_" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "    Cannot access SlideShowWindows(1).View: $_" -ForegroundColor Red
                Write-Host ""
                Write-Host "    This often happens with Presenter View." -ForegroundColor Yellow
                Write-Host "    Try: SlideShow > Set Up Slide Show > disable Presenter View" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "    SlideShowWindows.Count is 0" -ForegroundColor Red
            Write-Host ""
            Write-Host "    PowerPoint is open but NOT in slideshow mode." -ForegroundColor Yellow
            Write-Host "    Press F5 in PowerPoint to start the slideshow, then re-run." -ForegroundColor Yellow
            Write-Host ""

            if ($pptApp.Presentations.Count -gt 0) {
                $pres = $pptApp.Presentations(1)
                Write-Host "    Active Presentation: $($pres.Name)"
                Write-Host "    Slide Count: $($pres.Slides.Count)"

                try {
                    $sss = $pres.SlideShowSettings
                    Write-Host "    ShowType: $($sss.ShowType)"
                    Write-Host "    (1=Speaker/FullScreen, 2=Browsed by Individual, 3=Browsed at Kiosk)"
                }
                catch {
                    Write-Host "    Cannot read SlideShowSettings: $_" -ForegroundColor DarkYellow
                }
            }
        }
    }
    catch {
        Write-Host "    Error checking SlideShowWindows: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "    (skipped - no COM object)" -ForegroundColor DarkGray
}
Write-Host ""

# --- 6. Port 8080 Check ---
Write-Host "[6] Port 8080 Status" -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($portCheck) {
    foreach ($conn in $portCheck) {
        $procName = (Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue).ProcessName
        Write-Host "    Port 8080 in use by PID $($conn.OwningProcess) ($procName) - State: $($conn.State)"
    }
}
else {
    Write-Host "    Port 8080 is FREE (ready for ppt-controller.ps1)" -ForegroundColor Green
}
Write-Host ""

# --- 7. Existing ppt-controller.ps1 Check ---
Write-Host "[7] Controller Script Check" -ForegroundColor Yellow
$scriptPath = Join-Path $PSScriptRoot "..\scripts\Start-PptController.ps1"
$altPath = Join-Path $PSScriptRoot "Start-PptController.ps1"
if (Test-Path $altPath) {
    Write-Host "    Found: $altPath" -ForegroundColor Green
    Write-Host "    Size: $((Get-Item $altPath).Length) bytes"
    Write-Host "    Modified: $((Get-Item $altPath).LastWriteTime)"
}
elseif (Test-Path $scriptPath) {
    Write-Host "    Found: $scriptPath" -ForegroundColor Green
}
else {
    Write-Host "    Start-PptController.ps1 NOT FOUND nearby" -ForegroundColor DarkYellow
}
Write-Host ""

# --- Summary ---
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$issues = @()
if (-not $pptProcesses) { $issues += "PowerPoint is not running" }
if ($pptProcesses -and $pptApp -eq $null) { $issues += "COM GetActiveObject failed (likely bitness mismatch)" }
if ($pptApp -and $pptApp.SlideShowWindows.Count -eq 0) { $issues += "SlideShowWindows.Count is 0 (not in slideshow mode from COM perspective)" }

if ($issues.Count -eq 0) {
    Write-Host "  Everything looks good! COM can access slideshow." -ForegroundColor Green
}
else {
    Write-Host "  Issues found:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "    - $issue" -ForegroundColor Red
    }
}
Write-Host ""
