# Power Automate Solution Creation via CLI

This folder contains Power Automate flows packaged as Dataverse solutions for deployment via `pac` CLI.

## Prerequisites

- **pac CLI** installed and authenticated
- Authentication: `pac auth create --environment "https://yourorg.crm.dynamics.com"`
- Check auth: `pac auth list`

## Solution Structure (Required Files)

```
SolutionFolder/
├── solution.xml              # Solution manifest
├── customizations.xml        # Workflow metadata + connection references
├── [Content_Types].xml       # Content types declaration
└── Workflows/
    └── FlowName-GUID.json    # Flow definition (GUID in uppercase)
```

## Key File Formats

### 1. solution.xml

```xml
<ImportExportXml version="9.2.25124.197" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SolutionManifest>
    <UniqueName>YourSolutionName</UniqueName>
    <LocalizedNames>
      <LocalizedName description="Your Solution Name" languagecode="1033" />
    </LocalizedNames>
    <Descriptions>
      <Description description="Description here" languagecode="1033" />
    </Descriptions>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>YourPublisher</UniqueName>
      <LocalizedNames>
        <LocalizedName description="Your Publisher" languagecode="1033" />
      </LocalizedNames>
      <Descriptions>
        <Description description="Publisher description" languagecode="1033" />
      </Descriptions>
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>prefix</CustomizationPrefix>
      <CustomizationOptionValuePrefix>10000</CustomizationOptionValuePrefix>
      <!-- Address blocks required but can be nil -->
    </Publisher>
    <RootComponents>
      <!-- type="29" = Workflow/Flow -->
      <RootComponent type="29" id="{your-flow-guid-here}" behavior="0" />
    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
```

### 2. customizations.xml

```xml
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Entities></Entities>
  <Roles></Roles>
  <Workflows>
    <Workflow WorkflowId="{your-flow-guid}" Name="Flow Display Name">
      <JsonFileName>/Workflows/FlowName-GUID.json</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>           <!-- 5 = Modern Flow -->
      <Mode>0</Mode>
      <Scope>4</Scope>                 <!-- 4 = Organization -->
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>1</StateCode>         <!-- 1 = Active -->
      <StatusCode>2</StatusCode>       <!-- 2 = Activated -->
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>incident</PrimaryEntity>  <!-- or 'none' if no entity -->
      <LocalizedNames>
        <LocalizedName languagecode="1033" description="Flow Display Name" />
      </LocalizedNames>
    </Workflow>
  </Workflows>
  <FieldSecurityProfiles></FieldSecurityProfiles>
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <connectionreferences>
    <connectionreference connectionreferencelogicalname="prefix_sharedconnector_uniqueid">
      <connectionreferencedisplayname>Microsoft Dataverse</connectionreferencedisplayname>
      <connectorid>/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps</connectorid>
      <iscustomizable>1</iscustomizable>
      <promptingbehavior>0</promptingbehavior>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>
  </connectionreferences>
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>
```

### 3. [Content_Types].xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/octet-stream" />
  <Default Extension="json" ContentType="application/octet-stream" />
</Types>
```

### 4. Flow JSON (Workflows/FlowName-GUID.json)

```json
{
  "properties": {
    "connectionReferences": {
      "shared_commondataserviceforapps": {
        "api": {
          "name": "shared_commondataserviceforapps"
        },
        "connection": {
          "connectionReferenceLogicalName": "prefix_sharedconnector_uniqueid"
        },
        "runtimeSource": "embedded"
      }
    },
    "definition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "contentVersion": "1.0.0.0",
      "parameters": {
        "$authentication": {
          "defaultValue": {},
          "type": "SecureObject"
        },
        "$connections": {
          "defaultValue": {},
          "type": "Object"
        }
      },
      "triggers": {
        "Your_Trigger_Name": {
          "type": "OpenApiConnectionWebhook",
          "inputs": {
            "parameters": {
              "subscriptionRequest/message": 1,
              "subscriptionRequest/entityname": "incident",
              "subscriptionRequest/scope": 4
            },
            "host": {
              "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
              "operationId": "SubscribeWebhookTrigger",
              "connectionName": "shared_commondataserviceforapps"
            }
          }
        }
      },
      "actions": {
        "Your_Action_Name": {
          "type": "InitializeVariable",
          "inputs": {
            "variables": [
              {
                "name": "VariableName",
                "type": "string",
                "value": "@triggerOutputs()?['body/fieldname']"
              }
            ]
          },
          "runAfter": {}
        }
      },
      "outputs": {}
    },
    "templateName": null
  },
  "schemaVersion": "1.0.0.0"
}
```

## Critical Requirements

1. **GUID Format**: Use format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}` in XML, uppercase in filenames
2. **Forward Slashes**: ZIP must use forward slashes (`Workflows/file.json` not `Workflows\file.json`)
3. **schemaVersion**: Required at root level of flow JSON: `"schemaVersion": "1.0.0.0"`
4. **templateName**: Include `"templateName": null` in properties
5. **Connection Reference Match**: `connectionReferenceLogicalName` in JSON must match `connectionreferencelogicalname` in customizations.xml

## Trigger Message Types (subscriptionRequest/message)

| Value | Meaning |
|-------|---------|
| 1 | Create |
| 2 | Update |
| 3 | Delete |
| 4 | Create or Update |

## Trigger Scope Values (subscriptionRequest/scope)

| Value | Meaning |
|-------|---------|
| 1 | User |
| 2 | Business Unit |
| 3 | Parent: Child Business Units |
| 4 | Organization |

## Common Dataverse Entities

| Logical Name | Display Name |
|--------------|--------------|
| incident | Case |
| account | Account |
| contact | Contact |
| opportunity | Opportunity |
| lead | Lead |
| email | Email |
| task | Task |
| appointment | Appointment |
| msdyn_workorder | Work Order |

## ZIP Creation (PowerShell)

```powershell
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$solutionPath = "path\to\SolutionFolder"
$zipPath = "path\to\Solution.zip"

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$zip = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)

Get-ChildItem -Path $solutionPath -Recurse -File | ForEach-Object {
    # CRITICAL: Replace backslashes with forward slashes
    $relativePath = $_.FullName.Substring($solutionPath.Length + 1).Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $relativePath) | Out-Null
}

$zip.Dispose()
```

## Import Commands

```powershell
# Import solution
pac solution import --path "Solution.zip"

# Verify import
pac solution list | Select-String "SolutionName"

# Export to verify contents
pac solution export --name SolutionName --path "SolutionName_verify.zip"
```

## Post-Import: Manual Steps

⚠️ **Connection Reference Setup Required**

After import, you must manually configure the connection reference:
1. Go to `make.powerapps.com` → Solutions → Your Solution
2. Find Connection References
3. Select each connection reference and set the connection

This is required because connections contain credentials/auth that can't be included in the solution package.

## Example Solutions

- `CasePOC/` - Simple POC: Case trigger → Initialize 2 variables
- `MarcsFlowa_extracted/` - Reference export showing production flow structure
