# Field Service for MikeO

Dataverse client for managing Dynamics 365 Field Service Work Order Types.

## Overview

This project provides utilities to create, list, update, and delete Work Order Types in Dynamics 365 Field Service via the Dataverse Web API.

## Work Order Types

Work Order Types (`msdyn_workordertype`) define the category of work to be performed. Common examples include:
- Installation
- Inspection
- Maintenance
- Repair
- Emergency Service

## Setup

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the package:
   ```powershell
   pip install -e .
   ```

3. Create a `.env` file with your Dataverse credentials:
   ```
   DATAVERSE_URL=https://your-org.crm.dynamics.com
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   ```

## Usage

### List Work Order Types
```powershell
field-service list
```

### Create Work Order Type
```powershell
field-service create --name "Emergency Repair" --incident-required
```

### Get Work Order Type Details
```powershell
field-service get --id <guid>
```

## Dataverse Entity Reference

### msdyn_workordertype
| Column | Type | Description |
|--------|------|-------------|
| msdyn_workordertypeid | GUID | Primary key |
| msdyn_name | String | Name of work order type |
| msdyn_incidentrequired | Boolean | Incident type required |
| msdyn_taxable | Boolean | Is taxable |
| statecode | OptionSet | Status (Active/Inactive) |

## API Endpoints

Base URL: `{DATAVERSE_URL}/api/data/v9.2/`

- GET `msdyn_workordertypes` - List all work order types
- POST `msdyn_workordertypes` - Create new work order type
- GET `msdyn_workordertypes({id})` - Get specific work order type
- PATCH `msdyn_workordertypes({id})` - Update work order type
- DELETE `msdyn_workordertypes({id})` - Delete work order type

## License

Internal use only.
