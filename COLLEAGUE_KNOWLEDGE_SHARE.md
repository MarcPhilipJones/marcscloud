# Power Platform & Azure Development Knowledge Base

This document contains accumulated learnings, patterns, and best practices for Power Platform, Dynamics 365, Azure, and Home Assistant development. Place this file in your workspace's `.github/copilot-instructions.md` to have Copilot use these patterns.

---

## How This Knowledge Was Built

This knowledge base was created by documenting discoveries, workarounds, and patterns during real development work. The key practice is:

1. When you discover something useful, document it immediately
2. Place learnings in `.github/copilot-instructions.md` so Copilot remembers them
3. Use the **SpecStory** extension to save chat history for cross-session memory

### SpecStory Extension Setup

Install: `specstory.specstory-vscode`

Chat history is saved to: `.specstory/history/`

```powershell
# List recent chat files
Get-ChildItem ".specstory\history" | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Search for chats about a topic
Get-ChildItem ".specstory\history" -Filter "*field*"
```

**Key Practice**: When you learn something important in a chat, add it to `copilot-instructions.md` for permanent memory across sessions.

---

## Azure Cognitive Services - API Key Authentication Bypass

When managed environment policies block API key authentication (`DisableLocalAuth = true`), use this workaround:

### SecurityControl Tag Bypass (14-day window)

1. **Add bypass tag** (use REST API if PowerShell doesn't apply it):
   ```powershell
   $tags = @{ SecurityControl = "Ignore" }
   Set-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" -Tag $tags
   ```
   
   Or via REST API:
   ```powershell
   $body = @{ tags = @{ SecurityControl = "Ignore" } } | ConvertTo-Json
   Invoke-RestMethod -Uri $uri -Method Patch -Headers @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" } -Body $body
   ```

2. **Disable local auth restriction**:
   ```powershell
   Set-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" -DisableLocalAuth $false
   ```

3. **Verify**:
   ```powershell
   Get-AzCognitiveServicesAccount -ResourceGroupName "<RG>" -Name "<AccountName>" | Select-Object AccountName, Tags, DisableLocalAuth
   ```

**Warning**: This bypass only works for **14 days** before policy re-enforces. Discovered via MCAPS support.

---

## Dynamics 365 Web API Patterns

### Opening Records in Browser
```
https://{org}.crm{region}.dynamics.com/main.aspx?etn={entity}&id={guid}&pagetype=entityrecord
```
Example entities: `incident` (case), `contact`, `account`, `subject`

### Case Metadata Reference

**Case Origins (`caseorigincode`)**:
| Value | Label |
|-------|-------|
| 1 | Phone |
| 2 | Email |
| 3 | Web |
| 2483 | Facebook |
| 3986 | Twitter |
| 700610000 | IoT |

**Priorities (`prioritycode`)**:
| Value | Label |
|-------|-------|
| 1 | High |
| 2 | Normal |
| 3 | Low |

---

## Retrieving Omnichannel Conversation Transcripts

Transcripts are stored in annotations attached to `msdyn_transcript` records.

### Data Path
```
Case (incident)
  └── activitypointers (timeline) 
        └── msdyn_ocliveworkitem (conversation)
              └── msdyn_transcript (transcript record)
                    └── annotation (base64-encoded transcript in documentbody)
```

### Retrieval Steps

1. **Get conversation from case timeline:**
   ```
   GET activitypointers?$filter=_regardingobjectid_value eq {case_id}
   ```
   Look for `activitytypecode = 'msdyn_ocliveworkitem'`

2. **Find transcript record:**
   - Query `msdyn_transcripts` and check `_msdyn_liveworkitemidid_value` (note: double "id")
   - Or filter annotations by `objecttypecode eq 'msdyn_transcript'`

3. **Get annotation with transcript:**
   ```
   GET annotations?$filter=_objectid_value eq {transcript_id}
   ```

4. **Decode transcript:**
   - Base64 decode `documentbody`
   - Parse outer JSON array
   - Parse `Content` field as nested JSON array of messages
   - Filter out `isControlMessage: true` entries
   - Each message has: `from.user.displayName`, `content`, `createdDateTime`

### Key Fields
- `msdyn_transcript._msdyn_liveworkitemidid_value` → links to conversation
- `annotation.documentbody` → base64 encoded transcript JSON
- `annotation.objecttypecode` → filter by `'msdyn_transcript'`

---

## Dataverse Web API with Python

### Authentication Pattern
```python
import httpx
from msal import ConfidentialClientApplication

def get_dataverse_token(tenant_id, client_id, client_secret, resource):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )
    result = app.acquire_token_for_client(scopes=[f"{resource}/.default"])
    return result["access_token"]

# Usage
token = get_dataverse_token(tenant_id, client_id, client_secret, base_url)
headers = {'Authorization': f'Bearer {token}'}
```

### Query Pattern
```python
url = f'{base_url}/api/data/v9.2/msdyn_workorders?$select=msdyn_workorderid,msdyn_name&$orderby=createdon desc&$top=5'

with httpx.Client(timeout=30.0) as client:
    resp = client.get(url, headers={'Authorization': f'Bearer {token}'})
    data = resp.json()
```

### Required Packages
```powershell
pip install msal httpx --only-binary :all:
```

---

## Field Service - Key Entities

| Entity | Purpose |
|--------|---------|
| `msdyn_workorders` | Work orders |
| `msdyn_workorderservicetasks` | Service tasks on work orders |
| `msdyn_bookableresourcebookings` | Bookings/schedules |
| `msdyn_workordertypes` | Work order types |
| `bookableresources` | Technicians/resources |
| `msdyn_incidenttypes` | Incident types (templates) |
| `msdyn_servicetasktypes` | Service task type definitions |
| `msdyn_incidenttypeservicetasks` | Links tasks to incident types |
| `characteristics` | Skills and certifications |
| `bookableresourcecharacteristics` | Assigns characteristics to resources |

### Work Order System Status (`msdyn_systemstatus`)
| Value | Label |
|-------|-------|
| 690970000 | Unscheduled |
| 690970001 | Scheduled |
| 690970002 | In Progress |
| 690970003 | Completed |
| 690970004 | Posted |
| 690970005 | Canceled |

---

## Creating Field Service Data via API

### Work Order Type
```python
client.post("msdyn_workordertypes", {
    "msdyn_name": "Printer Installation",
    "msdyn_incidentrequired": True,
    "msdyn_taxable": False
})
```

### Service Task Type
```python
client.post("msdyn_servicetasktypes", {
    "msdyn_name": "Test Print & Validation",
    "msdyn_estimatedduration": 4,  # minutes
    "msdyn_description": "Print test page, verify quality"
})
```

### Incident Type (links to Work Order Type)
```python
client.post("msdyn_incidenttypes", {
    "msdyn_name": "Printer Installation",
    "msdyn_estimatedduration": 30,
    "msdyn_description": "Install and configure network printer",
    "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({work_order_type_id})"
})
```

### Link Service Task to Incident Type
```python
client.post("msdyn_incidenttypeservicetasks", {
    "msdyn_name": "Step 1 - Check Equipment",
    "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incident_type_id})",
    "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({task_type_id})",
    "msdyn_lineorder": 1
})
```

### Characteristic (Skill/Certification)
```python
# characteristictype: 1=Skill, 2=Certification
client.post("characteristics", {
    "name": "Network Cabling & Termination",
    "characteristictype": 1
})
```

### Assign Characteristic to Bookable Resource
```python
client.post("bookableresourcecharacteristics", {
    "Resource@odata.bind": f"/bookableresources({resource_id})",
    "Characteristic@odata.bind": f"/characteristics({char_id})"
})
```

---

## OData Binding Patterns

When creating records with relationships, use `@odata.bind`:
```python
{
    "fieldname@odata.bind": "/entitysetname(guid)"
}
```

**Examples:**
- `"msdyn_workordertype@odata.bind": "/msdyn_workordertypes(abc-123)"`
- `"parentaccountid@odata.bind": "/accounts(def-456)"`
- `"transactioncurrencyid@odata.bind": "/transactioncurrencies(ghi-789)"`

### Currency Handling (UK/GBP)
```python
# Get GBP currency ID
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

---

## Home Assistant Development Patterns

### Running Home Assistant on Raspberry Pi 5 with Docker

Recommended container stack:
| Container | Image | Purpose |
|-----------|-------|---------|
| homeassistant | ghcr.io/home-assistant/home-assistant:stable | Main HA instance |
| matter-server | ghcr.io/home-assistant-libs/python-matter-server:stable | Matter/Thread bridge |
| scrypted | ghcr.io/koush/scrypted:latest | Camera/HomeKit bridge |
| homebridge | homebridge/homebridge:latest | HomeKit bridge |
| portainer | portainer/portainer-ce:latest | Docker management |
| watchtower | containrrr/watchtower | Auto-update containers |

### Thread & Matter Device Workflow

If using Apple HomeKit as Thread controller:

1. Add device to **Apple Home first**
2. Test it works in Apple Home
3. Get pairing code from Apple Home (Settings → Device → Turn on Pairing Mode)
4. Add to Home Assistant using that pairing code

This uses Matter's **multi-admin** feature - devices respond to both controllers simultaneously.

### Home Assistant MCP Tools

Use Home Assistant MCP tools for:
- `ha_get_states` - Get all entity states
- `ha_call_service` - Call services (turn on lights, etc.)
- `ha_fire_event` - Fire events
- `ha_get_history` - Get historical data
- `ha_render_template` - Test Jinja templates

---

## VS Code Tips

### Chrome Profile for Dynamics 365
```powershell
# Open URL in specific Chrome profile
Start-Process chrome.exe -ArgumentList "--profile-directory=`"Profile 2`"", "https://your-org.crm.dynamics.com"
```

### Environment File Pattern
Keep secrets in `.env` files (not committed):
```dotenv
DATAVERSE_BASE_URL=https://orgXXX.crm4.dynamics.com
DATAVERSE_TENANT_ID=your-tenant-id
DATAVERSE_CLIENT_ID=your-client-id
DATAVERSE_CLIENT_SECRET=your-secret
DATAVERSE_API_VERSION=v9.2
DATAVERSE_ALLOW_WRITES=true
```

---

## Key Learnings Summary

1. **Azure Policy Bypass**: `SecurityControl = "Ignore"` tag bypasses managed policies for 14 days
2. **Transcript Location**: Omnichannel transcripts are base64-encoded in annotations linked via `msdyn_transcript`
3. **OData Relationships**: Use `@odata.bind` syntax for creating records with lookups
4. **Matter Multi-Admin**: Devices can be controlled by multiple platforms simultaneously
5. **Cross-Session Memory**: Use SpecStory + copilot-instructions.md to persist learnings
6. **Field Service Status Codes**: Values are 690970000-690970005 for Unscheduled through Canceled

---

## How to Use This Document

1. **Copy to your workspace**: Place in `.github/copilot-instructions.md`
2. **Customize**: Update with your own environment values and learnings
3. **Extend**: Add new sections as you discover patterns
4. **Share**: This document travels with your workspace

When Copilot has this file, it will use these patterns and knowledge to help you more effectively.
