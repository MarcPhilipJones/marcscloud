# Power Pages Code Site Starter — Complete Guide

> **Last updated:** 7 March 2026
>
> Internal CLI scaffolder for branded Power Pages SPA demo sites. Generates a React + TypeScript + Vite project with authentication, a sample "My Cases" page using the Power Pages Web API, and mock data for local development.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start — For Marc](#quick-start--for-marc)
4. [Quick Start — For Colleagues](#quick-start--for-colleagues)
5. [What Gets Generated](#what-gets-generated)
6. [Local Development](#local-development)
7. [Build and Deploy](#build-and-deploy)
8. [Manual Power Pages Steps (Post-Deploy)](#manual-power-pages-steps-post-deploy)
9. [Important Notes and Gotchas](#important-notes-and-gotchas)
10. [Customising the Template](#customising-the-template)
11. [Sharing With Colleagues](#sharing-with-colleagues)
12. [Validation Checklist](#validation-checklist)
13. [Troubleshooting](#troubleshooting)

---

## Overview

`create-power-page` is a Node.js CLI tool that scaffolds a branded Power Pages SPA (Single-Page Application). You answer three prompts — site name, primary colour, output folder — and it generates a production-ready project.

**What it generates:**

- React 19 + TypeScript + Vite project
- Deploys with `pac pages upload-code-site` (Power Platform CLI)
- Relative asset paths (`base: "./"`) so Power Pages loads JS/CSS correctly
- Sign In / Sign Out buttons wired to Power Pages authentication (`/SignIn`, `/Account/Login/LogOff`)
- Sample **My Cases** page that queries the `incident` table via the Power Pages Web API (`/_api/incidents`)
- Mock data for local development (no Dataverse connection needed locally)
- Anti-forgery token handling for non-GET API requests
- Branded with your chosen colour (primary + auto-calculated hover shade)

**What it does NOT do:**

- Create Power Pages sites in the environment (that happens on first `pac pages upload-code-site`)
- Configure table permissions, site visibility, or authentication providers
- Provision SSL certificates (Power Pages handles this automatically after activation)

---

## Prerequisites

Before using the scaffolder, ensure you have:

| Requirement | How to check | Install link |
|---|---|---|
| **Node.js 20+** | `node --version` | https://nodejs.org/ |
| **npm** (comes with Node) | `npm --version` | Included with Node.js |
| **Power Platform CLI (PAC)** | `pac --version` | https://learn.microsoft.com/power-platform/developer/cli/introduction |
| **Authenticated PAC profile** | `pac auth list` | `pac auth create --environment <url>` |
| **Git** (for cloning this repo) | `git --version` | https://git-scm.com/ |

**Environment requirements:**

- A **Power Platform environment** with Power Pages enabled
- The user running `pac pages upload-code-site` needs **System Administrator** or **System Customizer** role
- End users accessing the deployed site need a **Power Pages licence** (or the environment must have appropriate capacity)

---

## Quick Start — For Marc

From the workspace root (where `create-power-page/` is a subfolder):

```bash
node create-power-page/index.mjs
```

Or from inside the `create-power-page` folder:

```bash
npm start
```

You will be prompted for:

1. **Site name** — e.g. "Contoso Customer Portal" (becomes the page title and header)
2. **Primary colour** — hex code, e.g. `#0078d4` (used for buttons, links, header)
3. **Output folder** — where to create the project, e.g. `./contoso-customer-portal`

The tool then:

1. Copies the template directory
2. Replaces all `{{TOKEN}}` placeholders with your values
3. Runs `npm install` in the generated project
4. Prints the manual post-deploy steps

---

## Quick Start — For Colleagues

### 1. Clone the repository

```bash
git clone https://github.com/MarcPhilipJones/marcscloud.git
cd marcscloud/create-power-page
```

### 2. Install the scaffolder's dependencies

```bash
npm install
```

This only installs `prompts` (the interactive CLI library). It's fast.

### 3. Run the scaffolder

Navigate to the folder where you want your new project created, then run:

```bash
node /path/to/create-power-page/index.mjs
```

Or stay in the `create-power-page` folder and run:

```bash
npm start
```

The output folder prompt lets you specify where the project goes (relative to your current directory).

### 4. Develop locally

```bash
cd ./your-project-folder
npm run dev
```

This starts a Vite dev server with **mock data** — no Dataverse connection needed.

### 5. Deploy to Power Pages

```bash
npm run deploy
```

This runs `npm run build` then `pac pages upload-code-site --rootPath .`

### 6. Complete the manual steps

See [Manual Power Pages Steps](#manual-power-pages-steps-post-deploy) below — these must be done in the Power Pages maker portal after the first deploy.

---

## What Gets Generated

The scaffolder creates this project structure:

```
your-project-folder/
├── eslint.config.js          # ESLint configuration
├── index.html                # Entry HTML (title = your site name)
├── package.json              # Dependencies and scripts
├── powerpages.config.json    # Power Pages deployment config
├── tsconfig.json             # TypeScript config (references)
├── tsconfig.app.json         # App TypeScript config
├── tsconfig.node.json        # Node TypeScript config
├── vite.config.ts            # Vite config (base: "./" for Power Pages)
└── src/
    ├── main.tsx              # React entry point
    ├── App.tsx               # Router setup (Home + Cases pages)
    ├── index.css             # All styles (branded with your colour)
    ├── components/
    │   ├── Header.tsx        # Navigation header with site name
    │   └── AuthButton.tsx    # Sign In / Sign Out (Power Pages auth)
    ├── pages/
    │   ├── Home.tsx          # Welcome page with link to Cases
    │   └── CaseList.tsx      # My Cases page (search, filter, status badges)
    ├── services/
    │   ├── api.ts            # OData fetch wrapper + anti-forgery tokens
    │   ├── cases.ts          # Case query (incidents by contact)
    │   └── mockData.ts       # Mock case data for local dev
    └── types/
        └── index.ts          # TypeScript interfaces + status/priority maps
```

### Token Replacements

| Token | Replaced with | Example |
|---|---|---|
| `{{SITE_NAME}}` | Your site name | Contoso Customer Portal |
| `{{PROJECT_SLUG}}` | Slugified site name | contoso-customer-portal |
| `{{PRIMARY_COLOUR}}` | Your hex colour | #0078d4 |
| `{{PRIMARY_HOVER}}` | Auto-darkened (15%) | #00669f |

Tokens are replaced in all text files: `.ts`, `.tsx`, `.css`, `.json`, `.html`, `.js`, `.mjs`, `.yml`, `.yaml`, `.md`. Binary files (images, etc.) are copied as-is.

---

## Local Development

```bash
cd your-project-folder
npm run dev
```

- Starts Vite dev server (typically `http://localhost:5173`)
- **Uses mock data** — the `api.ts` service detects `import.meta.env.DEV` and returns fake case records
- Authentication buttons render but don't function locally (Power Pages auth only works on the deployed site)
- Hot Module Replacement (HMR) for instant CSS/component updates

### Available npm Scripts

| Script | Command | Purpose |
|---|---|---|
| `dev` | `vite` | Local dev server with HMR and mock data |
| `build` | `tsc -b && vite build` | Type-check and production build to `dist/` |
| `lint` | `eslint .` | Run ESLint checks |
| `preview` | `vite preview` | Preview the production build locally |
| `deploy` | `npm run build && pac pages upload-code-site --rootPath .` | Build and deploy to Power Pages |

---

## Build and Deploy

### First-time deploy

```bash
cd your-project-folder
npm run deploy
```

This runs two commands:

1. `npm run build` — TypeScript compile + Vite production build to `dist/`
2. `pac pages upload-code-site --rootPath .` — uploads the site to Power Pages

On the **first deploy**, PAC creates a new Power Pages code site in your authenticated environment. The `powerpages.config.json` file tells PAC the site name and where to find the built files.

### Subsequent deploys

Same command:

```bash
npm run deploy
```

PAC detects the existing site (by name in `powerpages.config.json`) and updates it.

### Pre-deploy checklist

- [ ] `pac auth list` shows an active profile for the correct environment
- [ ] `npm run build` completes without errors
- [ ] `dist/` folder contains `index.html` and `assets/` with bundled JS/CSS

---

## Manual Power Pages Steps (Post-Deploy)

These steps **must be completed manually** in the Power Pages maker portal after the first deploy. They cannot be automated via CLI.

### Step 1: Activate the Site

After the first `pac pages upload-code-site`, the site is created but **inactive**.

1. Go to the **Power Pages maker portal**: https://make.powerpages.microsoft.com/
2. Select your environment
3. Find your site under **Inactive sites**
4. Click **Reactivate**

### Step 2: Set Site Visibility to Public

By default, sites are private (only users with explicit access can view them). For demo or anonymous access:

1. In the Power Pages maker portal, click **Edit site**
2. Go to **Security** → **Site visibility**
3. Change to **Public**
4. Save

> **Cannot be done via API** — this must be changed in the Power Pages UI.
>
> **Developer environments cannot be made public** — you need a sandbox or production environment for public sites.

### Step 3: Wait for SSL Certificate

After activation, Power Pages provisions an SSL certificate for your site's URL. This can take **up to 1-2 hours**.

During this period, you may see:

```
NET::ERR_CERT_COMMON_NAME_INVALID
```

This is normal. The certificate will provision automatically — no action required. Just wait and retry.

### Step 4: Add Table Permission for Cases

The sample "My Cases" page queries the `incident` (Case) table. Power Pages blocks all table access by default — you must explicitly grant permission.

1. In the Power Pages maker portal, click **Edit site**
2. Go to **Security** → **Table permissions**
3. Click **+ New permission**
4. Configure:

| Field | Value |
|---|---|
| **Name** | Contact Cases Read |
| **Table** | Case (`incident`) |
| **Access type** | Contact access |
| **Relationship** | Customer (`customerid`) |
| **Read** | Checked |

5. Click **+ Add roles** → select **Authenticated Users**
6. Click **Save**

This allows authenticated contacts to read their own cases (where they are the customer on the case).

**Columns exposed by the template's query:**

`incidentid`, `title`, `ticketnumber`, `createdon`, `modifiedon`, `statuscode`, `statecode`, `prioritycode`, `caseorigincode`, `_customerid_value`, `_subjectid_value`

If you restrict column access, ensure at minimum these columns are readable.

### Step 5: Restart the Site

After changing security settings (table permissions, site visibility, authentication):

1. In the Power Pages maker portal, click **Edit site**
2. Click the **...** (more) menu
3. Click **Restart site**

Security changes do not take effect until the site is restarted.

### Step 6: Configure Profile Redirect (Optional)

By default, after sign-in, Power Pages redirects users to a profile page. If you want users to land on the homepage instead:

1. In the Power Pages maker portal, click **Edit site**
2. Go to **Advanced settings** (or **Site settings** in the portal management app)
3. Find the setting: `Authentication/Registration/ProfileRedirectEnabled`
4. Set its value to `false`
5. Save and restart the site

### Step 7: Register a Test Contact

To test the authenticated experience:

1. Visit your site's public URL
2. Click **Sign In**
3. Click **Register** (if using local authentication)
4. Register with an email address that matches a **Dataverse contact** record
5. After registration and sign-in, the "My Cases" page shows cases where the contact is the customer

> **Tip:** If you don't see any cases, verify the contact has cases assigned to them in Dataverse (the `customerid` lookup on the `incident` record must point to the contact).

---

## Important Notes and Gotchas

### Site visibility

- Cannot be set via CLI or API — must be changed in the Power Pages maker portal UI
- **Developer environments** do not support public site visibility
- For demos, you need a **sandbox** or **production** environment

### Table security

- Power Pages blocks **all** Dataverse table access by default
- Table permissions are **environment-specific** — they are not part of the deployed code
- The scaffold documents the required permission pattern but does not create the permission records
- If you add new Dataverse tables to the app, you must create corresponding table permissions

### `.powerpages-site/` folder

- This folder is **not** included in the template
- It is generated by the Power Pages platform **after deployment**
- After your first deploy, you'll see a `.powerpages-site/` folder appear in your project — this is normal
- Do not commit this folder to Git (add it to `.gitignore`)

### Default sample uses `incident`

- The "My Cases" page queries the `incident` (Case) table
- This gives colleagues a working pattern for contact-authenticated, relationship-scoped data access
- The same pattern works for any Dataverse table — just change the entity set name, create a new service file, and add the corresponding table permission

### Anti-forgery tokens

- All non-GET API requests require an anti-forgery token
- The `api.ts` service handles this automatically — it fetches and caches the token from `/_api/antiforgery/token`
- Tokens expire periodically; the service fetches a new one when needed
- Anti-forgery only works on the deployed Power Pages site, not in local dev

### Mock data in development

- When running `npm run dev`, the app detects `import.meta.env.DEV === true`
- All API calls return mock data from `services/mockData.ts`
- This means you can develop locally without any Dataverse connection
- Mock data is never included in the production build

### Vite `base: "./"` configuration

- This is **critical** for Power Pages — without it, asset paths resolve as absolute (`/assets/index.js`) which breaks on the Power Pages domain
- Do not change `base` in `vite.config.ts` unless you understand the Power Pages URL structure

---

## Customising the Template

### Adding a new page

1. Create a new component in `template/src/pages/YourPage.tsx`
2. Add a route in `template/src/App.tsx`
3. Add a navigation link in `template/src/components/Header.tsx`
4. If the page uses Dataverse data, create a service in `template/src/services/`
5. Add mock data for the new entity in `template/src/services/mockData.ts`

### Adding a new Dataverse table

1. Create a service file (copy `cases.ts` as a pattern):

```typescript
import { getRecords } from "./api";

const ENTITY_SET = "your_entities";   // Dataverse entity set name
const DEFAULT_SELECT = ["field1", "field2"].join(",");

export async function getMyRecords(contactId: string) {
  return getRecords(ENTITY_SET, {
    $select: DEFAULT_SELECT,
    $filter: `_customerid_value eq ${contactId}`,
    $orderby: "createdon desc",
    $top: "50",
  });
}
```

2. Add a mock data array in `mockData.ts`
3. Add the dev mock route in `api.ts` → `devMockFetch()`
4. After deployment, create a **table permission** in Power Pages for the new table

### Adding a new token

1. Add the token placeholder (e.g. `{{MY_TOKEN}}`) in the template files where needed
2. Add the prompt in `index.mjs` (in the `prompts()` call)
3. Add the replacement in the `replacements` object in `index.mjs`

### Modifying styles

All styles are in `template/src/index.css`. The primary colour is applied via `{{PRIMARY_COLOUR}}` and `{{PRIMARY_HOVER}}` tokens. Edit the CSS directly — it uses standard CSS (no preprocessor).

---

## Sharing With Colleagues

This tool is shared via **Git**, not npm publishing.

### For the repository owner (Marc)

The repository is hosted on GitHub. After making changes:

```bash
cd create-power-page
git add .
git commit -m "Description of changes"
git push
```

### For colleagues

#### First time

```bash
git clone https://github.com/MarcPhilipJones/marcscloud.git
cd marcscloud/create-power-page
npm install
```

#### Running the scaffolder

From any directory where you want the new project created:

```bash
node /path/to/create-power-page/index.mjs
```

Or from inside the cloned folder:

```bash
npm start
```

#### Getting updates

```bash
cd create-power-page
git pull
npm install   # in case dependencies changed
```

### What colleagues need

| Requirement | Notes |
|---|---|
| Git | To clone the repo |
| Node.js 20+ | To run the scaffolder and the generated project |
| Power Platform CLI (`pac`) | To deploy generated projects |
| PAC auth profile | `pac auth create --environment https://your-org.crm.dynamics.com` |

---

## Validation Checklist

When modifying the scaffold itself, verify these before pushing changes:

- [ ] **Generate a test project**: Run the CLI and create a sample project
- [ ] **Build succeeds**: Run `npm run build` in the generated project — no TypeScript or Vite errors
- [ ] **No unreplaced tokens**: Search the generated project for `{{` — there should be zero matches:
  ```bash
  grep -r "{{" ./generated-project/src/
  ```
- [ ] **Dev server works**: Run `npm run dev` — mock data renders correctly
- [ ] **Styles are branded**: Check that the primary colour appears in buttons, header, and links
- [ ] **Deploy works** (if you changed deploy-related files): Run `npm run deploy` against a test environment

---

## Troubleshooting

### `pac` command not found

The Power Platform CLI is not installed or not in your PATH.

- **Install**: https://learn.microsoft.com/power-platform/developer/cli/introduction
- **Verify**: `pac --version`
- On Windows, if installed via the VS Code extension, it may only be available inside VS Code terminals

### `pac auth` — no active profile

```
Error: No active auth profile found
```

Create an auth profile for your environment:

```bash
pac auth create --environment https://your-org.crm4.dynamics.com
```

Then select it:

```bash
pac auth select --index 1
```

### SSL certificate error after deploy

```
NET::ERR_CERT_COMMON_NAME_INVALID
```

This is normal after first activation. The SSL certificate can take **up to 1-2 hours** to provision. Wait and retry — no action needed.

### 403 error on API calls (table permissions)

```
403 Forbidden
```

The Dataverse table does not have a table permission configured for the current user's web role.

1. Go to Power Pages maker portal → Edit site → Security → Table permissions
2. Verify a permission exists for the table you're querying (e.g. `incident`)
3. Verify the permission has the correct **Access type** (Contact access) and **Relationship** (customerid)
4. Verify **Authenticated Users** role is assigned
5. **Restart the site** after making changes

### 403 — `AttributePermissionIsMissing`

A specific column in your `$select` is not included in the table permission's allowed columns.

- By default, table permissions allow all columns
- If column-level security is configured, ensure all queried columns are permitted

### Anti-forgery token errors

```
Error: Failed to fetch anti-forgery token
```

- Anti-forgery tokens only work on the deployed Power Pages site
- In local dev (`npm run dev`), the mock data path bypasses token fetching
- If this happens on the deployed site, try clearing browser cookies and reloading

### No cases displayed after sign-in

1. Verify the signed-in contact has cases in Dataverse where they are the **Customer** (`customerid` lookup)
2. Verify the table permission is configured (see 403 error above)
3. Open browser DevTools → Network tab → look for the `/_api/incidents` request and check the response

### Deploy succeeds but site shows old content

Power Pages caches aggressively.

1. **Restart the site** in the maker portal
2. Hard-refresh the browser (Ctrl+Shift+R)
3. Try an incognito/private window

### Generated project has TypeScript errors

If `npm run build` fails with type errors after modifying the template:

1. Check that new components import types correctly
2. Run `npx tsc --noEmit` for detailed error messages
3. Ensure `tsconfig.app.json` includes the `src` folder

---

## Architecture Reference

### How Power Pages authentication works in this template

1. User clicks **Sign In** → redirects to `/SignIn?returnUrl=%2F`
2. Power Pages handles the authentication flow (local registration, Azure AD B2C, etc.)
3. After sign-in, Power Pages sets `window.Microsoft.Dynamic365.Portal.User` with the contact's details
4. `AuthButton.tsx` reads this object to display the user's name and show Sign Out
5. `CaseList.tsx` reads `contactId` from the portal user object to query "my cases"

### How the Web API integration works

1. `api.ts` provides `apiFetch()` — a wrapper around `fetch()` that:
   - In **dev mode**: returns mock data (no network requests)
   - In **production**: fetches from `/_api/<entitySet>` with anti-forgery token
2. `cases.ts` provides `getMyCases(contactId)` — queries `/_api/incidents` filtered by `_customerid_value`
3. The Power Pages Web API (`/_api/`) is a built-in OData endpoint secured by table permissions
