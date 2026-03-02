<#
.SYNOPSIS
    WebSocket server for controlling PowerPoint slide navigation from the AI Café Presenter.

.DESCRIPTION
    Runs a lightweight HTTP/WebSocket server on port 8080.
    The AI Café Presenter HTML app connects via WebSocket and sends JSON commands:
        { "action": "next" }     — advance to next slide
        { "action": "previous" } — go back one slide
        { "action": "first" }    — jump to first slide
        { "action": "last" }     — jump to last slide
        { "action": "goto", "slide": 5 }  — jump to slide 5
        { "action": "status" }   — returns current slide info

    PowerPoint must be running in SlideShow mode for navigation to work.

.PARAMETER Port
    The port number to listen on. Default: 8080.

.EXAMPLE
    .\ppt-controller.ps1
    .\ppt-controller.ps1 -Port 9090
#>

param(
    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

# Marshal.GetActiveObject was removed in .NET Core / .NET 5+.
# For PowerShell 7 we P/Invoke oleaut32!GetActiveObject directly.
if (-not ([System.Runtime.InteropServices.Marshal] | Get-Member -Static -Name 'GetActiveObject' -ErrorAction SilentlyContinue)) {
    Add-Type -Language CSharp -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class ComHelper
{
    [DllImport("oleaut32.dll", PreserveSig = false)]
    private static extern void GetActiveObject(
        [MarshalAs(UnmanagedType.LPStruct)] Guid rclsid,
        IntPtr pvReserved,
        [MarshalAs(UnmanagedType.IUnknown)] out object ppunk);

    public static object GetActiveObject(string progId)
    {
        Guid clsid;
        Type t = Type.GetTypeFromProgID(progId, true);
        clsid = t.GUID;
        object obj;
        GetActiveObject(clsid, IntPtr.Zero, out obj);
        return obj;
    }
}
'@
    Write-Host "[init] Added COM helper for PowerShell 7+ (GetActiveObject shim)" -ForegroundColor DarkGray
}

function Get-ActiveComObject {
    <# Cross-version wrapper: works on PS 5.1 (.NET Framework) and PS 7+ (.NET Core). #>
    param([string]$ProgId)
    if ([System.Runtime.InteropServices.Marshal] | Get-Member -Static -Name 'GetActiveObject' -ErrorAction SilentlyContinue) {
        return [System.Runtime.InteropServices.Marshal]::GetActiveObject($ProgId)
    } else {
        return [ComHelper]::GetActiveObject($ProgId)
    }
}

# Cached COM references — avoids repeated GetActiveObject calls which
# can fail intermittently due to COM apartment threading issues.
$script:pptApp  = $null
$script:pptView = $null

function Get-PowerPointApp {
    <# Returns the cached PowerPoint.Application COM object, re-acquiring if needed. #>
    if ($script:pptApp) {
        try {
            # Quick liveness check — access a harmless property
            $null = $script:pptApp.Name
            return $script:pptApp
        } catch {
            # COM reference went stale — re-acquire
            $script:pptApp = $null
            $script:pptView = $null
        }
    }
    try {
        $script:pptApp = Get-ActiveComObject -ProgId 'PowerPoint.Application'
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] COM: Acquired PowerPoint.Application (v$($script:pptApp.Version))" -ForegroundColor DarkGray
        return $script:pptApp
    } catch {
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] COM: GetActiveObject failed — $($_.Exception.Message)" -ForegroundColor DarkYellow
        return $null
    }
}

function Get-PowerPointSlideShow {
    <# Returns the SlideShowView COM object, or $null if PPT isn't presenting. #>
    $ppt = Get-PowerPointApp
    if (-not $ppt) { return $null }

    try {
        if ($ppt.SlideShowWindows.Count -gt 0) {
            $script:pptView = $ppt.SlideShowWindows.Item(1).View
            return $script:pptView
        }
    } catch {
        # SlideShow ended or COM error — clear cache
        $script:pptView = $null
        $script:pptApp  = $null
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] COM: SlideShowWindows access failed — $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
    return $null
}

function Invoke-SlideAction {
    param([string]$Action, [int]$SlideNumber = 0)

    $view = Get-PowerPointSlideShow
    if (-not $view) {
        return @{ error = 'PowerPoint is not in SlideShow mode' }
    }

    try {
        switch ($Action) {
            'next'     {
                $view.Next()
                Start-Sleep -Milliseconds 100
                return @{ slide = $view.CurrentShowPosition }
            }
            'previous' {
                $view.Previous()
                Start-Sleep -Milliseconds 100
                return @{ slide = $view.CurrentShowPosition }
            }
            'first'    {
                $view.First()
                Start-Sleep -Milliseconds 100
                return @{ slide = $view.CurrentShowPosition }
            }
            'last'     {
                $view.Last()
                Start-Sleep -Milliseconds 100
                return @{ slide = $view.CurrentShowPosition }
            }
            'goto'     {
                if ($SlideNumber -gt 0) {
                    $view.GotoSlide($SlideNumber)
                    Start-Sleep -Milliseconds 100
                    return @{ slide = $view.CurrentShowPosition }
                }
                return @{ error = 'Missing slide number for goto command' }
            }
            'status'   {
                return @{
                    slide = $view.CurrentShowPosition
                    state = $view.State.ToString()
                }
            }
            default    { return @{ error = "Unknown action: $Action" } }
        }
    } catch {
        # COM call failed — invalidate cache so next call re-acquires
        $script:pptView = $null
        $script:pptApp  = $null
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] COM: Slide action '$Action' failed — $($_.Exception.Message)" -ForegroundColor Red
        return @{ error = "Slide action failed: $($_.Exception.Message)" }
    }
}

# ──────────────────────────────────────────────
# WebSocket handshake helpers
# ──────────────────────────────────────────────

function Send-WebSocketHandshake {
    param([System.IO.Stream]$Stream, [string]$RequestHeaders)

    # Extract the Sec-WebSocket-Key
    if ($RequestHeaders -match 'Sec-WebSocket-Key:\s*(.+)\r?\n') {
        $key = $Matches[1].Trim()
    } else {
        throw 'Invalid WebSocket handshake: missing key'
    }

    $magic   = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    $sha1    = [System.Security.Cryptography.SHA1]::Create()
    $accept  = [Convert]::ToBase64String($sha1.ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($key + $magic)
    ))

    $response = "HTTP/1.1 101 Switching Protocols`r`n" +
                "Upgrade: websocket`r`n" +
                "Connection: Upgrade`r`n" +
                "Sec-WebSocket-Accept: $accept`r`n" +
                "Access-Control-Allow-Origin: *`r`n`r`n"

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($response)
    $Stream.Write($bytes, 0, $bytes.Length)
    $Stream.Flush()
}

function Read-WebSocketFrame {
    <# Read one WebSocket text frame. Returns the decoded payload string, or $null on close. #>
    param([System.IO.Stream]$Stream)

    $header = New-Object byte[] 2
    $read   = $Stream.Read($header, 0, 2)
    if ($read -lt 2) { return $null }

    $opcode = $header[0] -band 0x0F
    if ($opcode -eq 8) { return $null }  # close frame

    $masked = ($header[1] -band 0x80) -ne 0
    $len    = $header[1] -band 0x7F

    if ($len -eq 126) {
        $ext = New-Object byte[] 2
        $Stream.Read($ext, 0, 2) | Out-Null
        $len = ([int]$ext[0] -shl 8) -bor [int]$ext[1]
    } elseif ($len -eq 127) {
        $ext = New-Object byte[] 8
        $Stream.Read($ext, 0, 8) | Out-Null
        $len = 0
        for ($i = 0; $i -lt 8; $i++) {
            $len = ($len -shl 8) -bor [int]$ext[$i]
        }
    }

    $mask = $null
    if ($masked) {
        $mask = New-Object byte[] 4
        $Stream.Read($mask, 0, 4) | Out-Null
    }

    $payload = New-Object byte[] $len
    $totalRead = 0
    while ($totalRead -lt $len) {
        $chunk = $Stream.Read($payload, $totalRead, $len - $totalRead)
        if ($chunk -le 0) { return $null }
        $totalRead += $chunk
    }

    if ($masked) {
        for ($i = 0; $i -lt $len; $i++) {
            $payload[$i] = $payload[$i] -bxor $mask[$i % 4]
        }
    }

    return [System.Text.Encoding]::UTF8.GetString($payload)
}

function Send-WebSocketFrame {
    <# Send a text frame back to the client. #>
    param([System.IO.Stream]$Stream, [string]$Text)

    $data = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $frame = @()

    # First byte: FIN + TEXT opcode
    $frame += [byte]0x81

    if ($data.Length -lt 126) {
        $frame += [byte]$data.Length
    } elseif ($data.Length -le 65535) {
        $frame += [byte]126
        $frame += [byte](($data.Length -shr 8) -band 0xFF)
        $frame += [byte]($data.Length -band 0xFF)
    } else {
        $frame += [byte]127
        for ($i = 7; $i -ge 0; $i--) {
            $frame += [byte](($data.Length -shr ($i * 8)) -band 0xFF)
        }
    }

    $all = [byte[]]$frame + $data
    $Stream.Write($all, 0, $all.Length)
    $Stream.Flush()
}

# ──────────────────────────────────────────────
# Handle a single client connection
# ──────────────────────────────────────────────

function Handle-Client {
    param([System.Net.Sockets.TcpClient]$Client)

    try {
        $stream = $Client.GetStream()
        $stream.ReadTimeout = 30000  # 30s timeout

        # Read HTTP upgrade request
        $buffer = New-Object byte[] 4096
        $count  = $stream.Read($buffer, 0, $buffer.Length)
        $request = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $count)

        if ($request -match 'Upgrade:\s*websocket') {
            # WebSocket upgrade
            Send-WebSocketHandshake -Stream $stream -RequestHeaders $request
            Write-Host "[$(Get-Date -f 'HH:mm:ss')] WebSocket client connected from $($Client.Client.RemoteEndPoint)" -ForegroundColor Green

            # Send initial status
            $status = Invoke-SlideAction -Action 'status'
            Send-WebSocketFrame -Stream $stream -Text ($status | ConvertTo-Json -Compress)

            # Message loop
            while ($Client.Connected) {
                try {
                    $msg = Read-WebSocketFrame -Stream $stream
                    if ($null -eq $msg) {
                        Write-Host "[$(Get-Date -f 'HH:mm:ss')] Client disconnected" -ForegroundColor Yellow
                        break
                    }

                    Write-Host "[$(Get-Date -f 'HH:mm:ss')] Received: $msg" -ForegroundColor Cyan

                    $parsed = $msg | ConvertFrom-Json
                    $action = $parsed.action
                    $slideNum = if ($parsed.slide) { [int]$parsed.slide } else { 0 }

                    $result = Invoke-SlideAction -Action $action -SlideNumber $slideNum
                    $json   = $result | ConvertTo-Json -Compress

                    Write-Host "[$(Get-Date -f 'HH:mm:ss')] Response: $json" -ForegroundColor Gray
                    Send-WebSocketFrame -Stream $stream -Text $json

                } catch [System.IO.IOException] {
                    Write-Host "[$(Get-Date -f 'HH:mm:ss')] Client connection lost" -ForegroundColor Yellow
                    break
                } catch {
                    $err = @{ error = $_.Exception.Message } | ConvertTo-Json -Compress
                    try { Send-WebSocketFrame -Stream $stream -Text $err } catch {}
                }
            }
        } else {
            # Plain HTTP request — serve a simple status page with CORS
            $body = '{"status":"ok","service":"ppt-controller","port":' + $Port + '}'
            $httpResp = "HTTP/1.1 200 OK`r`nContent-Type: application/json`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`nContent-Length: $($body.Length)`r`n`r`n$body"
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($httpResp)
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush()
        }
    } catch {
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] Error handling client: $_" -ForegroundColor Red
    } finally {
        $Client.Close()
    }
}

# ──────────────────────────────────────────────
# Main server loop
# ──────────────────────────────────────────────

Write-Host ''
Write-Host '  ╔══════════════════════════════════════════════════════╗' -ForegroundColor DarkCyan
Write-Host '  ║       ☕ AI Café Presenter — PPT Controller         ║' -ForegroundColor DarkCyan
Write-Host '  ╚══════════════════════════════════════════════════════╝' -ForegroundColor DarkCyan
Write-Host ''
Write-Host "  Listening on ws://localhost:$Port" -ForegroundColor Green
Write-Host '  Waiting for presenter to connect...' -ForegroundColor Gray
Write-Host '  Press Ctrl+C to stop.' -ForegroundColor Gray
Write-Host ''

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
$listener.Start()

try {
    while ($true) {
        # AcceptTcpClient blocks until a connection arrives
        $client = $listener.AcceptTcpClient()
        Handle-Client -Client $client
    }
} catch {
    Write-Host "`n[$(Get-Date -f 'HH:mm:ss')] Server error: $_" -ForegroundColor Red
} finally {
    $listener.Stop()
    Write-Host "`n  Server stopped." -ForegroundColor Yellow
}
