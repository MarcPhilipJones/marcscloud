# Azure Logic Apps Consumption Development

This workspace is configured for Azure Logic Apps (Consumption) development.

## Azure Cost Control (MANDATORY)

**Always prompt Marc for approval before provisioning, deploying, or recommending any Azure resource that incurs cost.** This workspace is used for presales — usage is light and costs must be kept low. This applies to:

- Creating or scaling Azure resources (VMs, App Services, Functions, Logic Apps, Storage, Cognitive Services, etc.)
- Deploying ARM/Bicep templates that provision billable resources
- Recommending paid-tier services when free/consumption tiers may suffice
- Any `az deployment` or `az resource create` commands

**Before proceeding**, confirm: the resource name, SKU/tier, estimated cost, and get explicit approval.

## Azure CLI Default Login

When using Azure CLI, always ensure the PATH includes the CLI and use these defaults:

| Property         | Value                                             |
| ---------------- | ------------------------------------------------- |
| **Subscription** | ME-D365DemoTSCE63319057-marcjones-1               |
| **Tenant**       | 996f568a-cc69-450a-b684-ae784069e679              |
| **User**         | admin@D365DemoTSCE63319057.onmicrosoft.com        |
| **CLI Path**     | `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin` |

Add to PATH at the start of any terminal session:

```powershell
$env:PATH = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin;$env:PATH"
```

### Persistent CLI Defaults (configured February 2026)

Azure CLI defaults are stored in `C:\Users\marcjones\.azure\config`:

| Default            | Value        |
| ------------------ | ------------ |
| **Resource Group** | `MJ_WebApps` |
| **Location**       | `westeurope` |

These persist across sessions — no need to pass `--resource-group` or `--location` for commands targeting `MJ_WebApps`.

**On first use in a new session**, Copilot should:

1. Run `az account show` to verify login is still valid
2. If login has expired, run `az login` and let the browser handle re-authentication
3. Run `az configure --list-defaults` to confirm defaults are still set
4. If defaults are missing, re-apply: `az configure --defaults group=MJ_WebApps location=westeurope`

**To change defaults** for a different resource group:

```powershell
az configure --defaults group=NewGroupName
```

Or override per-command with `--resource-group` when needed.

## Azure Authentication & Conditional Access Rules

This tenant has Microsoft Entra Conditional Access policies that enforce MFA on ARM write operations. These rules prevent auth dead-ends where a command silently fails or prompts for MFA that can't be satisfied.

### ARM vs Kudu/SCM Operations

| Operation Type | Examples | Subject to ARM MFA? |
|---------------|----------|---------------------|
| **ARM writes** | `az webapp config appsettings set`, `az resource create`, `az deployment group create`, `az webapp update` | **Yes** — requires MFA-capable auth |
| **Kudu / SCM** | `az webapp up` (ZIP deploy), `az webapp deployment source config-zip`, Kudu REST API | **No** — uses SCM credentials, bypasses ARM MFA |

**Key implication**: A deployment via `az webapp up` may succeed while `az webapp config appsettings set` in the same session fails, if the auth method can't satisfy MFA.

### Authentication Method Rules

1. **Always use interactive browser authentication**:
   - VS Code "Azure: Sign In" (Azure Account extension)
   - `az login` (opens browser — satisfies MFA interactively)
   - **NEVER use `az login --use-device-code` for ARM changes** — device code flow cannot satisfy MFA `acrs` claims challenges

2. **For non-interactive / automated scenarios, use a Service Principal**:
   - Client credentials with certificate or secret
   - `az login --service-principal --username <appId> --password <secret> --tenant <tenantId>`
   - Service Principals bypass interactive MFA (they authenticate via credential, not user identity)
   - This is already the pattern used for Dataverse scripts (MSAL client credentials)

3. **Before suggesting any ARM write command**, verify the current auth method can satisfy MFA. If device-code or token-based auth was used, warn that the command may fail and recommend re-authenticating via browser.

### Pre-Command Checklist for ARM Writes

Before running any of these commands, Copilot should verify auth:
- `az webapp config appsettings set`
- `az webapp update`
- `az resource create` / `az resource update`
- `az deployment group create` / `az deployment group validate`
- `az functionapp config appsettings set`
- Any `az` command that creates, updates, or deletes Azure resources

**Recommended approach**: Run the command with browser-based `az login` auth.
**Why this works**: Browser flow completes MFA interactively, satisfying Conditional Access.
**Fallback**: Use a Service Principal if non-interactive access is required.

### Answer Format for Azure Operations

When answering questions about Azure CLI commands, deployment, or configuration, prefer this structure:

1. **Recommended approach** — the lowest-friction option that satisfies MFA
2. **Why this works** — one sentence
3. **Fallback options** — only if needed

## Azure Web Apps Project

Deployed Node.js + Express demo app with multi-customer pages.

| Property           | Value                                          |
| ------------------ | ---------------------------------------------- |
| **Project Folder** | `azure-webapps/`                               |
| **App Name**       | `mj-webapps-demo-2026`                         |
| **URL**            | https://mj-webapps-demo-2026.azurewebsites.net |
| **Resource Group** | `MJ_WebApps`                                   |
| **Region**         | West Europe                                    |
| **SKU**            | F1 Free (£0/month)                             |
| **Runtime**        | Node.js 20 LTS (Linux)                         |
| **Entry Point**    | `server.js`                                    |

### Routes

| Route                    | Description                                                  |
| ------------------------ | ------------------------------------------------------------ |
| `/`                      | Landing page with links to all customer pages                |
| `/CustomerA`             | Customer A portal (teal background)                          |
| `/CustomerB`             | Customer B portal (amber background)                         |
| `/ContactDemo?id=<guid>` | Dataverse contact details — modern card layout for embedding |
| `/api/contact/:id`       | JSON API — fetches contact from Dataverse (server-side auth) |
| `/api/contact/:id/photo` | Proxied contact photo from Dataverse entity image            |
| `/health`                | JSON health check                                            |

### ContactDemo Page (February 2026)

Displays all known details about a Dataverse contact in a modern card-based layout. Designed to be embedded as an IFrame in a D365 Model-Driven App contact form.

**Architecture:**

- Backend (`/api/contact/:id`) uses MSAL client-credentials flow to fetch contact from Dataverse — secrets stay server-side
- Frontend (`/ContactDemo`) is a single HTML page that calls the API and renders cards client-side
- `dataverse-client.js` — reusable MSAL + Dataverse OData wrapper with token caching

**Card groups** (only shown when data exists):

1. Personal Information — name, job title, department, DOB, gender, marital status
2. Contact Details — emails, phones, fax, website (clickable links)
3. Primary Address — street, city, postcode, country
4. Secondary Address
5. Company & Management — company name (polymorphic lookup), manager, assistant
6. Boiler & Heating — boiler make/model, HomeCare, installation date
7. Energy & Smart Home — tariff, smart meter, Hive, EV charger, priority register
8. Communication Preferences — do-not-contact flags, GDPR opt-out
9. Analysis & Notes — conversation points/logic (full width)
10. System — status, created/modified dates

**Key technical notes:**

- `parentcustomerid` is a polymorphic Customer lookup — cannot be used in `$select`. Dataverse returns it automatically as `_parentcustomerid_value`
- Uses OData annotation `OData.Community.Display.V1.FormattedValue` for picklist/lookup display names
- Boolean fields render as Yes/No pills
- **Contact photos**: Dataverse stores entity images at `contacts({id})/entityimage/$value`. The `/api/contact/:id/photo` endpoint proxies this — returns image bytes with 5-min cache, or 404 if no photo. Frontend tries to load the photo after rendering; if it succeeds, replaces the initials avatar with the real photo. Falls back silently to initials if no photo exists.

**Azure App Settings** (configured on web app):

- `DATAVERSE_BASE_URL`, `DATAVERSE_TENANT_ID`, `DATAVERSE_CLIENT_ID`, `DATAVERSE_CLIENT_SECRET`

**Dependencies added:** `@azure/msal-node`

### Embedding in D365 Model-Driven App Forms

**Method:** IFrame control on a form tab.

**Correct IFrame configuration:**

| Setting                                                          | Value                                                        |
| ---------------------------------------------------------------- | ------------------------------------------------------------ |
| URL                                                              | `https://mj-webapps-demo-2026.azurewebsites.net/ContactDemo` |
| Pass record object-type code and unique identifier as parameters | **Yes**                                                      |
| Restrict cross-frame scripting (Security)                        | **No** (must be false)                                       |
| Scrolling                                                        | `auto`                                                       |
| Border                                                           | `false`                                                      |

**CRITICAL:** The URL must **NOT** have a hardcoded contact ID (e.g. `?id=abc-123`). When "Pass Parameters" is true, D365 automatically appends `&typename=contact&type=2&id={current-record-guid}`. The page's `getContactId()` function reads the `id` parameter.

**Currently embedded on:**

- Form: "Contact for Utilities (Interactive)" → Tab: "Contact Details" → IFrame: `IFRAME_MJWebPage`

### Inspecting D365 Form Configuration via API

Script: `scripts/inspect_contact_form.py` — queries `systemforms` entity, parses the formxml, and dumps tab/section/control structure including IFrame parameters.

```python
# Find forms by entity and name
filt = "objecttypecode eq 'contact' and contains(name, 'Utilities')"
url = f"{base}/api/data/{ver}/systemforms?$filter={filt}&$select=formid,name,type,formxml"
```

IFrame controls have classid `{FD2A7985-3187-444E-908D-6624B21F69C0}` and parameters including `<Url>`, `<PassParameters>`, `<Security>`, `<Scrolling>`, `<Border>`.

### Redeploy After Changes

```powershell
cd azure-webapps
$env:PATH = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin;$env:PATH"
az webapp up --name mj-webapps-demo-2026 --resource-group MJ_WebApps
```

### Notes

- UK South region had zero F1 free-tier quota — deployed to West Europe instead
- App name must be globally unique across all Azure customers
- `node_modules/` is excluded from zip deployment; Azure runs `npm install` during build
- Available Node.js runtimes (Feb 2026): `NODE:24-lts`, `NODE:22-lts`, `NODE:20-lts`

## Workspace Guidelines

- Use Azure Resource Manager (ARM) templates for deployment
- Follow Logic Apps workflow definition schema standards
- Keep workflow definitions in JSON format
- Use parameters for environment-specific values
- Test workflows locally using VS Code extension

## Development Checklist

- [x] Create copilot-instructions.md file
- [ ] Scaffold Logic Apps project structure
- [ ] Create sample workflow definitions
- [ ] Create configuration and parameter files
- [ ] Install Azure Logic Apps extension
- [ ] Create README documentation

## Hardware Setup

Key peripherals attached via Surface Thunderbolt 4 Dock:

- **Monitor**: DELL U3423WE (ultrawide)
- **Keyboard**: Logitech MX Keys (Bluetooth)
- **Mouse**: Logitech MX Master 3S (Bluetooth)
- **Webcam**: Logitech BRIO (USB)
- **VOL20**: Bluetooth volume dial (audio control only)

## SpecStory Chat History

The **SpecStory** extension (`specstory.specstory-vscode`) automatically saves Copilot chat history to markdown files.

### Location

Chat history is stored in: `.specstory/history/`

### Searching Previous Chats

```powershell
# List recent chat files
Get-ChildItem ".specstory\history" | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Search for chats about a topic
Get-ChildItem ".specstory\history" -Filter "*field*"

# Find chats from last 24 hours
Get-ChildItem ".specstory\history" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-1) }
```

### Reading Chat History

Chat files are markdown with timestamps and full conversation content. Read them to recover context from previous sessions.

### Key Learning: Cross-Session Memory

When the user asks "remember what we did" or "what did we learn in another chat":

1. Search `.specstory/history/` for relevant chat files by filename or content
2. Read the markdown files to extract learnings, code patterns, or decisions
3. Add important discoveries to this `copilot-instructions.md` file for permanent memory

This enables carrying forward learnings across Copilot chat sessions.

### Proactive Context Recovery

**Before starting significant new work**, Copilot should:

1. **Search chat history for related prior work** - Look for chats about the same entity, API, or project

    ```powershell
    # Example: Before working on Field Service, search for prior work
    Get-ChildItem ".specstory\history" -Filter "*field*service*"
    Select-String -Path ".specstory\history\*.md" -Pattern "work.?order|field.?service" -List
    ```

2. **Check for existing patterns in this workspace** - Avoid reinventing solutions that already exist in `scripts/`, `src/`, or prior sessions

3. **Surface relevant findings** - Briefly mention: "Found prior work on this topic in [chat file] - incorporating that approach"

**When to search:**

- User mentions a Dataverse entity, Power Platform feature, or API they've worked with before
- Task involves a project folder that has prior chat history
- User references "what we did before" or "like last time"

**Search patterns by topic:**
| Topic | Search Pattern |
|-------|----------------|
| Field Service | `*field*service*`, `*work*order*` |
| Cases/Incidents | `*case*`, `*incident*`, `*transcript*` |
| Home Assistant | `*home*assistant*`, `*pi*5*` |
| Power Apps | `*powerapp*`, `*mcclaren*` |
| Authentication | `*auth*`, `*credential*`, `*pac*` |

## Copilot Working Method Guidelines

### Full File Generation (Preferred)

When creating new files, **generate the complete file in a single operation** rather than building iteratively:

- Ask for "create the complete file with all functions" rather than building piece by piece
- Include all imports, error handling, and main execution blocks in the initial request
- Specify expected functions/classes upfront: "create a Python script with functions: get_data(), transform_data(), save_results()"

**Example prompt pattern:**

```
Create a complete Python script that:
- Authenticates to Dataverse using client credentials
- Retrieves all work orders from the last 7 days
- Exports them to a CSV file
- Include error handling and logging
- Add a main() function with argument parsing
```

This avoids the 100+ incremental edit pattern seen in previous sessions.

### Validation and Testing Requirements

Always include validation/testing requirements in the **initial request**, not as follow-ups:

**Include in your prompts:**

1. **Run after creation**: "...then run the script to verify it works"
2. **Error scenarios**: "...handle and log authentication failures, missing data, and API rate limits"
3. **Test data**: "...test with case ID abc-123 or create a test case first"
4. **Validation checks**: "...validate the output format before saving"

**Example prompt pattern:**

```
Create a script to update work order statuses, then:
- Run it against a test work order (create one if needed)
- Show the before/after state
- Verify the change in Dataverse
```

This ensures scripts are working before the session ends, avoiding "it didn't work" follow-up sessions.

### Local Dev Server Preference

**Use Vite as the default local dev server** for all HTML/CSS/JS projects.

- Run `npm run dev` (which calls `vite`) instead of using Live Server or other extensions
- Vite provides CSS hot-injection, fast reload, and ES module support out of the box
- No config file needed for plain HTML projects — Vite auto-detects `index.html`

**Exception**: Projects with their own backend server (e.g. `contractor-portal-dataverse` with Express) should keep their existing server — Vite is only for static/frontend-only projects.

**Projects with Vite configured:**
| Project | Notes |
|---------|-------|
| `code-apps/` | React + TypeScript + Vite (already configured) |
| `contractor-portal/` | Plain HTML + Vite (added Feb 2026) |

### PowerShell Execution Preference

**Always create script files** rather than inline PowerShell commands with complex arguments:

**Avoid inline commands with complex arguments:**

```powershell
# DON'T - quote escaping issues are common
pac auth create --name "Profile" --clientSecret "abc`"123" --environment "https://org.crm4.dynamics.com"
```

**Create a .ps1 script file instead:**

```powershell
# DO - create script, then run it
.\scripts\Create-AuthProfile.ps1
```

**Reasons:**

- Eliminates quote escaping issues between Copilot, terminal, and PowerShell
- Scripts are debuggable, reusable, and version-controlled
- Complex JSON, multi-line strings, and special characters work reliably
- Consistent behavior across PowerShell 5.1 and 7.x

**When inline is acceptable:**

- Simple commands with no special characters: `Get-Process | Select-Object -First 5`
- Single-quoted strings with no variables: `Get-ChildItem -Filter '*.ps1'`

## Azure Cognitive Services - Enabling API Key Authentication

When managed environment policies block API key authentication (DisableLocalAuth = true), follow these steps:

### Solution: SecurityControl Tag Bypass

1. **Add the bypass tag first** (use REST API if PowerShell doesn't apply it):

    ```powershell
    $tags = @{ SecurityControl = "Ignore" }
    Set-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" -Tag $tags
    ```

    Or via REST API if the above doesn't work:

    ```powershell
    $body = @{ tags = @{ SecurityControl = "Ignore" } } | ConvertTo-Json
    Invoke-RestMethod -Uri $uri -Method Patch -Headers @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" } -Body $body
    ```

2. **Then disable local auth restriction**:

    ```powershell
    Set-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" -DisableLocalAuth $false
    ```

3. **Verify the change**:
    ```powershell
    Get-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" | Select-Object AccountName, Tags, DisableLocalAuth
    ```

### ⚠️ Important Warning

- The `SecurityControl = Ignore` tag bypass only works for **14 days**
- After 14 days, the managed environment policy will re-enforce `DisableLocalAuth = true`
- You must repeat this process every 14 days to maintain API key access
- This workaround was discovered via MCAPS support

### Affected Resources in This Workspace

- Translation Service: `mjglobaltranslate` in `MJ_Resources`
- OpenAI: `MJOpenAI2` in `MJ_OpenAi`
- Other Cognitive Services accounts may also need this treatment

## Dynamics 365 Environment

- **Tenant**: D365DemoTSCE63319057.onmicrosoft.com
- **Environment**: MJCC2024
- **URL**: https://org6cb3e9fb.crm4.dynamics.com
- **API Base**: https://org6cb3e9fb.crm4.dynamics.com/api/data/v9.2/

### Opening Records in Browser

To open a record in the Dynamics 365 UI:

```
https://org6cb3e9fb.crm4.dynamics.com/main.aspx?etn={entity}&id={guid}&pagetype=entityrecord
```

Example entities: `incident` (case), `contact`, `account`, `subject`

## Chrome Profiles

Use these Chrome profile directories when opening external URLs:

| Profile Directory | Name                     | Use For                      |
| ----------------- | ------------------------ | ---------------------------- |
| `Profile 2`       | Marcs CCaSS 24 25 Tenant | Dynamics 365, Power Platform |
| `Default`         | marcjones.co.uk          | Personal/other               |

### Opening URLs in Chrome with Profile

```powershell
Start-Process chrome.exe -ArgumentList "--profile-directory=`"Profile 2`"", "https://org6cb3e9fb.crm4.dynamics.com"
```

## Dynamics 365 Customer Service - Case Metadata Reference

Reference data for Cases (incident entity) in this Dynamics 365 environment.

### Case Origins (`caseorigincode`)

| Value     | Label    |
| --------- | -------- |
| 1         | Phone    |
| 2         | Email    |
| 3         | Web      |
| 2483      | Facebook |
| 3986      | Twitter  |
| 700610000 | IoT      |

### Priorities (`prioritycode`)

| Value | Label  |
| ----- | ------ |
| 1     | High   |
| 2     | Normal |
| 3     | Low    |

### Key Subjects (41 total in environment)

Common subjects used for case categorization:

- **Utilities**: Gas, Water, Electric (parent category)
- **Gas Leak (Household)**, **Gas Leak (Public)**
- **Water Leak (Household)**, **Water Leak (Public)**
- **No Heating Household (Boiler Problems)** - used for Field Service demos
- **Discoloured Water** - Brown Water, discolored water complaints
- **Power Loss (Single Household)**, **Power Loss (Multiple Households)**
- **Finance**: Late Payments, Missed Payments, Pensions
- **ITSM**: Laptop, Stolen and Replace Laptop
- **Building Development**: Carpets, Painting, Snagging, Repair
- **Default Subject** - migration placeholder

### Retrieving Case Metadata

Run the script to get current values:

```powershell
cd PowerPlatform
python src\powerplatform\get_case_metadata.py
```

## Dynamics 365 - Retrieving Conversation Transcripts

Omnichannel conversation transcripts are stored in annotations (notes) attached to `msdyn_transcript` records.

### Data Path

```
Case (incident)
  └── activitypointers (timeline)
        └── msdyn_ocliveworkitem (conversation)
              └── msdyn_transcript (transcript record)
                    └── annotation (contains base64-encoded transcript in documentbody)
```

### Step-by-Step Retrieval

1. **Get conversation from case timeline:**

    ```
    GET activitypointers?$filter=_regardingobjectid_value eq {case_id}
    ```

    Look for `activitytypecode = 'msdyn_ocliveworkitem'`

2. **Find transcript record:**
    - Query `msdyn_transcripts` and check `_msdyn_liveworkitemidid_value` (note: double "id")
    - Or filter annotations by `objecttypecode eq 'msdyn_transcript'`

3. **Get annotation with transcript content:**

    ```
    GET annotations?$filter=_objectid_value eq {transcript_id}
    ```

4. **Decode the transcript:**
    - Base64 decode `documentbody`
    - Parse outer JSON array
    - Parse `Content` field as nested JSON array of messages
    - Filter out `isControlMessage: true` entries
    - Each message has: `from.user.displayName`, `content`, `createdDateTime`

### Example Script

```powershell
cd PowerPlatform
python scripts\display_transcript.py
```

### Key Fields

- `msdyn_transcript._msdyn_liveworkitemidid_value` → links to conversation
- `annotation.documentbody` → base64 encoded transcript JSON
- `annotation.objecttypecode` → filter by `'msdyn_transcript'`

## Dataverse Email Activities — Sending Email + Timeline (Proven February 2026)

### Pattern: Create Email Activity + SendEmail Bound Action

**This is the correct approach for sending emails that appear on a contact/case timeline.** Proven working on 25 Feb 2026 — email delivered and appeared on Chris Walker's contact timeline immediately.

**Why this approach (not Outlook connector):**

- The Dataverse `email` entity inherits from `activitypointer` — creating a row in `emails` with `regardingobjectid` set **automatically** places it on that record's timeline. No separate "post to timeline" step needed.
- The `SendEmail` bound action triggers server-side sync to deliver the email via the sender's mailbox.
- Single source of truth — the email IS the timeline record. No sync gaps.

### Two-Step API Pattern

**Step 1: Create the email activity** — `POST /api/data/v9.2/emails`

```python
email_payload = {
    "subject": "Your subject line",
    "description": "<html><body><p>HTML email body</p></body></html>",
    "directioncode": True,  # True = Outgoing
    # Links to timeline of the regarding record
    "regardingobjectid_contact@odata.bind": f"/contacts({contact_id})",
    # For cases use: "regardingobjectid_incident@odata.bind": f"/incidents({case_id})"
    # Activity parties define From and To
    "email_activity_parties": [
        {
            "partyid_queue@odata.bind": f"/queues({queue_id})",
            "participationtypemask": 1,  # 1 = From/Sender
        },
        {
            "partyid_contact@odata.bind": f"/contacts({contact_id})",
            "participationtypemask": 2,  # 2 = To Recipient
        },
    ],
}
resp = client.post(f"{api_url}/emails", headers=headers, json=email_payload)
activity_id = resp.headers["OData-EntityId"].split("(")[-1].rstrip(")")
```

**Step 2: Send the email** — `POST /api/data/v9.2/emails({activityid})/Microsoft.Dynamics.CRM.SendEmail`

```python
send_resp = client.post(
    f"{api_url}/emails({activity_id})/Microsoft.Dynamics.CRM.SendEmail",
    headers=headers,
    json={"IssueSend": True},
)
```

### Activity Party Participation Masks

| Value | Role          |
| ----- | ------------- |
| 1     | From (Sender) |
| 2     | To Recipient  |
| 3     | CC            |
| 4     | BCC           |

### Party ID Bindings (polymorphic)

- Queue: `"partyid_queue@odata.bind": "/queues({guid})"`
- Contact: `"partyid_contact@odata.bind": "/contacts({guid})"`
- User: `"partyid_systemuser@odata.bind": "/systemusers({guid})"`
- Account: `"partyid_account@odata.bind": "/accounts({guid})"`

### Email Status Codes (`statuscode`)

| Value | Label        |
| ----- | ------------ |
| 1     | Draft        |
| 2     | Completed    |
| 3     | Sent         |
| 4     | Received     |
| 6     | Pending Send |
| 7     | Sending      |
| 8     | Failed       |

### Regarding Object Bindings (timeline target)

| Target     | Binding                                                                       |
| ---------- | ----------------------------------------------------------------------------- |
| Contact    | `"regardingobjectid_contact@odata.bind": "/contacts({guid})"`                 |
| Case       | `"regardingobjectid_incident@odata.bind": "/incidents({guid})"`               |
| Account    | `"regardingobjectid_account@odata.bind": "/accounts({guid})"`                 |
| Work Order | `"regardingobjectid_msdyn_workorder@odata.bind": "/msdyn_workorders({guid})"` |

### Timeline Behaviour

- Email appears on the **regarding record's** timeline immediately after Step 1 (as Draft)
- Email **also** appears on the **To contact's** timeline (as an activity party)
- After Step 2, status transitions: Draft → Pending Send → Sent (usually within seconds)

### Prerequisites

- **Server-side sync** must be enabled for the sender mailbox (queue or user) in D365: Advanced Settings → Email Configuration → Mailboxes. Outgoing Email = "Server-Side Synchronization", status = "Success".
- Without this, emails stay stuck in "Pending Send" forever.

### Known Sender in This Environment

| Entity | Name    | Email                                          | GUID                                   |
| ------ | ------- | ---------------------------------------------- | -------------------------------------- |
| Queue  | support | `support@D365DemoTSCE63319057.onmicrosoft.com` | `1891ce59-6560-ef11-bfe3-000d3a65cf07` |

### Power Automate Implementation

In Power Automate cloud flows, the same pattern uses:

1. **"Add a new row"** (Dataverse connector) → entity `emails` → set subject, description, regarding, activity parties
2. **"Perform a bound action"** (Dataverse connector) → entity `emails`, action `SendEmail`, record ID from step 1, parameter `IssueSend: true`

### Reference Script

Working test script: `scripts/send_test_email.py` — sends from support queue to a contact with full activity party setup.

## Dataverse Knowledge Articles

### Publishing Knowledge Articles via API

**Method**: Direct PATCH to update `statecode` and `statuscode`. There is no dedicated `PublishKnowledgeArticle` action.

```python
# Publish a knowledge article
client.patch(f"knowledgearticles({article_id})", {
    "statecode": 3,
    "statuscode": 7
})
```

### Knowledge Article Status Values

| statecode | State     | statuscode | Status Reason |
| --------- | --------- | ---------- | ------------- |
| 0         | Draft     | 1          | Proposed      |
| 0         | Draft     | 2          | Draft         |
| 0         | Draft     | 8          | Needs Review  |
| 1         | Approved  | 5          | Approved      |
| 2         | Scheduled | 6          | Scheduled     |
| 3         | Published | 7          | Published     |
| 4         | Expired   | 10         | Expired       |
| 5         | Archived  | 12         | Archived      |
| 6         | Discarded | 11         | Discarded     |

### Article Versions - Which to Publish?

**Publish only the LATEST version**, not the root article.

When you create a new version in Dynamics 365, it creates a separate record:

- **Root article** (`isrootarticle=True`): The original article
- **Revision** (`isrootarticle=False`): New version(s) created via "Update" in the UI

Key fields for identifying versions:
| Field | Description |
|-------|-------------|
| `isrootarticle` | True = original article |
| `islatestversion` | True = most recent version |
| `majorversionnumber.minorversionnumber` | Version number (e.g., 1.0) |
| `_rootarticleid_value` | Links revision to root |

**Query to find the latest version to publish:**

```python
params = {
    "$filter": "contains(title, 'Article Name') and islatestversion eq true",
    "$select": "knowledgearticleid,title,statecode,majorversionnumber,minorversionnumber"
}
```

**Important**: Publishing an older version does NOT make it visible in the UI if a newer revision exists. Always publish the latest.

### Creating Knowledge Articles via API

Entity set: `knowledgearticles`

**Key Fields:**
| Field | Description |
|-------|-------------|
| `title` | Article title |
| `description` | Short summary |
| `content` | HTML body content |
| `keywords` | Comma-separated search keywords |
| `statecode` | 0=Draft, 1=Approved, 2=Scheduled, 3=Published |
| `statuscode` | Status reason (varies by state) |

### ⚠️ CRITICAL: HTML Content Formatting

**Dataverse sanitizes `<style>` blocks** - they are stripped from Knowledge Article content.

❌ **Does NOT work:**

```html
<style>
    body {
        font-family: Arial;
    }
</style>
<p>Content here</p>
```

✅ **Works - use inline styles on each element:**

```html
<p
    style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"
>
    Content here
</p>
```

### Recommended Style Constants

```python
H1_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL_STYLE = 'style="margin: 0 0 15px 20px; padding: 0;"'
```

### Example: Creating a Draft Article

```python
payload = {
    "title": "My Article Title",
    "description": "Short description for search results",
    "keywords": "keyword1, keyword2, keyword3",
    "content": f'<p {P_STYLE}>Article content with inline styles...</p>'
}

response = client.post(f"{base}/api/data/{ver}/knowledgearticles", json=payload, headers=headers)
```

Articles are created as **Draft** by default (statecode=0, statuscode=1).

## Microsoft Dataverse MCP Server (Preview) — Official

### What Is It?

Microsoft's **official MCP server for Dataverse**, hosted by Microsoft — no local server to run. Configured in `.vscode/mcp.json` as an HTTP/SSE server pointing at the environment's `/api/mcp_preview` endpoint. Authenticates via interactive browser OAuth as the signed-in user.

- **Documentation**: https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-mcp-preview-tools
- **VS Code setup**: https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-mcp-vscode
- **Preview endpoint**: `https://org6cb3e9fb.crm4.dynamics.com/api/mcp_preview`
- **GA endpoint** (when available): `https://org6cb3e9fb.crm4.dynamics.com/api/mcp`
- **Enabled in**: Power Platform Admin Centre → Environments → MJCC2024 → Settings → Product → Features → Dataverse Model Context Protocol

### MCP Config (`.vscode/mcp.json`)

```json
"dataverse-mcp-preview": {
    "type": "http",
    "url": "https://org6cb3e9fb.crm4.dynamics.com/api/mcp_preview"
}
```

### Available Tools (11)

| Tool             | Description                                 |
| ---------------- | ------------------------------------------- |
| `list_tables`    | Lists all tables in the environment         |
| `describe_table` | Retrieves T-SQL schema of a table           |
| `read_query`     | Executes SELECT queries (T-SQL syntax)      |
| `create_record`  | Inserts a new row, returns GUID             |
| `update_record`  | Updates an existing row                     |
| `Delete Record`  | Deletes a row                               |
| `Create Table`   | Creates a new table with schema             |
| `Update Table`   | Modifies table schema/metadata              |
| `Delete Table`   | Deletes a table                             |
| `Search`         | Keyword search across records               |
| `Fetch`          | Retrieves full record by entity name and ID |

### When Copilot Should Use This (MANDATORY — Updated 25 Feb 2026)

**The official Dataverse MCP preview server is now the PRIMARY tool for all Dataverse interactions.** Use it first for everything. Only fall back to the custom Python MCP server or OData scripts when the preview server cannot do the job.

**Use the official MCP preview server for:**

- **All** Dataverse queries — contacts, cases, work orders, knowledge articles, any entity
- Schema discovery — `list_tables` + `describe_table` instead of guessing entity/field names or writing Python scripts
- Record lookups, keyword searches, data verification
- Creating/updating/deleting individual records
- Any ad-hoc Dataverse question during a session
- Checking field names before building Power App formulas (McLaren app, etc.)
- Verifying Field Service demo data exists and is correct
- Cross-checking what the ContactDemo web app or Contractor Portal should display

**Fall back to custom Python server / OData scripts ONLY for:**

- Automated bulk operations (Field Service demo setup scripts with 50+ records)
- Client-credentials flows (unattended/background processing)
- Custom business logic that wraps multiple sequential API calls
- Complex OData queries requiring `$expand`, `$apply`, or FetchXML
- When the preview server is not started or unavailable in the session

**On session start**, if any Dataverse work is expected, Copilot should remind Marc to start the MCP preview server if it's not already running.

### Key Differences from Custom MCP Server

| Aspect      | Custom Python Server                         | Official Microsoft MCP                              |
| ----------- | -------------------------------------------- | --------------------------------------------------- |
| Auth        | Client credentials (app reg + secret)        | User-delegated OAuth (browser sign-in)              |
| Query       | OData `$filter`/`$select`/`$expand`          | **T-SQL SELECT** — easier for Copilot               |
| Schema      | Must know entity/field names upfront         | Self-discovery via `list_tables` / `describe_table` |
| Scope       | Only coded endpoints (contacts, work orders) | **All tables** in the environment                   |
| Security    | App-level access                             | **User-context** — respects row-level security      |
| Maintenance | You maintain Python code + dependencies      | **Zero** — Microsoft-hosted                         |
| Search      | Not available                                | **Keyword search** across all records               |

### Authentication Flow

1. Open Command Palette → **MCP: List Servers** → Start `dataverse-mcp-preview`
2. VS Code opens browser → sign in as `admin@D365DemoTSCE63319057.onmicrosoft.com`
3. Tools become available in Agent mode (`Ctrl+Alt+I`)
4. Token auto-refreshes during the session

### Client Authorisation (Completed 25 Feb 2026)

The GitHub Copilot client app (`aebc6443-996d-45c2-90f0-388ff96faa56`) must be whitelisted in Power Platform Admin Centre:

1. **Admin Centre** → Manage → Environments → MJCC2024 → Settings → Product → Features
2. **Dataverse Model Context Protocol** → Both GA and Preview checkboxes enabled
3. **Advanced Settings** → Allowed MCP Clients → "Microsoft GitHub Copilot" → **Is Enabled = Yes**

Without this, the server returns a 403 error. This was configured on 25 Feb 2026 and is persistent.

### Billing Note

Calls from non-Copilot Studio clients (like GitHub Copilot in VS Code) are charged via **Copilot Credits**. Dynamics 365 Premium or M365 Copilot USL licences exempt Dynamics 365 data access from charges.

### Sample Agent Instructions (from Microsoft)

When using this MCP server, these instructions help Copilot use the tools correctly:

- Always call `list_tables` to get logical table names (don't guess)
- Always call `describe_table` to get column/attribute names before querying
- Review tool descriptions and restrictions before executing
- For `read_query`, only use supported SQL keywords per the tool description
- Think step by step: plan → tool call → verify result → next step

### ⚠️ CRITICAL: `read_query` 20-Record Hard Limit (Discovered 25 Feb 2026)

The `read_query` tool has a **hard-coded server-side limit of 20 records** per query. This is enforced by the Dataverse plugin class `McpExecuteSqlQueryOperation.AddOrEditTopClause` — it intercepts SQL and forces `TOP 20` regardless of what you specify. Requesting `TOP 100` (or any value > 20) returns:

```
System.InvalidOperationException: Max of 20 records can be fetched.
```

**There is NO admin setting, environment variable, or configuration to increase this limit.** Thoroughly researched across all official Microsoft Learn docs (MCP overview, config, preview tools, VS Code setup, FAQ, Copilot Studio) — none mention any override. The local proxy args (`--ConnectionUrl`, `--TenantId`, etc.) have no record limit parameter either.

**Why it exists**: Deliberate safety constraint — LLM context window sizing, prevents accidental full-table scans via conversational AI.

**Workarounds (use these instead):**

| Approach                                       | When to Use                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------------ |
| `GROUP BY` / `COUNT(*)` / `SUM()` aggregations | Analysing trends, distributions, totals — works over entire table        |
| Paginate with `WHERE` clauses                  | `WHERE createdon > '{last_value}'` to batch through records 20 at a time |
| `Fetch` tool                                   | Retrieve a full single record by entity name + GUID (no limit)           |
| `Search` tool                                  | Keyword search across records (relevance-ranked results)                 |
| Custom Python MCP server / direct OData        | Bulk retrieval — standard 5,000-record OData page limit                  |

**Copilot should automatically apply these workarounds** when a query would need more than 20 records. For data analysis tasks, prefer aggregations first, then paginated detail queries if needed.

**Status**: May change in a future GA release (service is still in preview as of Feb 2026). If a future session hits this limit, check if Microsoft has updated the cap before applying workarounds.

---

## Dataverse Field Service - Work Orders

### MCP Dataverse Server

The `mcp-dataverse-server` project provides Dataverse access via Python. Configuration is in `mcp-dataverse-server/.env`.

### Querying Work Orders via Python

```python
import httpx
import sys
import os

os.chdir(r'c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server')
sys.path.insert(0, 'src')

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

settings = load_settings()
token_provider = TokenProvider(
    tenant_id=settings.dataverse_tenant_id,
    client_id=settings.dataverse_client_id,
    client_secret=settings.dataverse_client_secret,
    resource=settings.dataverse_base_url
)

token = token_provider.get_access_token()
base_url = settings.dataverse_base_url
api_version = settings.dataverse_api_version

# Query last N work orders
url = f'{base_url}/api/data/{api_version}/msdyn_workorders?$select=msdyn_workorderid,msdyn_name,createdon,msdyn_systemstatus&$orderby=createdon desc&$top=5'

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers={'Authorization': f'Bearer {token}'})
    data = resp.json()
    for wo in data.get('value', []):
        print(wo)
```

### Work Order System Status Values (`msdyn_systemstatus`)

| Value     | Label       |
| --------- | ----------- |
| 690970000 | Unscheduled |
| 690970001 | Scheduled   |
| 690970002 | In Progress |
| 690970003 | Completed   |
| 690970004 | Posted      |
| 690970005 | Canceled    |

### Required Python Packages

Install in the workspace `.venv`:

```powershell
.\.venv\Scripts\pip.exe install msal httpx --only-binary :all:
```

### Key Dataverse Entities

- `msdyn_workorders` - Work orders
- `msdyn_workorderservicetasks` - Service tasks on work orders
- `msdyn_bookableresourcebookings` - Bookings/schedules
- `msdyn_workordertypes` - Work order types
- `bookableresources` - Technicians/resources
- `msdyn_incidenttypes` - Incident types (templates for work orders)
- `msdyn_servicetasktypes` - Service task type definitions
- `msdyn_incidenttypeservicetasks` - Links tasks to incident types
- `characteristics` - Skills and certifications
- `bookableresourcecharacteristics` - Assigns characteristics to resources

### Field Service Demo Project

The `field-service-mikeo` project provides a complete Field Service demo setup:

```bash
cd field-service-mikeo
pip install -e .
python setup_prison_demo.py
```

### Creating Field Service Data via API

**Work Order Type:**

```python
client.post("msdyn_workordertypes", {
    "msdyn_name": "Printer Installation",
    "msdyn_incidentrequired": True,
    "msdyn_taxable": False
})
```

**Service Task Type:**

```python
client.post("msdyn_servicetasktypes", {
    "msdyn_name": "Test Print & Validation",
    "msdyn_estimatedduration": 4,  # minutes
    "msdyn_description": "Print test page, verify quality"
})
```

**Incident Type (links to Work Order Type):**

```python
client.post("msdyn_incidenttypes", {
    "msdyn_name": "Printer Installation",
    "msdyn_estimatedduration": 30,
    "msdyn_description": "Install and configure network printer",
    "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({work_order_type_id})"
})
```

**Link Service Task to Incident Type:**

```python
client.post("msdyn_incidenttypeservicetasks", {
    "msdyn_name": "Step 1 - Check Equipment",
    "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incident_type_id})",
    "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({task_type_id})",
    "msdyn_lineorder": 1
})
```

**Characteristic (Skill/Certification):**

```python
# characteristictype: 1=Skill, 2=Certification
client.post("characteristics", {
    "name": "Network Cabling & Termination",
    "characteristictype": 1
})
```

**Assign Characteristic to Bookable Resource:**

```python
client.post("bookableresourcecharacteristics", {
    "Resource@odata.bind": f"/bookableresources({resource_id})",
    "Characteristic@odata.bind": f"/characteristics({char_id})"
})
```

### Finding Bookable Resources

```python
# Find by user name
params = {
    "$select": "bookableresourceid,name",
    "$expand": "UserId($select=fullname)"
}
result = client.get("bookableresources", params)
```

### Currency Handling (UK/GBP)

```python
# Get GBP currency ID for UK accounts
result = client.get("transactioncurrencies", {
    "$filter": "isocurrencycode eq 'GBP'",
    "$select": "transactioncurrencyid"
})
gbp_id = result["value"][0]["transactioncurrencyid"]

# Use in account creation
client.post("accounts", {
    "name": "Customer Name",
    "transactioncurrencyid@odata.bind": f"/transactioncurrencies({gbp_id})"
})
```

### OData Binding Patterns

When creating records with relationships, use `@odata.bind`:

```python
{
    "fieldname@odata.bind": "/entitysetname(guid)"
}
```

Examples:

- `"msdyn_workordertype@odata.bind": "/msdyn_workordertypes(abc-123)"`
- `"parentaccountid@odata.bind": "/accounts(def-456)"`
- `"transactioncurrencyid@odata.bind": "/transactioncurrencies(ghi-789)"`

## Dataverse Knowledge Articles

### Creating Knowledge Articles via API

Entity set: `knowledgearticles`

**Key Fields:**
| Field | Description |
|-------|-------------|
| `title` | Article title |
| `description` | Short summary |
| `content` | HTML body content |
| `keywords` | Comma-separated search keywords |
| `statecode` | 0=Draft, 1=Approved, 2=Scheduled, 3=Published |
| `statuscode` | Status reason (varies by state) |

### ⚠️ CRITICAL: HTML Content Formatting

**Dataverse sanitizes `<style>` blocks** - they are stripped from Knowledge Article content.

❌ **Does NOT work:**

```html
<style>
    body {
        font-family: Arial;
    }
</style>
<p>Content here</p>
```

✅ **Works - use inline styles on each element:**

```html
<p
    style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"
>
    Content here
</p>
```

### Recommended Style Constants

```python
H1_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL_STYLE = 'style="margin: 0 0 15px 20px; padding: 0;"'
```

### Example: Creating a Draft Article

```python
payload = {
    "title": "My Article Title",
    "description": "Short description for search results",
    "keywords": "keyword1, keyword2, keyword3",
    "content": f'<p {P_STYLE}>Article content with inline styles...</p>'
}

response = client.post(f"{base}/api/data/{ver}/knowledgearticles", json=payload, headers=headers)
```

Articles are created as **Draft** by default (statecode=0, statuscode=1).

## Home Assistant Setup

- **URL**: http://192.168.0.111:8123
- **Version**: 2026.1.3
- **Location**: Home (UK) - West Bromwich, B71

### Raspberry Pi 5 Host System

Home Assistant runs on a **Raspberry Pi 5** via Docker:

| Property    | Value                                 |
| ----------- | ------------------------------------- |
| Hostname    | `raspberrypi` (SSH alias: `pi5`)      |
| OS          | Debian GNU/Linux 12 (bookworm)        |
| Kernel      | Linux 6.6.51+rpt-rpi-2712 (arm64)     |
| RAM         | 8GB (7.9Gi total)                     |
| Storage     | 32GB SD card (29GB usable, ~55% used) |
| Network     | WiFi (wlan0) at 192.168.0.111         |
| Temperature | ~57°C typical                         |

### Docker Containers

| Container           | Image                                                   | Purpose                               |
| ------------------- | ------------------------------------------------------- | ------------------------------------- |
| **homeassistant**   | ghcr.io/home-assistant/home-assistant:stable            | Main HA instance                      |
| **matter-server**   | ghcr.io/home-assistant-libs/python-matter-server:stable | Matter/Thread bridge                  |
| **scrypted**        | ghcr.io/koush/scrypted:latest                           | Camera/HomeKit bridge                 |
| **homebridge**      | homebridge/homebridge:latest                            | HomeKit bridge for non-native devices |
| **changedetection** | ghcr.io/dgtlmoon/changedetection.io:latest              | Web page monitoring                   |
| **heimdall**        | linuxserver/heimdall:latest                             | Dashboard/launcher                    |
| **portainer**       | portainer/portainer-ce:latest                           | Docker management UI                  |
| **watchtower**      | containrrr/watchtower                                   | Auto-update containers                |

### Thread & Matter Setup

Marc uses **Apple HomeKit as the primary Thread controller**:

| Property         | Value                             |
| ---------------- | --------------------------------- |
| Thread Network   | `MyHome1541761114`                |
| Border Router    | Living Room (Apple TV or HomePod) |
| Border Router IP | 192.168.0.228                     |
| Thread Version   | 1.3.0                             |
| Extended PAN ID  | `452fc667f1034860`                |

**Workflow for adding Matter devices:**

1. Add device to **Apple Home first**
2. Test it works in Apple Home
3. Get pairing code from Apple Home (Settings → Device → Turn on Pairing Mode)
4. Add to Home Assistant using that pairing code

This uses Matter's **multi-admin** feature - devices respond to both Apple Home and Home Assistant simultaneously over the Apple Thread network.

**Note**: Amazon Echo also has a Thread network (`AMZN-Thread-3e63`) at 192.168.0.130, Thread 1.1.1 - Marc does not use it.

### Matter Node Inventory (from Matter Server)

Data file: `/data/<fabric_id>.json` inside the `matter-server` Docker container.

| Node | Device                      | Manufacturer   | Connection           |
| ---- | --------------------------- | -------------- | -------------------- |
| 1    | Smart Radiator Thermostat X | tado° GmbH     | Thread (Kitchen)     |
| 2    | Smart Wi-Fi Plug            | Tapo           | Wi-Fi (Office)       |
| 3    | Smart Radiator Thermostat X | tado° GmbH     | Thread (Living Room) |
| 4    | Smart Radiator Thermostat X | tado° GmbH     | Thread (Bedroom)     |
| 5    | BILRESA dual button         | IKEA of Sweden | Thread (Office)      |
| 7    | Presence Multi-Sensor FP300 | Aqara          | Thread (Office)      |

**FP300 Thread Connection (Node 7):**

- Thread Network: `MyHome1541761114`, Channel 25
- Role: Sleepy End Device (SED) — battery-powered, wakes periodically
- Parent Router: RLOC16 `0xB000` — **Apple TV border router** (direct, no intermediate router)
- RSSI: -26 dBm (excellent signal)
- TX/RX: ~1215 packets, 1 retry (very reliable)

**Querying Matter Thread diagnostics:**

- Matter attribute `0/53/` = Thread Network Diagnostics cluster
- Key fields: `0/53/0` (channel), `0/53/1` (role), `0/53/2` (network name), `0/53/4` (extended PAN ID), `0/53/7` (neighbor table with parent router and RSSI)

### Configured Integrations (35 total)

**Smart Home Devices:**

- `matter` - Matter/Thread devices (Tapo Smart Plug, Kitchen Thermostat)
- `hikvision_next` - Embedded Net DVR (4 cameras: 101, 201, 301, 401)
- `tesla_custom` - Tesla Model Y (marcjones@microsoft.com)
- `thermopro` - TP393 temperature/humidity sensor
- `broadlink` - Living Room RM4Pro (IR/RF control)
- `esphome` - Home Assistant Voice NABU (unavailable)
- `apple_tv` - Living Room Apple TV
- `webostv` - LG OLED55CX5LB TV
- `xbox` - OzzyBrit2000 account

**Network & Infrastructure:**

- `bluetooth` - Raspberry Pi Bluetooth adapter
- `go2rtc` - WebRTC streaming for cameras
- `upnp` - UniFi NeXt-Gen Gateway
- `thread` - Thread network discovery

**AI & Voice:**

- `google_generative_ai_conversation` - Google Gemini AI
- `openai_conversation` - ChatGPT
- `google_translate` - TTS
- `cloud` - Home Assistant Cloud (Nabu Casa)

**Notifications:**

- `pushover` - Push notifications
- `mobile_app` - Marc's iPhone 15, Marc's iPad

**Utilities:**

- `hacs` - Home Assistant Community Store
- `backup` - Automatic backups
- `met` - Weather (Met Office)
- `shopping_list` - Shopping list

### Key Entities (209 total)

**Cameras (4):**

- `camera.dvr_204q_m10420250308ccwrfx3431707wcvu_101` - Camera 01
- `camera.dvr_204q_m10420250308ccwrfx3431707wcvu_201` - Camera 02
- `camera.dvr_204q_m10420250308ccwrfx3431707wcvu_301` - Camera 03
- `camera.dvr_204q_m10420250308ccwrfx3431707wcvu_401` - Camera 04

**Climate:**

- `climate.smart_radiator_thermostat_x` - Kitchen (Matter TRV)
- `climate.tesla_hvac_climate_system` - Tesla HVAC

**Switches:**

- `switch.smart_wi_fi_plug` - Office Tapo Smart Plug (Matter)
- `switch.tesla_sentry_mode`, `switch.tesla_polling`, etc.

**Sensors:**

- `sensor.smart_radiator_thermostat_x_temperature` - Kitchen temp
- `sensor.tp393_023e_temperature` - ThermoPro sensor
- `sensor.tesla_battery`, `sensor.tesla_range` - Tesla stats
- `sensor.smart_wi_fi_plug_power` - Plug power monitoring

**Media Players:**

- `media_player.living_room_apple_tv`
- `media_player.lg_webos_tv_oled55cx5lb_2`

**Device Trackers:**

- `device_tracker.marcs_iphone_15` - Marc's iPhone
- `device_tracker.marcs_ipad` - Marc's iPad
- `device_tracker.tesla_location_tracker` - Tesla

### Automations (10)

| Automation                                             | Purpose                                            |
| ------------------------------------------------------ | -------------------------------------------------- |
| `office_tapo_plug_weekday_morning_on_07_00`            | Turn on plug at 7am weekdays                       |
| `office_tapo_plug_weekday_18_30_off_with_notification` | Turn off plug at 6:30pm with Pushover notification |
| `tapo_plug_6pm_off_warning_at_17_55_weekdays`          | Warning 5 mins before shutoff                      |
| `tapo_plug_handle_mobile_cancel_tonight_button`        | Handle cancel button from notification             |
| `tapo_plug_reset_cancel_flag_18_30_daily`              | Reset cancel flag daily                            |
| `tapo_plug_weekday_6pm_off_unless_cancelled`           | Earlier 6pm off variant                            |
| `tapo_plug_weekday_morning_on_07_30`                   | Earlier 7:30am variant                             |
| `navigate_tesla_to_tutoring_fri_16_15_if_home`         | Navigate Tesla to tutoring on Fridays              |
| `tesla_tyre_pressure_alert_on_wake`                    | Alert for low tyre pressure                        |

### Scripts (4)

- `script.navigate_tesla_to_ets_tutoring` - Navigate Tesla to tutoring location
- `script.prepare_the_tesla` - Pre-condition Tesla
- `script.open_netflix_on_apple_tv` - Launch Netflix on Apple TV
- `script.1757004053790` - Open EE TV on Apple TV

### Dashboards

- **CCTV** - Original camera dashboard
- **CCTV2** - WebRTC camera dashboard (camera_view: live)
- **Marcs House** - General home dashboard
- **Energy** - Energy monitoring
- **Networking** - Network status
- **FP300** - Office presence sensor monitoring (occupancy, temp, humidity, lux, 48h history graphs, false positive detection via occupancy-vs-light overlay)

### Energy Monitoring

Octopus Energy integration via template sensors:

- `sensor.octopus_intelligent_go_price` - Current electricity price
- `binary_sensor.octopus_off_peak` - Off-peak period indicator
- Living Room Plug cost tracking (daily/weekly/monthly/yearly)

### External IP & Network

- **External IP**: 86.175.227.96 (via UniFi Gateway)
- **Router**: UniFi NeXt-Gen Gateway

## Power Apps Source Code Structure (Official Microsoft Documentation)

Reference: Microsoft Learn - authoritative source for Power Apps structure in VS Code.

### Canvas Apps – YAML / Power Fx Source Format

**Official documentation**: https://learn.microsoft.com/power-apps/maker/canvas-apps/power-apps-yaml

#### Documented Structure

- `Src/App.pa.yaml` – app-level definition
- `Src/<ScreenName>.pa.yaml` – one file per screen
- Assets, connections, and metadata separated clearly

#### Key Points (per Microsoft)

- Only files under `Src` are intended for source control
- JSON files inside `.msapp` are **not stable** and **not supported** for editing
- Extract using **Power Platform CLI** (PAC)

### Power Apps Code Apps – Pro-Code Model

**Official documentation**:

- https://learn.microsoft.com/power-apps/developer/code-apps/overview
- https://learn.microsoft.com/power-apps/developer/code-apps/

#### What's Documented

- VS Code as the **primary IDE**
- Standard web app structure (React, TypeScript)
- Power Platform CLI integration
- Deployment and ALM model

**100% safe for**: AI code assistants, linting, refactoring, CI/CD pipelines

### AI Assistant Usage Guidelines (Claude/Copilot)

#### Safe Uses ✅

- Feeding `*.pa.yaml` Canvas App source (read-only analysis, review, explanation)
- Code Apps React/TypeScript source
- Explaining Power Fx
- Refactoring suggestions
- Code review
- Documentation generation

#### Avoid ⚠️

- Blind auto-rewrite of Canvas YAML
- Treating YAML as a fully supported declarative DSL
- Canvas App YAML schema is **in active development** and not guaranteed stable

### Summary for Customer/RFP Responses

> Microsoft provides official, public documentation for the source code structure of Power Apps.
>
> For Canvas Apps, Microsoft documents the YAML-based source format (`*.pa.yaml`) used to represent screens, controls and Power Fx logic, which can be extracted and managed using the Power Platform CLI and edited in tools such as Visual Studio Code. This format is intended for source control and review, although Microsoft notes the schema is evolving.
>
> For pro-code scenarios, Microsoft supports Power Apps Code Apps, which are developed directly in Visual Studio Code using standard web technologies (React, TypeScript) and are fully compatible with modern AI-assisted development workflows.
>
> All of the above is covered by official Microsoft Learn documentation.

## VS Code Environment Setup (February 2026)

### Installed Extensions (45 total)

Categorised list of all extensions after the environment health review:

**Power Platform / Dynamics 365 / Dataverse:**

- `microsoft-isvexptools.powerplatform-vscode` — Power Platform Tools (PAC CLI, solutions, PCF)
- `danish-naglekar.dataverse-devtools` — Dataverse entity/metadata tooling
- `danish-naglekar.pcf-builder` — PCF control scaffolding and build

**Azure:**

- `ms-azuretools.vscode-azurefunctions` — Azure Functions local dev and deploy
- `ms-azuretools.vscode-azurelogicapps` — Logic Apps Standard
- `ms-azuretools.vscode-logicapps` — Logic Apps Consumption
- `ms-azuretools.vscode-azureresourcegroups` — Azure resource browser
- `ms-azuretools.vscode-bicep` — Bicep IaC language support
- `ms-azuretools.vscode-docker` — Docker/Compose management
- `ms-vscode.azure-account` — Azure sign-in
- `ms-vscode.azurecli` — Azure CLI IntelliSense
- `azurite.azurite` — Local Azure Storage emulator
- `bencoleman.armview` — Visual ARM template viewer

**Languages / Runtimes:**

- `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.debugpy`, `ms-python.vscode-python-envs`
- `ms-vscode.powershell`
- `ms-dotnettools.csdevkit`, `ms-dotnettools.csharp`, `ms-dotnettools.vscode-dotnet-runtime`

**Code Quality & Formatting:**

- `dbaeumer.vscode-eslint` — JavaScript/TypeScript linting
- `esbenp.prettier-vscode` — Multi-language formatter
- `charliermarsh.ruff` — Python linting/formatting (replaces flake8/black/isort)
- `redhat.vscode-yaml` — YAML IntelliSense (`.pa.yaml`, Azure Pipelines, HA config)
- `davidanson.vscode-markdownlint` — Markdown linting
- `editorconfig.editorconfig` — `.editorconfig` support

**Git:**

- `eamodio.gitlens` — Git blame, history, AI commit messages
- `mhutchie.git-graph` — Visual branch/merge graph

**Spell Checking (en-GB):**

- `streetsidesoftware.code-spell-checker` — Base spell checker
- `streetsidesoftware.code-spell-checker-british-english` — British English dictionary

**API Testing:**

- `humao.rest-client` — `.http` file runner (source-controllable)
- `rangav.vscode-thunder-client` — GUI API client

**Productivity:**

- `gruntfuggly.todo-tree` — TODO/FIXME aggregation
- `usernamehw.errorlens` — Inline error/warning display
- `ms-sarifvscode.sarif-viewer` — SARIF security results viewer
- `njpwerner.autodocstring` — Python docstring generator
- `specstory.specstory-vscode` — Copilot chat history persistence

**Remote / SSH:**

- `ms-vscode-remote.remote-ssh`, `ms-vscode-remote.remote-ssh-edit`, `ms-vscode.remote-explorer`

**Home Assistant:**

- `keesschollaart.vscode-home-assistant`, `rickykleinhempel.homeassistant-mcp`

**AI:**

- `github.copilot-chat`

### Key Settings Decisions

| Setting                    | Value                        | Why                                       |
| -------------------------- | ---------------------------- | ----------------------------------------- |
| `cSpell.language`          | `"en,en-GB"`                 | British English spell checking            |
| `editor.formatOnSave`      | `true`                       | Auto-format all files on save             |
| `[python]` formatter       | `charliermarsh.ruff`         | Modern all-in-one Python linter/formatter |
| `[yaml]` formatter         | `redhat.vscode-yaml`         | Validates `.pa.yaml` Power Apps source    |
| `[bicep]` formatter        | `ms-azuretools.vscode-bicep` | Azure IaC formatting                      |
| `telemetry.telemetryLevel` | `"error"`                    | Reduced telemetry                         |
| `git.autofetch`            | `true`                       | Keep local branches up to date            |
| Markdown `formatOnSave`    | `false`                      | Prevents unwanted markdown reformatting   |

### Configuration Files Created

- `.editorconfig` — consistent formatting rules (indent sizes per file type)
- `.vscode/settings.json` — workspace-level spell checker ignore paths, project-specific dictionary words, Ruff lint config, search exclusions
- `logicapps-development.code-workspace` — 34 categorised extension recommendations
- `scripts/Update-UserSettings.ps1` — reusable script to merge new settings into User settings.json safely

### User settings.json backup

Backup created at: `%APPDATA%\Code\User\settings.json.backup-20260219-123747`

## Official Microsoft Documentation & Learning Links

### Power Platform & Dynamics 365

| Resource                         | URL                                                                                             | What you'll find                                                             |
| -------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Power Platform CLI               | https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction                     | PAC CLI setup, authentication, solution export/import/deploy                 |
| Power Platform ALM               | https://learn.microsoft.com/en-us/power-platform/alm/                                           | Application lifecycle management, environments, solution layering, pipelines |
| Power Apps Developer             | https://learn.microsoft.com/en-us/power-apps/developer/                                         | Canvas/model-driven app development, custom connectors, code components      |
| PCF Controls                     | https://learn.microsoft.com/en-us/power-apps/developer/component-framework/overview             | Building Power Apps Component Framework controls in TypeScript               |
| Dataverse Developer              | https://learn.microsoft.com/en-us/power-apps/developer/data-platform/                           | Web API, plug-ins, entities, metadata, OData queries                         |
| Dynamics 365 Field Service Dev   | https://learn.microsoft.com/en-us/dynamics365/field-service/developer/                          | Field Service APIs, work orders, scheduling, customisation                   |
| Power Platform VS Code Extension | https://learn.microsoft.com/en-us/power-platform/developer/unified-experience/vs-code-extension | Official docs for Power Platform Tools extension                             |
| Power Apps YAML Source           | https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml                  | Canvas App `.pa.yaml` source format reference                                |
| Power Apps Code Apps             | https://learn.microsoft.com/en-us/power-apps/developer/code-apps/overview                       | Pro-code Power Apps using React/TypeScript in VS Code                        |

### Azure & Infrastructure as Code

| Resource                      | URL                                                                                                  | What you'll find                                     |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Azure Tools for VS Code       | https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack                 | Azure extension pack overview                        |
| Bicep Documentation           | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/                                | Bicep syntax, modules, deployment, ARM migration     |
| ARM Template Reference        | https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/                            | ARM JSON template authoring and deployment           |
| Logic Apps Consumption        | https://learn.microsoft.com/en-us/azure/logic-apps/quickstart-create-first-logic-app-workflow        | Logic Apps workflow design and deployment            |
| Logic Apps Standard (VS Code) | https://learn.microsoft.com/en-us/azure/logic-apps/create-single-tenant-workflows-visual-studio-code | Standard Logic Apps development in VS Code           |
| Azure Functions (VS Code)     | https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code                    | Functions development and local debugging in VS Code |

### VS Code Configuration

| Resource                  | URL                                                                           | What you'll find                                 |
| ------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------ |
| User & Workspace Settings | https://code.visualstudio.com/docs/getstarted/settings                        | How settings cascade (User → Workspace → Folder) |
| Multi-root Workspaces     | https://code.visualstudio.com/docs/editor/multi-root-workspaces               | Best practices for `.code-workspace` setups      |
| EditorConfig in VS Code   | https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig | How `.editorconfig` integrates with VS Code      |

## Dataverse / Field Service Scripting Best Practices

### Phase-Based Approach (MANDATORY for multi-entity setup)

**NEVER create one large monolithic setup script.** Instead, break into small per-phase scripts that each:

1. Create one category of entities (e.g. knowledge articles, characteristics, work order types)
2. Validate every record was created successfully
3. Save output GUIDs to a JSON state file (e.g. `state/phase3_work_order_types.json`)
4. Halt on any failure before proceeding

Each subsequent phase loads the state files from earlier phases to get the GUIDs it needs.

**Pattern**: `field-service-wessex/scripts/phase1_*.py` through `phase8_*.py` + `helpers.py`

### Entity Creation Order (Field Service)

When scaffolding a new Field Service demo, create entities in this exact dependency order:

1. **Knowledge Articles** — independent, no FK dependencies
2. **Characteristics** (Skills & Certifications) — link to bookable resource
3. **Work Order Types** — independent
4. **Service Task Types** — independent
5. **Incident Types** — depend on Work Order Types; then link Service Tasks via `msdyn_incidenttypeservicetasks`
6. **Products** — depend on Unit Groups / UoM
7. **Lookup existing records** (accounts, contacts) — just query, don't create
8. **Work Orders** — depend on everything above

### Critical Timing: Service Task Auto-Population

**Dataverse auto-populates work order service tasks from incident types ASYNCHRONOUSLY.**

When you create a work order with `msdyn_primaryincidenttype@odata.bind`, the service tasks from the incident type are copied to the work order **in the background**. This can take **30-60 seconds**.

**Always wait at least 60 seconds** before validating that work order service tasks were populated. Without this wait, task counts will appear as 0 even though the incident type has tasks correctly configured.

```python
# In Phase 8 (work orders), after creating all work orders:
import time
print("Waiting 60s for Dataverse to auto-populate service tasks...")
time.sleep(60)
# THEN validate task counts
```

### State File Pattern

Each phase saves its output to `state/<phase_name>.json`:

```python
# Saving: {"Entity Name": "guid", ...}
save_state("phase3_work_order_types", {"Water Leak Repair": "abc-123", ...})

# Loading in a later phase:
wot_ids = load_state("phase3_work_order_types")
wot_id = wot_ids["Water Leak Repair"]
```

### Key Learnings from field-service-wessex Demo

- **No customer branding**: Use fictitious names (e.g. "Contoso Utilities") — never the actual prospect's name
- **find_or_create()**: Always search by name before creating to make scripts idempotent/re-runnable
- **Knowledge article M:N linking**: `knowledgearticles({art_id})/msdyn_msdyn_workorder_knowledgearticle/$ref` with body `{"@odata.id": "{api_url}/msdyn_workorders({wo_id})"}`
- **Priority lookup**: Query `msdyn_priorities` — values vary by environment (not hardcoded option sets)
- **Products need**: Unit Group → Unit of Measure → Product (3-step dependency)

## Power Apps Code Apps (Pro-Code) — Detailed Reference

### What Are Code Apps?

Power Apps Code Apps let developers bring Power Apps capabilities into custom web apps built in a code-first IDE (VS Code). Build with popular frameworks (React, Vue, etc.) while keeping full control over UI and logic, then deploy and run in Power Platform.

Key features:

- **Microsoft Entra authentication and authorisation** built in
- **Access to Power Platform data sources and 1,500+ connectors**, callable directly from JavaScript/TypeScript
- **Easy publishing and hosting** of line-of-business web apps in Power Platform
- **Managed Platform policies** (app sharing limits, Conditional Access, DLP, etc.)
- **Simplified deployment and ALM** via PAC CLI

### Architecture

Three layers:

| Layer               | Purpose                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------- |
| **Your code**       | React/TypeScript app built with Vite                                                          |
| **Power Apps SDK**  | `@microsoft/power-apps` npm package — provides APIs, generates models/services for connectors |
| **Power Apps Host** | Manages end-user auth, app loading, runtime hosting                                           |

Key files:

| File                | Purpose                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| `power.config.json` | Generated by SDK — metadata for Power Platform connections and publishing. Do NOT edit manually |
| `src/generated/`    | Auto-generated typed TypeScript models and services when data sources are added via PAC CLI     |
| `vite.config.ts`    | Vite config with `powerApps()` plugin from `@microsoft/power-apps-vite`                         |

### Prerequisites

- Node.js (LTS), Git, VS Code, Power Platform CLI (PAC)
- Code Apps must be **enabled** in Power Platform Admin Centre: Manage > Environments > Settings > Product > Features > Enable code apps
- End-users need **Power Apps Premium** licence

### Project Setup (from Official Template)

```bash
# Clone the official Microsoft Vite template
npx degit github:microsoft/PowerAppsCodeApps/templates/vite my-app
cd my-app
npm install

# Authenticate and select environment
pac auth create
pac env select --environment <env-id>

# Initialise the code app
pac code init --displayname "My App Name"

# Run locally
npm run dev

# Build and deploy
npm run build | pac code push
```

The workspace project is at: `code-apps/`

### Contact Code App (Published 2 March 2026)

Second Code App project at `contact-code-app/` — a Fluent UI v9 contact management app with Dataverse connectivity.

| Property           | Value                                                                                                           |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Project Folder** | `contact-code-app/`                                                                                             |
| **App ID**         | `69d080da-4ad0-4719-8698-d475b552fee2`                                                                          |
| **App URL**        | https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2 |
| **Environment**    | MJCC2024 (`08690526-047d-ed9d-ab35-4528a98c0f4f`)                                                               |
| **Stack**          | React 19 + TypeScript + Vite + Fluent UI v9 + `@microsoft/power-apps` SDK                                       |
| **Data Sources**   | Dataverse `contact` table (via `pac code add-data-source`)                                                      |
| **Skill Guide**    | `contact-code-app/skill.md` — comprehensive dev reference (990 lines)                                           |

**Solution:** `CodeApps` (unmanaged) — Dataverse name: `mj_contactcodeapp_41e50`. Always deploy with `pac code push --solutionName CodeApps`

**Deploy command:** `cd contact-code-app && npm run deploy` (runs `npm run build && pac code push --solutionName CodeApps`)

**First-publish note:** On the first `pac code push` when `appId` is `null`, PAC creates a new app and automatically updates `power.config.json` with the assigned `appId`. A transient `CodePushMakeSolutionAwareErrorMessage` may appear on first push — it retries automatically and succeeds.

**CRITICAL — Solution association (learned 2 March 2026):** The `--solutionName` flag does **not** retroactively add an existing app to a solution. If the first push was done without `--solutionName`, subsequent pushes with it silently succeed but don't actually add the component. `pac solution add-solution-component` also fails because Code Apps are not stored in the `canvasapp` entity. **Fix:** Add via Power Apps maker portal UI → Solutions → Add existing → App → Code app. Always specify `--solutionName` on the **very first** push to avoid this.

### Key npm Packages

| Package                      | Type          | Purpose                                                       |
| ---------------------------- | ------------- | ------------------------------------------------------------- |
| `@microsoft/power-apps`      | dependency    | Power Apps SDK — runtime APIs, connector models/services      |
| `@microsoft/power-apps-vite` | devDependency | Vite plugin (`powerApps()`) for local dev with Power Platform |
| `react` + `react-dom`        | dependency    | UI framework (v19+)                                           |
| `vite`                       | devDependency | Build tool with HMR                                           |
| `typescript`                 | devDependency | Type checking                                                 |

### Connecting to Data Sources

#### Dataverse (First-Class Support)

```powershell
pac code add-data-source -a dataverse -t <table-logical-name>
# Example: pac code add-data-source -a dataverse -t account
```

Auto-generates `AccountsModel.ts` and `AccountsService.ts` in `src/generated/`.

```typescript
import { AccountsService } from "./generated/services/AccountsService";
import type { Accounts } from "./generated/models/AccountsModel";

// CRUD operations
await AccountsService.getAll({
    select: ["name"],
    filter: "statecode eq 0",
    top: 50,
});
await AccountsService.get(accountId);
await AccountsService.create({ name: "New" } as Omit<Accounts, "accountid">);
await AccountsService.update(accountId, { name: "Updated" });
await AccountsService.delete(accountId);
```

**Supported**: Create, Retrieve, RetrieveMultiple, Update, Delete, Filter, Sort, Top, Paging
**Not yet supported**: Polymorphic lookups, Dataverse actions/functions, FetchXML, alternate keys

#### Connectors (1,500+ available)

```powershell
# List available connections
pac connection list

# Non-tabular (e.g., Office 365 Users)
pac code add-data-source -a "shared_office365users" -c "<connectionId>"

# Tabular (e.g., SQL)
pac code add-data-source -a "shared_sql" -c "<connectionId>" -t "[dbo].[TableName]" -d "server.db.net,dbname"

# Discover datasets/tables
pac code list-datasets -a <apiId> -c <connectionId>
pac code list-tables -a <apiId> -c <connectionId> -d <datasetName>

# Delete a data source (no refresh command exists — delete and re-add instead)
pac code delete-data-source -a "shared_sql" -ds "TableName"
```

**Important**: Connections must be created first at make.powerapps.com > Connections. You cannot create connections via PAC CLI (yet).

#### Connection References (for ALM portability)

```powershell
pac code add-data-source -a <apiName> -cr <connectionReferenceLogicalName> -s <solutionID>
```

### Getting Context Data at Runtime

```typescript
import { getContext } from "@microsoft/power-apps/app";

const ctx = await getContext();
ctx.app.appId; // App ID
ctx.app.environmentId; // Environment ID
ctx.app.queryParams; // URL query parameters
ctx.user.fullName; // User's full name
ctx.user.objectId; // User's Entra object ID
ctx.user.tenantId; // Tenant ID
ctx.user.userPrincipalName; // UPN
ctx.host.sessionId; // Session ID (changes each app open)
```

### ALM (Application Lifecycle Management)

```powershell
# Push to preferred solution (default)
pac code push

# Push to a specific solution
pac code push --solutionName <solutionName>
```

Add to solution in UI: Power Apps > Solutions > Add existing > App > Code app.
Use **Power Platform Pipelines** for Dev → Test → Prod deployment.

**ALM limitations**: No solution packager support, no source code integration.

### System Configuration Notes

- Published code is hosted on a publicly accessible endpoint — **never store sensitive data in app code**
- Hide Power Apps header: append `?hideNavBar=true` to the app URL
- Since December 2025, Chrome/Edge block localhost requests from public origins — users may need to grant Local Network Access permission during development

### Current Limitations (as of February 2026)

- No Power Platform Git integration
- Not supported in Power Apps mobile or Power Apps for Windows
- No Power BI data integration (PowerBIIntegration function)
- No SharePoint forms integration
- No solution packager support
- No Storage SAS IP restrictions
- Dataverse: no polymorphic lookups, actions/functions, FetchXML, alternate keys

### Useful Links

| Resource                  | URL                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| Code Apps Overview        | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/overview                          |
| Quickstart                | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/create-an-app-from-scratch |
| Architecture              | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/architecture                      |
| Connect to Data           | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/connect-to-data            |
| Connect to Dataverse      | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/connect-to-dataverse       |
| Connect to Copilot Studio | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/connect-to-copilot-studio  |
| Connect to Azure SQL      | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/connect-to-azure-sql       |
| Get Context Data          | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/retrieve-context           |
| ALM                       | https://learn.microsoft.com/en-gb/power-apps/developer/code-apps/how-to/alm                        |
| GitHub Samples            | https://github.com/microsoft/PowerAppsCodeApps/tree/main/samples                                   |
| GitHub Templates          | https://github.com/microsoft/PowerAppsCodeApps/tree/main/templates                                 |
| GitHub Issues             | https://github.com/microsoft/PowerAppsCodeApps/issues                                              |

## Home Assistant Automation Creation via SSH

### Why SSH Instead of MCP Tools

The `mcp_homeassistant_automation_config` tool's `create` action is **broken** — it fails with a `content` array validation error regardless of input format. Use the SSH method below instead.

### Method: Append to automations.yaml via SSH + Docker

Home Assistant runs in Docker on the Raspberry Pi 5 (SSH alias: `pi5`). Automations are stored in `/config/automations.yaml` inside the `homeassistant` container.

**Steps:**

1. **Read existing automations** (to verify format):

    ```powershell
    ssh pi5 "docker exec homeassistant cat /config/automations.yaml"
    ```

2. **Append new automation YAML** via PowerShell here-string piped to SSH:

    ```powershell
    $yaml = @'
    - id: unique_automation_id
      alias: Human Readable Name
      description: What the automation does
      triggers:
      - trigger: state
        entity_id: event.some_entity
        attribute: event_type
        to: multi_press_1
      conditions: []
      actions:
      - action: tts.speak
        target:
          entity_id: tts.google_translate_en_com
        data:
          media_player_entity_id: media_player.home_assistant_voice_nabu_media_player
          message: Your message here
      mode: single
    '@
    $yaml | ssh pi5 "docker exec -i homeassistant tee -a /config/automations.yaml > /dev/null"
    ```

3. **Reload automations** (no restart needed):

    ```python
    ha_call_service(domain="automation", service="reload")
    ```

4. **Verify** with `ha_get_states(search="automation_name")`

### IKEA BILRESA Dual Button (Matter)

- **Entity IDs**: `event.bilresa_dual_button_button_1`, `event.bilresa_dual_button_button_2`
- **Event types**: `multi_press_1` (single), `multi_press_2` (double), `long_press`, `long_release`
- **Battery**: `sensor.bilresa_dual_button_battery` (AAA)
- **Connected via**: Matter (paired in Apple Home first, then shared to HA using pairing code)
- **Matter pairing**: Cannot be done via API — must use HA UI: Settings → Devices & Services → Add Integration → Matter → Commission using code

### NABU Voice TTS Pattern

To make the NABU voice speak:

```python
ha_call_service(
    domain="tts",
    service="speak",
    service_data={"media_player_entity_id": "media_player.home_assistant_voice_nabu_media_player", "message": "Your message"},
    target={"entity_id": "tts.google_translate_en_com"}
)
```

### NABU Voice Volume

Preferred volume: **0.7 (70%)** — set on 25 Feb 2026 after testing 50%, 80%, and 70%.

### NABU Voice Wake Words

Available: `no_wake_word`, `Hey Jarvis`, `Hey Mycroft`, `Okay Nabu` (no "Hey Nabu" option)
Currently set to: `Okay Nabu`

### HA Config File Locations (Pi 5 Docker)

| File                 | Container Path                          | Host Path                                                 |
| -------------------- | --------------------------------------- | --------------------------------------------------------- |
| `automations.yaml`   | `/config/automations.yaml`              | `/home/admin/homeassistant/automations.yaml`              |
| `configuration.yaml` | `/config/configuration.yaml`            | `/home/admin/homeassistant/configuration.yaml`            |
| Entity Registry      | `/config/.storage/core.entity_registry` | `/home/admin/homeassistant/.storage/core.entity_registry` |
| Restore State        | `/config/.storage/core.restore_state`   | `/home/admin/homeassistant/.storage/core.restore_state`   |

**To edit files while HA is running**: use `docker exec` (reads/writes inside container at `/config/`)
**To edit registry files**: stop HA first (`docker stop homeassistant`), edit at host path with `sudo`, then start again

### Cleaning Orphaned Automation Entities

When automations are removed from `automations.yaml`, their entity registry entries persist as `unavailable`. To fully remove:

1. `docker stop homeassistant`
2. Edit both `core.entity_registry` AND `core.restore_state` at the **host path** (`/home/admin/homeassistant/.storage/`) using `sudo python3`
3. `docker start homeassistant`

Editing via `docker exec` while HA is running gets overwritten on restart.

### TTS Template Messages — Critical YAML Formatting

**NEVER use `>-` (YAML folded block scalar) for TTS messages containing Jinja2 templates.** The templates won't render — the message is sent as literal text.

**Always use single-line double-quoted strings:**

```yaml
# CORRECT — templates render
message: "{% if now().hour < 12 %}Good morning{% else %}Good afternoon{% endif %}, power turned on."

# WRONG — templates sent as literal text
message: >-
  {% if now().hour < 12 %}Good morning{% else %}Good afternoon{% endif %},
  power turned on.
```

### Office Automation System (February 2026)

**Devices:**

- **Tapo Smart Plug** (`switch.smart_wi_fi_plug`) — controls office power (dock, monitors, etc.)
- **FP300 Presence Sensor** (Matter) — mmWave occupancy, temperature, humidity, illuminance
- **NABU Voice Module** — TTS announcements
- **IKEA Bilresa Dual Button** — currently disconnected (Matter battery device connectivity issues)

**FP300 Configuration:**

- Hold time: 30 seconds (`number.presence_multi_sensor_fp300_hold_time`)
- Sensitivity: standard (`select.presence_multi_sensor_fp300_sensitivity`)
- **Mounting**: Top corner of room, pointing down (repositioned 25 Feb 2026)
- Previous position caused 3.5-hour false positive on 24 Feb evening (18:38–22:12) due to reflections

**FP300 False Positive Analysis (24 Feb 2026):**

- Marc left the office at **16:38** (confirmed by user)
- Illuminance dropped from 340 → 10 lux by 16:55 (monitors off, lights off — proves empty room)
- Temperature peaked at 20.3°C at 17:26 then steadily declined all evening (no human heat source)
- Occupancy flickered on/off between 17:46–18:25 (intermittent false detections)
- Sensor went **unavailable** at 18:37 (physically being repositioned), recovered at 18:38
- Locked into continuous false "on" from 18:38–22:12 (3h 34m) despite room being empty, dark (1 lux), and cooling
- **Proof of false positive**: lux=1, temperature declining steadily: 19.3°C → 18.2°C → 17.4°C → 16.7°C → 16.0°C
- Evening Auto-Off automation never fired ("off for 10 min" condition never met due to false "on")
- Safety Cutoff at 20:00 saved the day — turned plug off regardless
- **Root cause**: Sensor position was causing reflections off monitors/walls

**FP300 Repositioning Test (25 Feb 2026):**

- Moved to ceiling corner, pointing down — ideal mmWave placement
- Baseline: occupancy=on (Marc present), temp=12.3°C, humidity=72%, lux=293, sensitivity=standard, hold=30s
- **Check back 26 Feb** to verify no false positives overnight when office is empty

**Statistics Sensor** (in `configuration.yaml`):

```yaml
sensor:
    - platform: statistics
      name: "Office Overnight Low Temperature"
      entity_id: sensor.presence_multi_sensor_fp300_temperature
      state_characteristic: value_min
      max_age:
          hours: 12
```

**Active Automations (6):**

| #   | ID                                | Name              | Trigger                  | Conditions                          | Actions                                            |
| --- | --------------------------------- | ----------------- | ------------------------ | ----------------------------------- | -------------------------------------------------- |
| 1   | `office_morning_arrival_power_on` | Morning Arrival   | Occupancy on for 3s      | Weekday, 07:30–10:00, plug off      | Plug on, TTS greeting + overnight low temp         |
| 2   | `office_evening_auto_off`         | Evening Auto-Off  | Occupancy off for 10 min | After 18:00, plug on                | TTS goodbye, Pushover, plug off                    |
| 3   | `office_hard_safety_cutoff_2000`  | Safety Cutoff     | Time 20:00               | Plug on                             | TTS warning, Pushover, plug off                    |
| 4   | `office_welcome_back`             | Welcome Back      | Occupancy on (from off)  | 09:00–18:00, plug on, absent 5+ min | TTS "Welcome back", 15-min cooldown                |
| 5   | `office_light_getting_low`        | Light Getting Low | Illuminance < 150 lux    | 09:00–18:00, occupied, plug on      | TTS "Light levels getting low", 60-min cooldown    |
| 6   | `office_low_light_warning`        | Low Light Warning | Illuminance < 50 lux     | 09:00–18:00, occupied, plug on      | TTS "Consider turning on a light", 60-min cooldown |

**Design Decisions:**

- Weekend presence does NOT auto-power-on (button only, currently disconnected)
- Cooldowns use `mode: single` + `delay` at end of actions
- 5-minute absence threshold for Welcome Back filters brief desk departures
- Two-tier light warnings: early (150 lux) and urgent (50 lux)
- All Pushover notifications on power-off events only (not morning arrival)

### IKEA Bilresa Dual Button — Known Issues

- Battery-powered sleepy Matter device — loses connection after Matter server restarts
- Requires re-pairing after battery replacement (factory reset → Apple Home → HA)
- **Do NOT restart the `matter-server` Docker container** unless necessary — sleepy devices won't reconnect
- Button automations removed from active config due to unreliable connectivity
- Entity IDs: `event.bilresa_dual_button_button_1`, `event.bilresa_dual_button_button_2`
- Event types: `multi_press_1` (single), `multi_press_2` (double), `long_press`, `long_release`

### Creating HA Dashboards via Storage Files

The HA REST API does **not** support creating new dashboards. To create a dashboard programmatically:

1. **Stop HA**: `ssh pi5 "docker stop homeassistant"`
2. **Edit `lovelace_dashboards`** at host path `/home/admin/homeassistant/.storage/lovelace_dashboards` — add entry to `data.items[]`
3. **Create dashboard config** at `/home/admin/homeassistant/.storage/lovelace.dashboard_<id>` — follow same JSON structure as existing dashboards
4. **Start HA**: `ssh pi5 "docker start homeassistant"` (takes ~30s to boot)

Script: `scripts/Create-FP300Dashboard.ps1` — reference example for creating dashboards.

**Editing dashboard cards while HA is running**: Use `docker cp` to copy a Python script into the container, edit the file at `/config/.storage/lovelace.dashboard_<id>`, then **restart HA** (`docker restart homeassistant`) — storage files are cached in memory and won't reload without a restart.

**CRITICAL: HA restarts disable automations.** After every `docker stop`/`docker start` or `docker restart` of the HA container, **check and re-enable all automations**. They can come back as `off` after a restart. Always run:

```python
ha_call_service(domain="automation", service="turn_on", target={"entity_id": [
    "automation.office_morning_arrival_power_on",
    "automation.office_evening_auto_off",
    "automation.office_hard_safety_cutoff_20_00",
    "automation.office_welcome_back",
    "automation.office_light_getting_low",
    "automation.office_low_light_warning"
]})
```

### Future Office Improvements (Planned)

- **Smart bulb** (multi-colour): 4000K neutral warm, 70-80% brightness for Teams video
- Automation: auto-on with morning arrival, auto-adjust brightness by lux
- Automation: shift to 3000K 50% after 5pm for evening warmth
- Bilresa button re-pairing when connectivity resolved

### Pi 5 Maintenance

**Log cleanup command** (safe to run periodically):

```powershell
ssh pi5 "sudo journalctl --vacuum-size=20M; sudo rm -f /var/log/wtmp.1"
```

**Backup cleanup** (keep only latest):

```powershell
ssh pi5 "ls -t /home/admin/homeassistant/backups/*.tar | tail -n +2 | xargs sudo rm -v"
```

---

## Shared from Grant Readings

> Learnings shared by colleague Grant Readings (greadings@microsoft.com) from his demo tenant development work. Reviewed February 2026.

### Dataverse Authentication via Az Module (PowerShell)

When `Microsoft.Xrm.Data.PowerShell` fails or `Connect-CrmOnline` doesn't work, use the Az module pattern. **Critical**: `Get-AzAccessToken` may return either a `SecureString` or plain text depending on the Az module version — always handle both formats:

```powershell
Import-Module Az.Accounts
$tokenResp = Get-AzAccessToken -ResourceUrl 'https://orgXXX.crm.dynamics.com'

# Handle both SecureString and plain text token formats
if ($tokenResp.Token -is [System.Security.SecureString]) {
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($tokenResp.Token)
    try { $token = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
} else {
    $token = $tokenResp.Token
}

$headers = @{
    Authorization      = "Bearer $token"
    'OData-MaxVersion' = '4.0'
    'OData-Version'    = '4.0'
    Accept             = 'application/json'
}
```

### PAC CLI Key Commands

```powershell
# Authenticate
pac auth create --url https://orgXXX.crm.dynamics.com

# Solution operations
pac solution export --name MySolution --path ./exports/MySolution.zip
pac solution import --path ./exports/MySolution.zip

# Canvas app operations (DEPRECATED — use Git Integration instead)
pac canvas unpack --msapp ./MyApp.msapp --sources ./src
pac canvas pack --sources ./src --msapp ./MyApp.msapp
```

### Solution Component Cleanup (SOAP API Fallback)

When orphaned solution components (e.g. deleted app modules still referenced) block solution import, the REST API cannot remove them. Use the **SOAP endpoint** as a fallback:

1. **Find orphaned components:**

    ```powershell
    $uri = "$baseUrl/solutioncomponents?`$filter=_solutionid_value eq $solutionId and componenttype eq 80"
    ```

2. **Remove via SOAP API:**
    ```powershell
    $soapBody = @"
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
      <s:Body>
        <Execute xmlns="http://schemas.microsoft.com/xrm/2011/Contracts/Services">
          <request i:type="b:RemoveSolutionComponentRequest" xmlns:b="http://schemas.microsoft.com/crm/2011/Contracts"
                   xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
            <b:Parameters xmlns:c="http://schemas.datacontract.org/2004/07/System.Collections.Generic">
              <b:KeyValuePairOfstringanyType>
                <c:key>ComponentId</c:key>
                <c:value i:type="d:guid" xmlns:d="http://schemas.microsoft.com/2003/10/Serialization/">$componentGuid</c:value>
              </b:KeyValuePairOfstringanyType>
              <b:KeyValuePairOfstringanyType>
                <c:key>ComponentType</c:key>
                <c:value i:type="d:int" xmlns:d="http://www.w3.org/2001/XMLSchema">80</c:value>
              </b:KeyValuePairOfstringanyType>
              <b:KeyValuePairOfstringanyType>
                <c:key>SolutionUniqueName</c:key>
                <c:value i:type="d:string" xmlns:d="http://www.w3.org/2001/XMLSchema">$solutionName</c:value>
              </b:KeyValuePairOfstringanyType>
            </b:Parameters>
            <b:RequestName>RemoveSolutionComponent</b:RequestName>
          </request>
        </Execute>
      </s:Body>
    </s:Envelope>
    "@
    ```

### Power Apps Canvas App Formula Patterns (Power Fx)

> Critical learnings from building canvas apps in Power Apps Studio. These patterns apply to any Dataverse-connected canvas app.

#### OnStart vs OnVisible

- **OnStart** runs once when the app loads (Play button). Use it for all variable initialisation.
- **OnVisible** does **NOT** fire on the first screen when pressing Play — only when navigating TO a screen.
- **Always put `Set()` calls for global variables in OnStart**, not OnVisible.

#### Column Name Disambiguation

When a Dataverse entity has multiple columns with the same display name, Power Apps requires disambiguation:

```
'Display Name (logicalname)'
```

**Example**: The Contact entity has two columns called "Contact":
| Logical Name | Type |
|---|---|
| `contactid` | Uniqueidentifier (PK) |
| `msevtmgt_contactid` | Lookup (Event Management) |

Power Apps requires: `'Contact (contactid)'` to reference the primary key.

#### Lookup Column Comparison (GUID-based)

Filter records by a lookup column using GUIDs, not records:

```
// WORKS — GUID to GUID comparison
Filter('Car Collections', Customer.'Contact (contactid)' = varContactId)

// FAILS — Record to Record comparison
Filter('Car Collections', Customer = varContact)
// Error: "Incompatible types for comparison. These types can't be compared: Record, Record."
```

**Fallback**: If GUID comparison silently returns no results, use a name-based lookup instead.

#### Choice/Picklist Column Formulas

**Single-select**: Auto-coerces to text when concatenated with `&`. No `.Value` needed:

```
"Driving Style: " & varPreference.'Driving Style'
// Result: "Driving Style: Track"
```

**Important**: `.Value` does NOT appear in IntelliSense for choice columns accessed via a variable. Do NOT use `varPreference.'Driving Style'.Value` — it won't compile.

**Multi-select**: Requires `Concat()` with `Value`:

```
"Music: " & Concat(varPreference.'Music Genre', Value, ", ")
// Result: "Music: Classical"
```

#### Copy-Paste Corruption Warning

**CRITICAL**: Copy-pasting formulas from a browser (including Copilot chat) into Power Apps Studio often introduces invisible Unicode characters that cause `"Unexpected characters"` errors. The formula looks correct but won't compile.

**Solution**: Always **TYPE formulas manually** in Power Apps Studio. If you get "Unexpected characters" on a formula that looks correct, delete it entirely and retype it character by character.

#### Entity Set Name Gotchas

Entity logical names and entity set names differ. Don't guess pluralisation — verify via API:

```powershell
# Verify entity set name
$attrs = Invoke-RestMethod -Uri "$base/EntityDefinitions(LogicalName='mcl_customerpreference')?`$select=EntitySetName" -Headers $h
```

Custom entities may use `es`, `s`, or other patterns unpredictably.

#### App.Theme Error Fix

If `App.Theme` shows error `"Name isn't valid. 'PowerAppsTheme' isn't recognized"`, clear the Theme property (leave it blank). This is a leftover from `.msapp` packing and is harmless.

#### Pre-Deployment Checklist for Canvas Apps

Before building formulas in Power Apps Studio, verify:

1. **Data exists** — Query Dataverse API to confirm sample data was loaded for ALL entities
2. **Column display names** — Use `EntityDefinitions/.../Attributes` API to get exact display names
3. **Disambiguation** — Check for duplicate display names on each entity that require `'Name (logicalname)'` syntax
4. **Lookup targets** — Verify lookup columns point to the expected entity
5. **Choice values** — Confirm choice/optionset integer values match what was deployed

### Power Apps `.pa.yaml` Source Code Schema (SchemaV3)

> Schema reference: https://go.microsoft.com/fwlink/?linkid=2299600

#### File Structure

- `Src/App.pa.yaml` — App-level properties (OnStart)
- `Src/[ScreenName].pa.yaml` — One file per screen
- `Src/_EditorState.pa.yaml` — Editor state (auto-generated)

#### Top-Level Keys

```yaml
# App.pa.yaml
App:
    Properties:
        OnStart: |-
            =Set(varFoo, "bar")

# ScreenName.pa.yaml — CRITICAL: use Screens: as top-level key
Screens:
    MyScreen:
        Properties:
            Fill: =RGBA(26, 26, 26, 1)
        Children:
            - MyLabel:
                  Control: Label@2.5.1
                  Properties:
                      Text: ="Hello"
```

**CRITICAL**: Screen files use `Screens:` as the top-level key, NOT the screen name directly. Do NOT use `Control: Screen` — screens don't have a Control property.

#### Control Syntax

```yaml
- ControlName:
      Control: ControlType@version # version is optional
      Variant: ManualLayout # or AutoLayout, optional
      Properties:
          X: =10
          Y: =20
      Children: # for containers
          - ChildControl: ...
```

**Control types with versions**: `Label@2.5.1`, `GroupContainer@1.4.0`, `Classic/Button@2.2.0`, `Image@4.2.0`

#### CRITICAL: Special Characters in Formulas

**Colons (`:`) and hash signs (`#`) are NEVER allowed in single-line formulas**, even inside quoted text strings. Always use YAML block scalar (`|`) form:

```yaml
# WRONG — colon in single-line breaks YAML parsing
Text: ="Address 1: City"

# CORRECT — use block scalar
Text: |
    ="Address 1: City"
```

This applies to ALL property values, not just `Text`.

#### GroupContainer Variants

| Variant        | Use                                                    |
| -------------- | ------------------------------------------------------ |
| `ManualLayout` | Absolute positioning with X, Y, Width, Height          |
| `AutoLayout`   | Flex-like layout with LayoutDirection, LayoutGap, etc. |

AutoLayout properties: `LayoutDirection`, `LayoutAlignItems`, `LayoutGap`, `LayoutMinHeight`, `LayoutMinWidth`, `PaddingTop/Bottom/Left/Right`

#### Z-Index Ordering

Children array order = ascending z-index. First child is at the bottom, last is on top.

#### Image Controls

Images must be uploaded through Power Apps Studio (Insert → Media → Upload). They **cannot** be added via Git.

#### Encoding Rules

- Files must be UTF-8 **without BOM** (byte order mark)
- PowerShell 5.1 `Set-Content -Encoding UTF8` adds a BOM — use `[System.Text.UTF8Encoding]::new($false)` instead:
    ```powershell
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($path, $content, $encoding)
    ```

#### Git Integration Workflow

1. **Environment → Git (Commit)**: Publish app first, then Solutions → Source Control → Commit
2. **Git → Environment (Pull)**: Edit `.pa.yaml` in VS Code, push to Azure DevOps, then Solutions → Source Control → Check for updates → Pull
3. **No auto-sync** — commits and pulls are always manual
4. **Azure DevOps only** — GitHub repos not supported (as of Feb 2026)
5. **Managed Environment required** — must be enabled in Power Platform Admin Centre
6. **`pac canvas pack/unpack` is DEPRECATED** — use Git Integration instead
7. **`pac solution pack --processCanvasApps`** does NOT compile `.pa.yaml` → `.msapp`

### HTML Dealer Portal — Node.js + Express + MSAL Pattern

> Reusable pattern for building single-page HTML web apps that read/write Dataverse data via a Node.js backend proxy. Secrets never reach the browser.

#### Project Structure

```
project/
  .env                     # Secrets (gitignored)
  .env.example             # Template for other developers
  package.json
  server.js                # Express app — validates env, mounts routes
  public/
    index.html             # Single-page HTML (served as static)
    css/styles.css
    js/app.js              # Frontend JS — calls /api/* endpoints
  src/
    dataverse-client.js    # MSAL token acquisition + OData fetch wrapper
    routes/api.js          # Express router — typed + generic entity endpoints
```

#### Dependencies

```json
{
    "dependencies": {
        "@azure/msal-node": "^2.16.0",
        "dotenv": "^16.4.7",
        "express": "^4.21.2"
    }
}
```

#### Dataverse Client (Node.js MSAL with Token Caching)

```javascript
const { ConfidentialClientApplication } = require("@azure/msal-node");

class DataverseClient {
    constructor({ baseUrl, tenantId, clientId, clientSecret }) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.apiUrl = `${this.baseUrl}/api/data/v9.2`;
        this.tokenCache = null;
        this.tokenExpiry = null;
        this.msalClient = new ConfidentialClientApplication({
            auth: {
                clientId,
                authority: `https://login.microsoftonline.com/${tenantId}`,
                clientSecret,
            },
        });
    }

    async getToken() {
        if (
            this.tokenCache &&
            this.tokenExpiry &&
            Date.now() < this.tokenExpiry - 300000
        ) {
            return this.tokenCache;
        }
        const result = await this.msalClient.acquireTokenByClientCredential({
            scopes: [`${this.baseUrl}/.default`],
        });
        this.tokenCache = result.accessToken;
        this.tokenExpiry = result.expiresOn
            ? result.expiresOn.getTime()
            : Date.now() + 3600000;
        return this.tokenCache;
    }

    async fetch(endpoint, options = {}) {
        const token = await this.getToken();
        const url = endpoint.startsWith("http")
            ? endpoint
            : `${this.apiUrl}/${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                Authorization: `Bearer ${token}`,
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                Accept: "application/json",
                "Content-Type": "application/json",
                Prefer: 'odata.include-annotations="*"',
                ...options.headers,
            },
        });
        if (!response.ok)
            throw Object.assign(new Error(`${response.status}`), {
                status: response.status,
                body: await response.text(),
            });
        if (response.status === 204) return null;
        return response.json();
    }

    async get(entity, query = "") {
        return this.fetch(`${entity}${query ? "?" + query : ""}`);
    }
    async getById(entity, id, q = "") {
        return this.fetch(`${entity}(${id})${q ? "?" + q : ""}`);
    }
    async create(entity, data) {
        return this.fetch(entity, {
            method: "POST",
            body: JSON.stringify(data),
        });
    }
    async update(entity, id, data) {
        return this.fetch(`${entity}(${id})`, {
            method: "PATCH",
            body: JSON.stringify(data),
        });
    }
    async delete(entity, id) {
        return this.fetch(`${entity}(${id})`, { method: "DELETE" });
    }
}
```

#### API Route Pattern

Key endpoints:

- `GET /api/health` → calls `WhoAmI()` to verify connection
- `GET /api/contacts?filter=...&select=...&top=10` → typed entity route
- `GET /api/data/:entity` → generic passthrough for any Dataverse entity
- `POST /api/data/:entity` → create record
- `PATCH /api/data/:entity/:id` → update record
- `DELETE /api/data/:entity/:id` → delete record

#### Tenant ID Discovery Trick

If you only know the tenant domain, resolve the GUID via OpenID config:

```
GET https://login.microsoftonline.com/{domain}/.well-known/openid-configuration
```

The `issuer` field contains the tenant GUID.

**Key takeaway**: Use Node.js + Express + MSAL as a backend proxy so HTML pages can read/write Dataverse without exposing secrets to the browser.

### Quick Reference — Grant Readings Key Learnings

1. **Az Module Token Handling**: `Get-AzAccessToken` may return `SecureString` — always handle both formats
2. **SOAP API Fallback**: Some Dataverse operations (removing orphaned solution components) require the SOAP endpoint when REST fails
3. **OnStart vs OnVisible**: OnVisible does NOT fire on the first screen — use OnStart for all variable initialisation
4. **Column Disambiguation**: When multiple columns share a display name, use `'Display Name (logicalname)'` syntax
5. **Choice Column Text**: Single-select Picklist columns auto-coerce to text with `&` — no `.Value` needed
6. **Multi-Select Columns**: Use `Concat(field, Value, ", ")` for multi-select choice columns
7. **Copy-Paste Corruption**: Browser-to-Power Apps paste introduces invisible characters — always TYPE formulas manually
8. **Entity Set Names**: Always verify via API — don't guess pluralisation of custom entity names
9. **App.Theme Error**: Clear the Theme property if `PowerAppsTheme` isn't recognised — harmless leftover
10. **PA YAML Colon Rule**: Colons (`:`) and hash signs (`#`) are NEVER allowed in single-line `.pa.yaml` formulas — use `|` block scalar
11. **PA YAML SchemaV3**: Screen files use `Screens:` top-level key, controls need `@version` suffix, no `Control: Screen`
12. **PA YAML Encoding**: Files must be UTF-8 without BOM — PowerShell 5.1 adds BOM by default
13. **Git Integration**: Azure DevOps only, requires Managed Environment, no auto-sync, `pac canvas pack/unpack` is deprecated
14. **Dataverse HTML Portal**: Use Node.js + Express + MSAL backend proxy — secrets stay server-side
15. **Tenant ID Discovery**: Resolve tenant GUID from domain via `/.well-known/openid-configuration`

## Power Apps Code Apps — D365 Embedding & CSP (Learned March 2026)

### Code Apps CAN Be Embedded in D365 — With CSP Configuration

**Updated 2 March 2026**: By default, Code Apps are hosted on `*.powerplatformusercontent.com` which sets:

```
Content-Security-Policy: frame-ancestors 'self' https://*.powerapps.com
```

This **blocks embedding inside D365** (`*.dynamics.com`) by default. The error:

```
Framing '...environment.api.powerplatformusercontent.com/' violates the following
Content Security Policy directive: "frame-ancestors 'self' https://*.powerapps.com"
```

### Fix: Configure Code App CSP via Power Platform API (Proven 2 March 2026)

The CSP `frame-ancestors` directive for Code Apps is **configurable** via the Power Platform REST API. The settings are NOT on the Dataverse organization entity — they are on the Power Platform Environment Management API.

**API Endpoint:** `https://api.powerplatform.com/environmentmanagement/environments/{envId}/settings?api-version=2022-03-01-preview`

**Settings (Code App specific):**

| Setting                          | Description                                                     |
| -------------------------------- | --------------------------------------------------------------- |
| `PowerApps_CSPEnabledCodeApps`   | Whether CSP is enforced for Code Apps (default: `true`)         |
| `PowerApps_CSPConfigCodeApps`    | JSON config for directives — custom values merge with defaults  |
| `PowerApps_CSPReportingEndpoint` | URL for CSP violation reports (shared with model-driven/canvas) |

**Authentication:** Requires a token for `https://api.powerplatform.com/` with delegated permissions. Azure CLI token (for Azure resources) does NOT work — returns 403 `InsufficientDelegatedPermissions`. Use the **Power Platform CLI client ID** (`9cee029c-6210-4654-90bb-17e6e9d36617`) with MSAL interactive browser flow.

**To add D365 to frame-ancestors:**

```python
import httpx, json, msal

# 1. Authenticate with PAC CLI client ID
app = msal.PublicClientApplication(
    "9cee029c-6210-4654-90bb-17e6e9d36617",
    authority="https://login.microsoftonline.com/996f568a-cc69-450a-b684-ae784069e679"
)
result = app.acquire_token_interactive(scopes=["https://api.powerplatform.com/.default"])
token = result["access_token"]

# 2. PATCH the CSP config (custom values MERGE with defaults)
env_id = "08690526-047d-ed9d-ab35-4528a98c0f4f"
url = f"https://api.powerplatform.com/environmentmanagement/environments/{env_id}/settings?api-version=2022-03-01-preview"
payload = {
    "PowerApps_CSPConfigCodeApps": json.dumps({
        "Frame-Ancestors": {"sources": [{"source": "https://*.dynamics.com"}]}
    }),
    "PowerApps_CSPEnabledCodeApps": True,
}
resp = httpx.patch(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload)
# Status 200 = success
```

**Resulting frame-ancestors:** `'self' https://*.powerapps.com https://*.dynamics.com`

**Docs:**

- Code App CSP: https://learn.microsoft.com/en-us/power-apps/developer/code-apps/how-to/content-security-policy
- General CSP: https://learn.microsoft.com/en-gb/power-platform/admin/content-security-policy
- Microsoft also provides PowerShell `Get-CodeAppContentSecurityPolicy` and `Set-CodeAppContentSecurityPolicy` helper functions in the docs

**Admin Centre UI:** Power Platform Admin Centre → Environments → MJCC2024 → Settings → Product → Privacy + Security → Content Security Policy → **App tab**. The "Configure directives" section allows adding custom `frame-ancestors` origins. If the UI doesn't show the directives section, use the REST API approach above.

**Current state in MJCC2024 (set 2 March 2026):**

- `PowerApps_CSPEnabledCodeApps`: `true`
- `PowerApps_CSPConfigCodeApps`: `{"Frame-Ancestors": {"sources": [{"source": "https://*.dynamics.com"}]}}`
- `PowerApps_CSPReportingEndpoint`: `null`

**Scripts:** `scripts/update_codeapp_csp.py` (update), `scripts/query_pp_csp.py` (read)

### App2 Tab — Code App IFrame on Contact Form (2 March 2026)

A second IFrame tab was added to test Code App embedding after the CSP fix:

| Setting             | Value                                                                                                                             |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Tab name**        | `tab_5`                                                                                                                           |
| **Tab label**       | App2                                                                                                                              |
| **IFrame ID**       | `IFRAME_CodeApp`                                                                                                                  |
| **URL**             | `https://apps.powerapps.com/play/e/08690526-047d-ed9d-ab35-4528a98c0f4f/app/69d080da-4ad0-4719-8698-d475b552fee2?hideNavBar=true` |
| **Pass Parameters** | `true`                                                                                                                            |
| **Security**        | `false`                                                                                                                           |
| **Scrolling**       | `auto`                                                                                                                            |
| **Border**          | `false`                                                                                                                           |

Script: `scripts/add_app2_tab.py` — idempotent (removes existing App2 tab before recreating).

### Alternative Approach: Azure Web App IFrame (Also Working)

If CSP config is not possible (e.g. managed environments with locked-down policies), recreate the same UI as a standalone HTML page on the Azure Web App and IFrame that instead.

**Architecture:**

```
D365 Contact Form → "App" Tab → IFrame
  → https://mj-webapps-demo-2026.azurewebsites.net/EnergyDashboard?id={guid}
    → /api/contact/:id (server-side MSAL → Dataverse OData)
    → HTML page renders fields + Chart.js charts client-side
```

**Key technical notes:**

- The `/EnergyDashboard` route on the Azure Web App serves a single HTML page
- Contact ID is passed via D365 IFrame "Pass Parameters" (`&id={guid}`)
- Server-side `/api/contact/:id` fetches from Dataverse using MSAL client-credentials
- Charts use Chart.js loaded via CDN (no npm dependency on the server)
- Uses `Prefer: odata.include-annotations="OData.Community.Display.V1.FormattedValue"` to get choice field display names

### Chart.js Sizing Inside D365 IFrames (Critical)

**Problem**: Inside a D365 IFrame, `window.innerHeight` returns an extremely large value because the IFrame has no fixed height constraint. CSS flex-based sizing (`flex: 1`, `max-height: 50%`, `calc()`) does NOT constrain Chart.js — it ignores CSS and sizes canvases based on the parent element's computed size.

**Solution**: Use JavaScript to calculate chart heights with a hard pixel cap:

```javascript
function sizeCharts() {
    var fields = document.querySelector(".fields-section");
    var fieldsH = fields.offsetHeight;
    var vh = Math.min(window.innerHeight, 700); // clamp viewport
    var available = vh - fieldsH - 60;
    var perChart = Math.max(100, Math.floor(available / 2));
    perChart = Math.min(perChart, 200); // HARD CAP — never taller than 200px

    // Set explicit pixel heights on containers AND canvas elements
    document.querySelectorAll(".chart-container").forEach(function (c) {
        c.style.height = perChart + "px";
    });
    document.querySelectorAll(".chart-container canvas").forEach(function (cv) {
        cv.setAttribute("height", perChart);
        cv.style.height = perChart + "px";
        cv.style.maxHeight = perChart + "px";
    });
}
```

**Call `sizeCharts()` BEFORE creating Chart.js instances**, not after. Also add `window.addEventListener('resize', sizeCharts)`.

### Alternative Approaches to D365 Form Integration

| Method                    | Works in IFrame? | Notes                                              |
| ------------------------- | ---------------- | -------------------------------------------------- |
| **Code App via Play URL** | ✅ Yes           | Requires CSP `frame-ancestors` update (see above)  |
| **Azure Web App IFrame**  | ✅ Yes           | No CSP changes needed — fallback approach          |
| **PCF Control (React)**   | ✅ Yes           | Native D365 control — best UX, more effort (~3-4h) |
| **D365 Web Resource**     | ✅ Yes           | Uses `Xrm.WebApi` — no external infra needed       |
| **Custom Page**           | ❌ No            | Canvas Apps only, not Code Apps                    |

### EnergyDashboard IFrame Configuration

| Setting                             | Value                                                            |
| ----------------------------------- | ---------------------------------------------------------------- |
| **IFrame ID**                       | `IFRAME_MJWebPage`                                               |
| **URL**                             | `https://mj-webapps-demo-2026.azurewebsites.net/EnergyDashboard` |
| **Pass Parameters**                 | `true`                                                           |
| **Security (restrict cross-frame)** | `false`                                                          |
| **Scrolling**                       | `no`                                                             |
| **Border**                          | `false`                                                          |
| **Form**                            | Contact for Utilities (Interactive)                              |
| **Tab**                             | App (`tab_4`)                                                    |
| **Form ID**                         | `b45b0a55-3d74-f011-b4cc-002248a0aee6`                           |

### Updating the IFrame URL

Script: `scripts/update_app_tab_iframe.py` — fetches formxml, updates the IFrame URL, PATCHes back, and publishes.

### Contacts with mj\_ Energy Data Populated

| Contact       | GUID                                   | Key fields                                              |
| ------------- | -------------------------------------- | ------------------------------------------------------- |
| Chris Walker  | `7fba73b9-2461-ef11-bfe2-002248a36d0e` | Worcester Bosch, EV Tariff, Complete HomeCare, EV owner |
| Andrew Palmer | `b1bf9a01-b056-e711-abaa-00155d701c02` | Vaillant, Fixed tariff, Boiler Only, Smart TRVs         |

## Power Apps Code Apps — SDK & Dataverse Integration Learnings (2 March 2026)

Critical lessons discovered while building the Contact Code App with live Dataverse connectivity.

### 1. URL Parameters — Use SDK `getContext()`, NOT `window.location`

The Power Apps host runs code inside `powerplatformusercontent.com` — **`window.location.search` is always empty**. Query parameters passed from D365 IFrames are only accessible via the SDK:

```typescript
import { getContext } from "@microsoft/power-apps/app";

const ctx = await getContext();
const id = ctx.app.queryParams?.["id"]; // ← correct
// window.location.search → "" ← always empty in Code Apps
```

D365 IFrame "Pass Parameters" appends `&id={guid}&typename=contact&type=2` — these arrive in `ctx.app.queryParams`.

### 2. Boolean (BIT) Fields — Send `true`/`false`, NOT `0`/`1`

**CRITICAL:** Despite the generated TypeScript types using `0 | 1` as key aliases, the Dataverse OData API expects **`Edm.Boolean` (`true`/`false`)**. Sending integers causes:

```
Cannot convert a value of type 'Edm.Int32' to the expected type 'Edm.Boolean'
```

**Correct conversion:**

```typescript
// ✅ CORRECT — Dataverse accepts this
payload.mj_homecarecover = true;

// ❌ WRONG — causes OData error
payload.mj_homecarecover = 1;
```

The generated model types (`Contactsmj_homecarecover = keyof typeof {0: 'No', 1: 'Yes'}`) are misleading — the wire format is native boolean, not integer.

### 3. SDK `update()` Returns Errors Without Throwing

`ContactsService.update()` may return `{ success: false, error: { message: "..." } }` **without throwing an exception**. Always check:

```typescript
const result = await ContactsService.update(id, payload);
const res = result as Record<string, unknown>;
if (res?.success === false && res?.error) {
    throw new Error(`Dataverse update failed: ${(res.error as any).message}`);
}
```

### 4. Field Name Mismatches — Generated Model vs Dataverse

| Dataverse logical name | Generated SDK field | Notes                                      |
| ---------------------- | ------------------- | ------------------------------------------ |
| `company`              | `company`           | NOT `companyname` — different from Web API |
| `fullname`             | `fullname`          | Computed/read-only — omit from `$select`   |
| `mj_primarystore`      | `mj_primarystore`   | Lookup (object type) — omit from `$select` |

Invalid field names in `$select` cause the SDK to silently return empty data without errors.

### 5. `$select` Best Practices for Code Apps SDK

- **Omit computed fields** (`fullname`) — returned automatically
- **Omit lookup fields** (`mj_primarystore`) — object type, can cause silent failures
- **Use exact Dataverse logical names** — verify with MCP `describe_table` or `EntityDefinitions`
- When debugging, try calling `ContactsService.get(id)` with **no options** to rule out `$select` issues

### 6. SDK Result Shape

`ContactsService.get()` returns `IOperationResult<Contacts>`:

```typescript
{
  data: Contacts | null,   // The record (or null if not found)
  success?: boolean,
  error?: { message: string }
}
```

### 7. Deploy Command

```powershell
cd contact-code-app
npm run deploy   # runs: npm run build && pac code push --solutionName CodeApps
```

Always specify `--solutionName CodeApps` to keep the app in the correct solution.

## Contact Energy Dashboard — D365 Web Resource (March 2026)

### Overview

A single-file HTML web resource (`contact-single-html/contact-energy-dashboard.html`) embedded on the D365 Contact form. Uses `Xrm.WebApi` for data access — no external servers, no secrets, no CSP configuration needed.

| Property              | Value                                                 |
| --------------------- | ----------------------------------------------------- |
| **Project Folder**    | `contact-single-html/`                                |
| **Current Version**   | v1.2.0                                                |
| **Web Resource Name** | `mj_contact_energy_dashboard`                         |
| **Web Resource ID**   | `a665e256-0f17-f111-8341-7c1e52fc4a22`                |
| **Form**              | Contact for Utilities (Interactive)                   |
| **Form ID**           | `b45b0a55-3d74-f011-b4cc-002248a0aee6`                |
| **Form Control**      | `WebResource_EnergyDashboard`                         |
| **Data Access**       | `Xrm.WebApi` (parent frame, user-context)             |
| **Fallback Contact**  | Chris Walker (`7fba73b9-2461-ef11-bfe2-002248a36d0e`) |

### CRITICAL: Web Resource Name

The form references `mj_contact_energy_dashboard` — **NOT** `mj_/html/contactenergydashboard.html`. There is a second web resource with the longer name that was created by mistake. Always deploy to the correct name.

The deploy script (`contact-single-html/scripts/deploy-webresource.py`) has `WEB_RESOURCE_NAME = "mj_contact_energy_dashboard"` — this is correct.

### Deploy Command

```powershell
.\.venv\Scripts\python.exe contact-single-html\scripts\deploy-webresource.py
```

This: base64-encodes the HTML file, updates the web resource in Dataverse via PATCH, then publishes via `PublishXml`.

### Verify Deployment

```powershell
.\.venv\Scripts\python.exe contact-single-html\scripts\verify-webresource.py
```

Checks the actual content in Dataverse for version, auto-save presence, etc.

### Auto-Save Architecture (v1.2.0)

- **No Save button** — fields auto-save individually
- **Toggles/dropdowns/dates**: save immediately on change via `setFieldAndSave()`
- **Text inputs**: save on blur (when user tabs/clicks away) via `autoSaveField()`
- **Sequential save queue**: `saveQueue = saveQueue.then(...)` prevents race conditions
- **Status overlay**: floating top-right "Saving…" → "✓ Saved" (fades after 3s)
- **Version badge**: floating bottom-right, subtle grey text

### Layout

- No top bar — fields start at the very top to maximise screen space inside the D365 IFrame
- Fields section → energy charts below
- Chart sizing accounts for IFrame viewport constraints (`Math.min(window.innerHeight, 700)`)

### Key Functions

| Function             | Purpose                                                    |
| -------------------- | ---------------------------------------------------------- |
| `autoSaveField(k,v)` | Builds minimal payload for one field, queues save          |
| `setFieldAndSave()`  | Sets formState + triggers immediate save                   |
| `setField()`         | Sets formState only (for text oninput — defer save)        |
| `showSaveStatus()`   | Updates the floating save status overlay                   |
| `toggleBool()`       | Toggles a boolean field + calls autoSaveField              |
| `getXrmWebApi()`     | Gets Xrm.WebApi from parent frame or self                  |
| `getContactId()`     | Resolves contact ID from Xrm.Page, URL params, or fallback |

### Formatter Warning

The Prettier/VS Code formatter can **re-add deleted code** from undo history or cause merge conflicts when reformatting. After any edit, always verify:

1. Old dead code (`isDirty`, `updateDirtyState`, `handleSave`, `btn-save`) is NOT present
2. Auto-save functions (`autoSaveField`, `setFieldAndSave`, `showSaveStatus`) ARE present
3. Deploy and verify with the check scripts before confirming to user

### Utility Scripts

| Script                               | Purpose                                          |
| ------------------------------------ | ------------------------------------------------ |
| `scripts/deploy-webresource.py`      | Deploy HTML to Dataverse web resource + publish  |
| `scripts/verify-webresource.py`      | Verify deployed content (version, features)      |
| `scripts/check-form-iframes.py`      | List IFrame/WebResource controls on contact form |
| `scripts/check-both-webresources.py` | Compare both web resources side by side          |
