<#
.SYNOPSIS
    Safely merges recommended VS Code user settings into the existing settings.json.
    Only adds NEW keys — never overwrites existing values.
.NOTES
    Created: 2026-02-19
    Purpose: Environment health improvement for Power Platform / D365 / Azure dev
#>

$settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Error "User settings.json not found at: $settingsPath"
    exit 1
}

# Read current settings as raw text, then parse
$rawJson = Get-Content $settingsPath -Raw

# PowerShell's ConvertFrom-Json doesn't handle comments in JSONC
# Remove single-line comments before parsing
$cleanJson = $rawJson -replace '//.*$', '' -replace '/\*[\s\S]*?\*/', ''
$current = $cleanJson | ConvertFrom-Json

# Define new settings to add (only if not already present)
$newSettings = @{
    # ─── British English & Spell Checking ───
    "cSpell.language"                        = "en,en-GB"
    "cSpell.enabledFileTypes"                = @{
        "markdown"   = $true
        "plaintext"  = $true
        "yaml"       = $true
        "json"       = $true
        "jsonc"      = $true
        "python"     = $true
        "powershell" = $true
        "javascript" = $true
        "typescript" = $true
        "html"       = $true
        "css"        = $true
        "bicep"      = $true
    }
    "cSpell.words"                           = @(
        "Dataverse", "Dynamics", "Bicep", "Azurite", "pylance",
        "pyproject", "httpx", "msal", "powerplatform", "odata",
        "Copilot", "GitLens", "Pushover", "lodash", "devkit"
    )

    # ─── Editor Defaults ───
    "editor.formatOnSave"                    = $true
    "editor.formatOnPaste"                   = $false
    "editor.defaultFormatter"                = "esbenp.prettier-vscode"
    "editor.bracketPairColorization.enabled" = $true
    "editor.guides.bracketPairs"             = "active"
    "editor.minimap.enabled"                 = $false
    "editor.wordWrap"                        = "off"
    "editor.linkedEditing"                   = $true
    "editor.stickyScroll.enabled"            = $true

    # ─── Language-Specific Formatters ───
    "[python]"                               = @{
        "editor.defaultFormatter"  = "charliermarsh.ruff"
        "editor.formatOnSave"      = $true
        "editor.codeActionsOnSave" = @{
            "source.fixAll"          = "explicit"
            "source.organizeImports" = "explicit"
        }
    }
    "[powershell]"                           = @{
        "editor.defaultFormatter" = "ms-vscode.powershell"
        "editor.formatOnSave"     = $true
    }
    "[json]"                                 = @{
        "editor.defaultFormatter" = "esbenp.prettier-vscode"
        "editor.formatOnSave"     = $true
    }
    "[jsonc]"                                = @{
        "editor.defaultFormatter" = "esbenp.prettier-vscode"
        "editor.formatOnSave"     = $true
    }
    "[yaml]"                                 = @{
        "editor.defaultFormatter" = "redhat.vscode-yaml"
        "editor.formatOnSave"     = $true
    }
    "[bicep]"                                = @{
        "editor.defaultFormatter" = "ms-azuretools.vscode-bicep"
        "editor.formatOnSave"     = $true
    }
    "[html]"                                 = @{
        "editor.defaultFormatter" = "esbenp.prettier-vscode"
        "editor.formatOnSave"     = $true
    }
    "[css]"                                  = @{
        "editor.defaultFormatter" = "esbenp.prettier-vscode"
        "editor.formatOnSave"     = $true
    }
    "[markdown]"                             = @{
        "editor.defaultFormatter" = "esbenp.prettier-vscode"
        "editor.formatOnSave"     = $false
        "editor.wordWrap"         = "on"
    }
    "[csharp]"                               = @{
        "editor.defaultFormatter" = "ms-dotnettools.csharp"
        "editor.formatOnSave"     = $true
    }

    # ─── File Associations ───
    "files.associations"                     = @{
        "*.tfvars"          = "terraform"
        "*.arm.json"        = "json"
        "*.parameters.json" = "json"
        "*.logicapp.json"   = "json"
    }

    # ─── Telemetry & Privacy ───
    "telemetry.telemetryLevel"               = "error"
    "redhat.telemetry.enabled"               = $false

    # ─── YAML Configuration ───
    "yaml.schemas"                           = @{
        "https://json.schemastore.org/github-workflow.json" = ".github/workflows/*.yml"
        "https://json.schemastore.org/github-action.json"   = "action.yml"
    }
    "yaml.format.enable"                     = $true
    "yaml.validate"                          = $true

    # ─── Git ───
    "git.autofetch"                          = $true
    "git.confirmSync"                        = $false
    "git.enableSmartCommit"                  = $true

    # ─── Explorer ───
    "explorer.confirmDelete"                 = $false
    "explorer.confirmDragAndDrop"            = $false
}

# Track what we add
$added = @()
$skipped = @()

foreach ($key in $newSettings.Keys) {
    $hasProp = [bool]($current.PSObject.Properties.Name -contains $key)
    if (-not $hasProp) {
        $current | Add-Member -NotePropertyName $key -NotePropertyValue $newSettings[$key]
        $added += $key
    }
    else {
        $skipped += $key
    }
}

# Write back
$outputJson = $current | ConvertTo-Json -Depth 10

# Create backup
$backupPath = "$settingsPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $settingsPath $backupPath
Write-Host "Backup saved to: $backupPath" -ForegroundColor Cyan

Set-Content -Path $settingsPath -Value $outputJson -Encoding UTF8
Write-Host ""
Write-Host "=== User settings.json updated ===" -ForegroundColor Green
Write-Host "Added $($added.Count) new settings:" -ForegroundColor Green
$added | ForEach-Object { Write-Host "  + $_" -ForegroundColor DarkGreen }
Write-Host ""
Write-Host "Skipped $($skipped.Count) existing settings (not overwritten):" -ForegroundColor Yellow
$skipped | ForEach-Object { Write-Host "  ~ $_" -ForegroundColor DarkYellow }
