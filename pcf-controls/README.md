# PCF Controls Workspace

This folder is a dedicated workspace for building multiple Power Apps Component Framework (PCF) controls.

It’s designed for experimentation: each control lives in its own folder under `controls/`, and you can optionally collect them into one (or more) Dataverse solutions under `solutions/`.

## Prerequisites

- Power Platform CLI (`pac`) (installed on this machine already)
- Node.js + npm (installed on this machine already)
- A Dataverse environment (for import/testing)
- Recommended VS Code extensions:
  - `danish-naglekar.pcf-builder`
  - `danish-naglekar.dataverse-devtools`

## Folder layout

- `controls/` — one subfolder per PCF control
- `solutions/` — one subfolder per Dataverse solution (optional but recommended)
- `scripts/` — helper scripts to create/build controls

## Create a new control (recommended)

From this folder in PowerShell:

- Create a field control and add it to a solution:
  - `./scripts/new-control.ps1 -ControlName HelloWorld -Template field`

- Create a dataset control:
  - `./scripts/new-control.ps1 -ControlName CasesKanban -Template dataset`

This will:
1. Run `pac pcf init` into `controls/<ControlName>`
2. `npm install` and `npm run build`
3. Create `solutions/<SolutionName>` (if missing)
4. Add a solution reference to the PCF project

## Build controls

- Build everything:
  - `./scripts/build-all.ps1`

- Build a single control:
  - `cd ./controls/<ControlName>`
  - `npm run build`

## Next steps (typical)

- Auth to your environment:
  - `pac auth create --url https://<org>.crm.dynamics.com`

- Build and import the solution (fast, no publish-all):
  - `./scripts/import-solution.ps1`

- Or build, import, AND publish all (slow):
  - `./scripts/import-solution.ps1 -PublishAll`

- Import only (skip build):
  - `./scripts/import-solution.ps1 -SkipBuild`

If you tell me your preferred workflow (CLI-first vs Maker Portal-first) and whether you want a single solution for all controls or one solution per control, I’ll tailor the build+import flow.
