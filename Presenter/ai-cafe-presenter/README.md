# ☕ AI Café Presenter

A standalone, single-file HTML presenter application for live demos and presentations. Runs in VS Code's Simple Browser or any web browser — no frameworks, no build step, just vanilla HTML + CSS + JavaScript.

## What It Does

| Feature | Description |
|---------|-------------|
| **Chat Panel** | Left sidebar with an `<iframe>` — load any chat client, web app, or URL |
| **Content Viewer** | Right panel URL bar + `<iframe>` — browse any website, local HTML file, or app |
| **Draw Mode** | Full-screen `<canvas>` overlay for freehand annotations (hold **D** or click the button) |
| **PPT Control** | WebSocket connection to `ppt-controller.ps1` for remote PowerPoint slide navigation |
| **Screen Capture** | Uses the browser's `getDisplayMedia` API to capture and display another screen/window |
| **Resize** | Draggable divider between chat and content panels |
| **Zoom** | Cycle through 50% / 75% / 100% / 125% / 150% zoom on the content viewer |
| **Status Bar** | Shows current mode, PPT connection status, loaded URL, and time |

## Architecture

```
presenter.html (~600 lines)
├── <style>     All CSS inline — dark VS Code-inspired theme
├── HTML        Toolbar, sidebar, content area, overlays, modals
└── <script>    All JavaScript inline — zero dependencies

ppt-controller.ps1 (~250 lines)
├── TCP listener on port 8080
├── WebSocket handshake (RFC 6455)
├── Frame read/write (text frames, masking)
└── PowerPoint COM automation (SlideShowView)
```

**Why it looks like a VS Code app**: Open the HTML file in VS Code's Simple Browser panel (`Ctrl+Shift+P` → "Simple Browser: Show") and it renders inside a VS Code tab.

## Quick Start

### 1. Open the Presenter

**Option A — VS Code Simple Browser (recommended):**
1. Press `Ctrl+Shift+P` → type `Simple Browser: Show`
2. Paste the file path: `file:///C:/path/to/Presenter/ai-cafe-presenter/src/presenter.html`

**Option B — Run the launch script:**
```powershell
cd Presenter\ai-cafe-presenter
.\scripts\Start-Presenter.ps1
```

**Option C — VS Code Task:**
Press `Ctrl+Shift+P` → `Tasks: Run Task` → `Open Presenter (Simple Browser)`

### 2. Start PowerPoint Controller (optional)

Only needed if you want to control PowerPoint slides from the presenter:

```powershell
.\scripts\Start-PptController.ps1
```

Or via VS Code Task: `Start PPT Controller`

PowerPoint must be running in **SlideShow mode** for navigation to work.

### 3. Start Everything at Once

VS Code Task: `Start Everything (Presenter + PPT)` — launches both in sequence.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `D` (hold) | Enter draw mode (release to exit) |
| `Esc` | Exit draw mode / close help / stop capture |
| `C` | Clear all annotations |
| `→` / `PageDown` | Next PPT slide |
| `←` / `PageUp` | Previous PPT slide |
| `F11` | Toggle fullscreen |
| `Ctrl+L` | Focus URL bar |
| `Ctrl+Shift+B` | Toggle chat sidebar |
| `?` | Toggle help dialog |
| `1`–`7` | Select drawing colour |
| `[` / `]` | Decrease / increase brush size |

## Drawing Features

- **7 colours**: Red, Blue, Green, Yellow, Pink, White, Black
- **Adjustable brush**: 1px–20px via slider or `[` / `]` keys
- **Two modes**: Hold `D` for temporary draw, click ✏️ button for sticky toggle
- **Clear**: Click 🗑️ or press `C`
- Annotations persist across draw sessions until cleared

## PPT WebSocket Protocol

The presenter connects to `ws://localhost:8080` and sends JSON commands:

```json
{ "action": "next" }
{ "action": "previous" }
{ "action": "first" }
{ "action": "last" }
{ "action": "goto", "slide": 5 }
{ "action": "status" }
```

Server responds with:

```json
{ "slide": 3 }
{ "slide": 3, "state": "Running" }
{ "error": "PowerPoint is not in SlideShow mode" }
```

## Project Structure

```
ai-cafe-presenter/
├── .vscode/
│   ├── settings.json          VS Code workspace settings
│   └── tasks.json             Launch tasks
├── scripts/
│   ├── Start-Presenter.ps1    Open presenter in browser/VS Code
│   └── Start-PptController.ps1  Start WebSocket PPT server
├── src/
│   ├── presenter.html         THE APP — single-file, ~600 lines
│   └── ppt-controller.ps1     WebSocket server for PPT control
└── README.md
```

## Requirements

- **Any modern browser** (Chrome, Edge, Firefox) or VS Code Simple Browser
- **PowerShell 5.1+** for the PPT controller
- **PowerPoint** (desktop, with SlideShow running) for slide control
- No Node.js, no npm, no build tools

## Tips

- The chat panel URL persists during the session — load your Azure-hosted chat client once
- Screen capture works best with a second monitor
- Draw annotations render on top of everything, including screen capture
- The PPT controller auto-reconnects every 5 seconds if the connection drops
- Toast notifications appear bottom-right for status updates
