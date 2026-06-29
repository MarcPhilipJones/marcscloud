<#
.SYNOPSIS
    Quote-safe remote command / file deploy helper for the Raspberry Pi.

.DESCRIPTION
    Avoids the PowerShell<->SSH quoting failures that bite when you embed
    \"...\" and pipes inside an `ssh host "..."` argument. Everything is sent to
    the Pi over STDIN, so PowerShell never tries to parse the remote script.

    Three modes:
      -Command "<bash>"          run a bash command/script on the Pi
      -Command "<py>"  -Python   run it as python3 on the Pi
      add -Root to any of the above to run under sudo
      -DeployFile <local> -Dest <remote>   copy a local file into a root-owned
                                           path (stages via /tmp then sudo cp,
                                           preserving root:root)

.EXAMPLE
    ./scripts/pi-exec.ps1 -Command 'sed -n "120,140p" /home/admin/homeassistant/scripts.yaml'
.EXAMPLE
    ./scripts/pi-exec.ps1 -Python -Root -Command @'
p="/home/admin/homeassistant/scripts.yaml"
print(open(p).read()[:200])
'@
.EXAMPLE
    ./scripts/pi-exec.ps1 -DeployFile ha-config-backup/packages/teslamate.yaml `
        -Dest /home/admin/homeassistant/packages/teslamate.yaml
#>
[CmdletBinding(DefaultParameterSetName = 'Run')]
param(
    [Parameter(ParameterSetName = 'Run', Mandatory)]
    [string]$Command,
    [Parameter(ParameterSetName = 'Run')]
    [switch]$Python,
    [Parameter(ParameterSetName = 'Run')]
    [switch]$Root,

    [Parameter(ParameterSetName = 'Deploy', Mandatory)]
    [string]$DeployFile,
    [Parameter(ParameterSetName = 'Deploy', Mandatory)]
    [string]$Dest,

    [string]$PiHost = 'pi5'
)

$ErrorActionPreference = 'Stop'

if ($PSCmdlet.ParameterSetName -eq 'Deploy') {
    if (-not (Test-Path $DeployFile)) { throw "Local file not found: $DeployFile" }
    $tmp = "/tmp/" + [IO.Path]::GetFileName($Dest)
    # 1) copy to a writable temp path on the Pi
    scp $DeployFile "${PiHost}:${tmp}"
    if ($LASTEXITCODE -ne 0) { throw "scp failed" }
    # 2) move into place as root, keep root:root, clean up
    $mv = "sudo cp '$tmp' '$Dest' && sudo chown root:root '$Dest' && rm -f '$tmp' && echo DEPLOYED && ls -l '$Dest'"
    ssh $PiHost $mv
    return
}

# Run mode: base64-encode the payload and decode it on the Pi. This sidesteps
# ALL PowerShell<->ssh newline (CRLF) and quoting problems - the wire only ever
# carries base64 (alphanumerics + / = ), and bash/python read clean LF text.
$runner = if ($Python) { 'python3 -' } else { 'bash -s' }
if ($Root) { $runner = "sudo $runner" }
$lf = ($Command -replace "`r`n", "`n") -replace "`r", "`n"
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($lf))
ssh $PiHost "echo $b64 | base64 -d | $runner"
