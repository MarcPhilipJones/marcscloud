<#
.SYNOPSIS
    Create a git checkpoint (stage + commit) after a verified change.

.DESCRIPTION
    A lightweight, reversible save-point per feature so changes can be rolled
    back individually. It NEVER pushes — local commits only. Shows the staged
    diff stat first; pass -Yes to skip the confirmation prompt.

.EXAMPLE
    ./scripts/checkpoint.ps1 "tesla: trigger on state=driving (fixes reverse-off-driveway)"
.EXAMPLE
    ./scripts/checkpoint.ps1 -Yes "geofence: add Tesco Express Stone Cross"
#>
param(
    [Parameter(Mandatory, Position = 0)]
    [string]$Message,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path .git)) { throw "Not a git repository root." }

git add -A
$stat = git diff --cached --stat
if (-not $stat) {
    Write-Host "Nothing staged - working tree clean." -ForegroundColor Yellow
    return
}

Write-Host "Staged changes:" -ForegroundColor Cyan
Write-Host $stat

if (-not $Yes) {
    $ans = Read-Host "Commit with message '$Message'? (y/N)"
    if ($ans -notmatch '^[Yy]') { Write-Host "Aborted (changes remain staged)." -ForegroundColor Yellow; return }
}

git commit -m $Message
Write-Host "Checkpoint created. (Not pushed - local only.)" -ForegroundColor Green
