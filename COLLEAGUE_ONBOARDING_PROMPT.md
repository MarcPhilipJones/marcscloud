# Power Platform & Logic Apps Development Context

*Use this document as a system prompt or copilot-instructions.md to educate Claude (Opus 4.5+) about your development environment.*

---

## Environment Overview

We work with Microsoft Power Platform, Azure Logic Apps, and Dynamics 365 Customer Service. This document captures critical knowledge for navigating these systems programmatically.

---

## Dynamics 365 / Dataverse Access

### Connection Details
Replace these with your own environment values:

```
Dataverse Base URL: https://<your-org-id>.crm4.dynamics.com
API Endpoint: https://<your-org-id>.crm4.dynamics.com/api/data/v9.2/
Tenant ID: <your-azure-ad-tenant-id>
Client ID: <your-app-registration-client-id>
Client Secret: (stored in environment variables, NEVER in code)
```

### Authentication Pattern (Python)
```python
from msal import ConfidentialClientApplication

authority = f"https://login.microsoftonline.com/{TENANT_ID}"
scope = [f"{DATAVERSE_URL}/.default"]

app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=authority,
)
result = app.acquire_token_for_client(scopes=scope)
token = result["access_token"]

headers = {
    "Authorization": f"Bearer {token}",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Prefer": "odata.include-annotations=*",
}
```

### Opening Records in Browser UI
```
https://<your-org>.crm4.dynamics.com/main.aspx?etn={entity}&id={guid}&pagetype=entityrecord
```
Example entities: `incident` (case), `contact`, `account`, `subject`, `msdyn_ocliveworkitem`

---

## Case Metadata (incident entity)

### Case Origins (`caseorigincode`)
| Value | Label |
|-------|-------|
| 1 | Phone |
| 2 | Email |
| 3 | Web |
| 2483 | Facebook |
| 3986 | Twitter |
| 700610000 | IoT |

### Priorities (`prioritycode`)
| Value | Label |
|-------|-------|
| 1 | High |
| 2 | Normal |
| 3 | Low |

### State Codes (`statecode`)
| Value | Label |
|-------|-------|
| 0 | Active |
| 1 | Resolved |
| 2 | Cancelled |

---

## Omnichannel Conversations - WHERE TRANSCRIPTS ARE STORED

This is critical knowledge. Omnichannel conversation transcripts are NOT stored directly on the conversation record. They're stored in **annotations** (notes) attached to **msdyn_transcript** records.

### Entity Hierarchy
```
Case (incident)
  └── activitypointers (timeline) 
        └── msdyn_ocliveworkitem (the conversation)
              └── msdyn_transcript (transcript record)
                    └── annotation (contains base64-encoded transcript in documentbody)
```

### Step-by-Step Transcript Retrieval

**Step 1: Get conversation from case timeline**
```http
GET /api/data/v9.2/activitypointers?$filter=_regardingobjectid_value eq {case_id}
```
Look for `activitytypecode = 'msdyn_ocliveworkitem'`

**Step 2: Find transcript record**
Query `msdyn_transcripts` and check `_msdyn_liveworkitemidid_value` (note: double "id" - this is intentional and correct)

Alternatively, filter annotations directly:
```http
GET /api/data/v9.2/annotations?$filter=objecttypecode eq 'msdyn_transcript'
```

**Step 3: Get annotation with transcript content**
```http
GET /api/data/v9.2/annotations?$filter=_objectid_value eq {transcript_id}
```

**Step 4: Decode the transcript**
```python
import base64
import json
import re

# The annotation's documentbody field is base64-encoded
decoded = base64.b64decode(annotation["documentbody"]).decode("utf-8")

# Parse outer JSON array
outer = json.loads(decoded)

# The outer array has one item with a "Content" field containing nested JSON
content_str = outer[0].get("Content", "")
messages = json.loads(content_str)

# Filter out control messages
user_messages = [m for m in messages if not m.get("isControlMessage", False)]

# Each message has these fields:
# - from.user.displayName - sender name
# - content - message text (may contain HTML)
# - createdDateTime - timestamp

for msg in user_messages:
    sender = msg.get("from", {}).get("user", {}).get("displayName", "Copilot")
    content = re.sub(r'<[^>]+>', '', str(msg.get("content", ""))).strip()
    timestamp = msg.get("createdDateTime", "")[:19]
    print(f"[{timestamp}] {sender}: {content}")
```

### Key Fields Reference
- `msdyn_ocliveworkitem` - The conversation record (Omnichannel live work item)
- `msdyn_transcript._msdyn_liveworkitemidid_value` - Links transcript to conversation
- `annotation.documentbody` - Base64 encoded transcript JSON
- `annotation.objecttypecode` - Filter by `'msdyn_transcript'`

---

## Azure Logic Apps (Consumption)

### Workflow Definition Schema
```json
{
  "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {},
  "triggers": {},
  "actions": {}
}
```

### Common Patterns

#### Dataverse Webhook Trigger (conversation closed)
```json
"When_a_conversation_ends": {
  "type": "ApiConnectionWebhook",
  "inputs": {
    "body": {
      "entityname": "msdyn_ocliveworkitem",
      "message": 3,
      "filterexpression": "statecode eq 1 or statecode eq 2 or statuscode eq 4 or statuscode eq 5 or statuscode eq 6"
    }
  }
}
```

#### HTTP Action with OAuth2
```json
"HTTP": {
  "type": "Http",
  "inputs": {
    "method": "GET",
    "uri": "@{parameters('dataverseBaseUrl')}/api/data/v9.2/incidents",
    "authentication": {
      "type": "ActiveDirectoryOAuth",
      "tenant": "@{parameters('dataverseTenantId')}",
      "audience": "@{parameters('dataverseBaseUrl')}",
      "clientId": "@{parameters('dataverseClientId')}",
      "secret": "@{parameters('dataverseClientSecret')}"
    }
  }
}
```

### ARM Deployment
```powershell
# Validate template
az deployment group validate `
  --resource-group <RG> `
  --template-file templates/azuredeploy.json `
  --parameters @parameters/dev.parameters.json

# Deploy
az deployment group create `
  --resource-group <RG> `
  --template-file templates/azuredeploy.json `
  --parameters @parameters/dev.parameters.json
```

---

## Power Automate vs Logic Apps

| Aspect | Power Automate | Logic Apps (Consumption) |
|--------|---------------|-------------------------|
| Target Users | Citizen developers, business users | Pro developers |
| Design Surface | Power Automate portal, web-based | Azure Portal, VS Code, ARM templates |
| Pricing | Per-user or per-flow licenses | Pay-per-execution |
| Connectors | Premium connectors need licensing | All connectors available |
| Source Control | Limited, export/import | Full Git integration with ARM templates |
| ALM | Solution-based | Azure DevOps / GitHub Actions |

### When to Use Which
- **Power Automate**: Simple, user-maintained business processes; citizen developer scenarios
- **Logic Apps**: Complex integrations; API-first design; enterprise-grade reliability; when you need source control

---

## Creating Sample Data

### Python Script Pattern for Creating Cases
```python
from powerplatform.client import DataverseClient

# Subject IDs - query your environment to get these
SUBJECTS = {
    "Pensions": "31895e8f-61fb-f011-8406-7ced8d4279eb",
    "Late Payments": "...",
}

# Contact IDs - query contacts first
CONTACTS = {
    "John Smith": "a7bf9a01-b056-e711-abaa-00155d701c02",
}

with DataverseClient() as client:
    # Create a case
    case_data = {
        "title": "Sample Case Title",
        "description": "Detailed description of the issue",
        "prioritycode": 2,  # Normal
        "caseorigincode": 3,  # Web
        "subjectid@odata.bind": f"/subjects({SUBJECTS['Pensions']})",
        "customerid_contact@odata.bind": f"/contacts({CONTACTS['John Smith']})",
    }
    
    result = client._request("POST", "incidents", data=case_data)
```

### Querying Existing Data
```python
# Get all subjects
subjects = client._request("GET", "subjects?$select=subjectid,title,description")

# Get contacts
contacts = client._request("GET", "contacts?$select=contactid,fullname,emailaddress1&$top=20")

# Get recent cases
cases = client._request(
    "GET", 
    "incidents?$select=incidentid,title,ticketnumber,prioritycode&$top=10&$orderby=createdon desc"
)
```

---

## Field Service Integration (Demo Scenarios)

If your environment includes Dynamics 365 Field Service, you can search for engineer availability and book work orders:

### Search Resource Availability
```http
POST /api/data/v9.2/msdyn_SearchResourceAvailability
Content-Type: application/json

{
  "Version": "3",
  "Requirement": {
    "@odata.type": "Microsoft.Dynamics.CRM.msdyn_resourcerequirement",
    "msdyn_fromdate": "2026-02-17T08:00:00Z",
    "msdyn_todate": "2026-02-18T18:00:00Z",
    "msdyn_duration": 60
  }
}
```

### Key Field Service Entities
- `msdyn_workorder` - Work orders
- `msdyn_workordertype` - Work order types (e.g., "Boiler Repair")
- `bookableresourcebooking` - Bookings
- `bookableresource` - Engineers/resources

---

## Common Gotchas

1. **Double "id" in transcript linking**: The field is `_msdyn_liveworkitemidid_value` - the double "id" is correct
2. **Base64 + nested JSON**: Transcripts are base64-encoded JSON containing a string field that's ALSO JSON
3. **HTML in messages**: Chat message content may contain HTML tags - strip them before display
4. **Control messages**: Filter out `isControlMessage: true` entries - they're system events, not conversation
5. **OData bind syntax**: When setting lookups in POST/PATCH, use `fieldname@odata.bind` format with entity set plural name
6. **State vs Status**: `statecode` is the high-level state (Active/Resolved/Cancelled); `statuscode` is the detailed status

---

## Environment Variables to Configure

Create a `.env` file with:
```bash
DATAVERSE_BASE_URL=https://<your-org>.crm4.dynamics.com
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-app-client-id>
AZURE_CLIENT_SECRET=<your-secret>
DATAVERSE_API_VERSION=v9.2
```

---

## Useful Scripts to Create

1. **get_case_metadata.py** - Retrieves picklist values for case origins, priorities, subjects
2. **display_transcript.py** - Given a case ID, retrieves and displays the conversation transcript
3. **create_demo_cases.py** - Creates sample cases with realistic data for demos
4. **find_conversations.py** - Lists recent Omnichannel conversations

---

## Recommended Project Structure

```
your-project/
├── .github/
│   └── copilot-instructions.md    # This document!
├── .vscode/
│   └── tasks.json                  # VS Code tasks
├── PowerPlatform/
│   ├── src/
│   │   └── powerplatform/
│   │       ├── auth.py             # Authentication helper
│   │       ├── client.py           # Dataverse API client
│   │       └── entities.py         # Entity models
│   └── scripts/
│       └── *.py                    # Utility scripts
├── workflows/
│   └── *.json                      # Logic App workflow definitions
├── templates/
│   └── azuredeploy.json            # ARM template
├── parameters/
│   ├── dev.parameters.json
│   ├── dev.secrets.parameters.json # Git-ignored, contains secrets
│   └── prod.parameters.json
└── .env                            # Git-ignored, local secrets
```

---

## Quick Reference: Common API Calls

```python
# Get a case by ticket number
client._request("GET", "incidents?$filter=ticketnumber eq 'CAS-01234-ABC123'&$top=1")

# Get conversation from case timeline
client._request("GET", f"activitypointers?$filter=_regardingobjectid_value eq {case_id}")

# Get annotation (transcript) content
client._request("GET", f"annotations({annotation_id})")

# Update a case
client._request("PATCH", f"incidents({case_id})", data={"description": "Updated description"})

# Query with expand (get related records)
client._request("GET", f"incidents({case_id})?$expand=customerid_contact($select=fullname,emailaddress1)")
```

---

*Last updated: February 2026*
