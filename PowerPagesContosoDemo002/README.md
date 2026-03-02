# PowerPagesContosoDemo002

Power Pages development project for Contoso Demo portal.

## Environment

- **Tenant**: D365DemoTSCE63319057.onmicrosoft.com
- **Environment**: MJCC2024
- **Environment URL**: https://org6cb3e9fb.crm4.dynamics.com/

## Available Portals

| Portal | Website ID |
|--------|------------|
| Demo Factory Customer Self-Service | 4f305015-545a-ef11-bfe3-000d3adf7d02 |
| Customer Service 002 | 0ee2eac6-3d1a-4ad3-8c82-607cbf53cd50 |
| D365 FieldService Portal | 90f4b6ec-b424-4f21-80f6-6a550785ca21 |
| Customer Service 003 | 06d030f8-d704-f011-bae3-7c1e527722a8 |
| Customer Self Service 001 | ea12d997-bf5f-ef11-bfe3-000d3a65cf07 |

## Getting Started

### Download Portal Content

```powershell
# Download a specific portal
pac powerpages download --websiteId <website-id> --path ./portal-content

# Example: Download Customer Service 002
pac powerpages download --websiteId 0ee2eac6-3d1a-4ad3-8c82-607cbf53cd50 --path ./portal-content
```

### Upload Changes

```powershell
# Upload changes back to Dataverse
pac powerpages upload --path ./portal-content
```

### Preview Changes

Use the Power Pages design studio or run locally with the VS Code Power Platform Tools extension.

## Project Structure

```
PowerPagesContosoDemo002/
├── README.md
├── portal-content/          # Downloaded portal files
│   ├── web-pages/
│   ├── web-templates/
│   ├── content-snippets/
│   ├── web-files/
│   └── ...
└── .gitignore
```

## Useful Commands

```powershell
# List portals
pac powerpages list

# Check auth
pac auth list

# Switch environment
pac auth select --index <n>
```
