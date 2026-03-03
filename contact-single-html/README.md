# Contact Single HTML — D365 Web Resource

A single-file HTML web resource that replicates the **Contact Code App** (`contact-code-app/`) functionality as a native Dynamics 365 web resource. No external servers, no MSAL, no CSP configuration required.

## Why Web Resource Instead of Code App?

| Aspect             | Code App                              | Web Resource (this)              |
| ------------------ | ------------------------------------- | -------------------------------- |
| **Hosting**        | `powerplatformusercontent.com`        | Inside D365 itself               |
| **CSP / IFrame**   | Required `frame-ancestors` fix        | Works natively — no CSP issues   |
| **Auth**           | SDK `getContext()` for params         | `Xrm.WebApi` — built-in, zero config |
| **Licence**        | Power Apps Premium per user           | Included with any D365 licence   |
| **Deployment**     | `pac code push`                       | Solution import or manual upload |
| **Data access**    | SDK `ContactsService`                 | `Xrm.WebApi.retrieveRecord()` direct |
| **Dependencies**   | React, Fluent UI, Vite, npm           | Zero (Chart.js via CDN)          |
| **Build step**     | `npm run build`                       | None — single file               |

## Architecture

```
D365 Contact Form → Tab → Web Resource (HTML)
  → Xrm.WebApi.retrieveRecord("contact", id, "?$select=...")
  → Renders editable fields + Chart.js energy charts client-side
  → Xrm.WebApi.updateRecord("contact", id, payload) on Save
```

## Features

- **Editable fields** — Boiler, Energy, Smart Home, and Service fields with inline editing
- **Choice dropdowns** — Boiler Make, Energy Tariff, HomeCare Cover Type
- **Boolean toggles** — CSS-only toggle switches for Yes/No fields
- **Date picker** — Click-to-edit date field with UK locale display
- **Save button** — Dirty detection, save feedback, Xrm.WebApi update
- **Energy usage charts** — 12-month electricity & gas area charts (Chart.js)
- **D365 IFrame compatible** — Chart sizing capped for IFrame viewport
- **Fallback ID** — Falls back to Chris Walker for development/testing

## Files

| File                            | Purpose                                     |
| ------------------------------- | ------------------------------------------- |
| `contact-energy-dashboard.html` | The complete web resource (single file)     |
| `README.md`                     | This file                                   |
| `scripts/deploy-webresource.py` | Python script to upload to D365 as a web resource |

## Contact ID Resolution

The page resolves the contact ID in priority order:

1. **`window.parent.Xrm.Page`** — when embedded as a web resource on a D365 form
2. **URL query parameters** — `?id=<guid>` from IFrame "Pass Parameters"
3. **Fallback** — Chris Walker (`7fba73b9-2461-ef11-bfe2-002248a36d0e`) for dev/testing

## Editable Fields

### Boiler & Heating (Column 1)
- Boiler Make (`mj_boilermake`) — Choice dropdown
- Boiler Model (`mj_boilermodel`) — Text input
- Installation Date (`mj_installationdate`) — Date picker
- HomeCare Cover (`mj_homecarecover`) — Toggle
- Cover Type (`mj_homecaretypeofcover`) — Choice dropdown

### Energy & Smart Home (Column 2)
- Energy Tariff (`mj_energytariff`) — Choice dropdown
- Smart Meter (`mj_smartmeter`) — Toggle
- Hive Thermostat (`mj_doyouhaveahivethermostat`) — Toggle
- Smart TRVs (`mj_doyouhavesmartradiatorvalves`) — Toggle
- EV Owner (`mj_utility_ev_owner`) — Toggle

### EV & Service (Column 3)
- EV Charger (`mj_homeevcharger`) — Toggle
- Priority Register (`mj_priorityregister`) — Toggle
- Repaired Recently (`mj_repairedrecently`) — Toggle
- Conversation Points (`mj_conversationpoints`) — Text (spans 2 columns)

## Deployment Options

### Option 1: Manual Upload via D365

1. Open **D365 → Settings → Customizations → Customize the System**
2. **Web Resources → New**
3. Set:
   - Name: `mj_/html/contactenergydashboard.html`
   - Display Name: `Contact Energy Dashboard`
   - Type: `Webpage (HTML)`
4. Upload `contact-energy-dashboard.html`
5. **Save and Publish**

### Option 2: Python Script

```powershell
cd contact-single-html
..\.venv\Scripts\python.exe scripts\deploy-webresource.py
```

### Option 3: Add to a Solution

After uploading, add the web resource to a solution for ALM:
1. Solutions → Open your solution → Add Existing → Web Resource
2. Select `mj_/html/contactenergydashboard.html`

## Embedding on a D365 Contact Form

### As a Web Resource (recommended)

1. Open the Contact form in the Form Designer
2. Add a new **Tab** (e.g. "Energy Dashboard")
3. Insert a **Web Resource** control
4. Set:
   - Web Resource: `mj_/html/contactenergydashboard.html`
   - Pass record object-type code and unique identifier: **Yes**
   - Restrict cross-frame scripting: **No**
5. Save and Publish

### As an IFrame (alternative)

1. Upload the HTML file to an Azure Web App or other host
2. Add an IFrame control to the form tab
3. Configure as per the `copilot-instructions.md` IFrame settings

## Dependencies

- **Chart.js 4.4.7** — loaded via CDN (`cdn.jsdelivr.net`)
- **Xrm.WebApi** — provided by the D365 runtime (no install needed)

## Development / Testing

To test locally outside D365, the page falls back to Chris Walker's contact ID. However, `Xrm.WebApi` won't be available — you'll see the error state explaining this. For local testing, you could:

1. Open the page directly in the D365 web resource editor preview
2. Embed it on a contact form in a dev environment
3. Use the Azure Web App version (`/EnergyDashboard` route) with server-side MSAL as an alternative local test path

## Choice Field Option Values

| Field           | Value     | Label            |
| --------------- | --------- | ---------------- |
| Boiler Make     | 124610000 | Worcester Bosch  |
| Boiler Make     | 124610001 | Vaillant         |
| Boiler Make     | 124610002 | Ideal            |
| Boiler Make     | 124610003 | Baxi             |
| Boiler Make     | 124610004 | Other/Unknown    |
| Energy Tariff   | 124610000 | Fixed            |
| Energy Tariff   | 124610001 | Variable         |
| Energy Tariff   | 124610002 | EV Tariff        |
| Energy Tariff   | 124610003 | Other            |
| HomeCare Type   | 124610000 | Boiler Only      |
| HomeCare Type   | 124610001 | Complete         |
| HomeCare Type   | 124610002 | Plumbing & Drain |
| HomeCare Type   | 124610003 | Electrical       |
