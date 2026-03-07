# Create Power Page

CLI scaffolder that generates a **branded Power Pages SPA** (React + TypeScript + Vite) with
contact authentication, a sample My Cases page, and mock data for local development.

> **Full documentation:** [CreatePowerPortalCodeStarter.md](./CreatePowerPortalCodeStarter.md)
> — prerequisites, quick start, all manual Power Pages steps, troubleshooting, and sharing guide.
>
> **GitHub:** https://github.com/MarcPhilipJones/marcscloud (folder: `create-power-page/`)

## Quick Start

```bash
# From the workspace root
node create-power-page/index.mjs

# Or from inside this folder
npm install
npm start
```

You will be prompted for site name, primary colour, and output folder. The tool copies the
template, replaces tokens, and runs `npm install` in the generated project.

## After Generation

```bash
cd ./your-project-folder
npm run dev      # local dev server with mock data
npm run deploy   # build and deploy to Power Pages
```

Then complete the [Manual Power Pages Steps](./CreatePowerPortalCodeStarter.md#7-manual-power-pages-steps-post-deploy)
in the maker portal (activate site, set visibility, add table permissions, restart).
