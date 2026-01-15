# Azure Logic Apps Consumption Development

This workspace is configured for developing Azure Logic Apps using the Consumption pricing model.

## Project Structure

```
logicappsdevelopment/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot workspace instructions
├── .vscode/
│   └── tasks.json                  # VS Code tasks for deployment
├── workflows/
│   ├── HelloWorld.json             # Simple HTTP request/response workflow
│   └── ProcessOrder.json           # Order processing workflow with conditions
├── parameters/
│   ├── dev.parameters.json         # Development environment parameters
│   └── prod.parameters.json        # Production environment parameters
├── templates/
│   └── azuredeploy.json            # ARM template for Logic App deployment
├── connections.json                # Managed API and service provider connections
└── README.md                       # This file
```

## Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/)
- [Azure Logic Apps (Consumption) Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurelogicapps)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) (for deployment)
- Active Azure subscription

## Getting Started

### 1. Install Required Extensions

The Azure Logic Apps extension should already be installed. If not:
1. Open VS Code Extensions (`Ctrl+Shift+X`)
2. Search for "Azure Logic Apps"
3. Install the extension from Microsoft

### 2. Connect to Azure

1. Click on the Azure icon in the Activity Bar
2. Sign in to your Azure account
3. Select your subscription

### 3. Working with Workflows

#### Sample Workflows Included

- **HelloWorld.json**: A basic HTTP-triggered workflow that responds with a greeting
- **ProcessOrder.json**: An order processing workflow demonstrating:
  - HTTP request trigger with schema validation
  - Variables and conditional logic
  - Response formatting

#### Creating New Workflows

1. Right-click the `workflows` folder
2. Select "New File"
3. Name it with `.json` extension
4. Use the Logic Apps workflow definition schema

### 4. Local Development

1. Open workflow files in the designer:
   - Right-click on a `.json` workflow file
   - Select "Open in Designer" (if available)
   - Or edit JSON directly in the editor

2. Test workflows locally using the designer's test functionality

### 5. Deployment

#### Using VS Code Tasks

Press `Ctrl+Shift+P` and run:
```
Tasks: Run Task > Deploy Logic App to Azure
```

#### Using Azure CLI

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your-Subscription-Name"

# Create resource group (if needed)
az group create --name MyResourceGroup --location eastus

# Deploy to development
az deployment group create \
  --resource-group MyResourceGroup \
  --template-file templates/azuredeploy.json \
  --parameters @parameters/dev.parameters.json

# Deploy to production
az deployment group create \
  --resource-group MyResourceGroup \
  --template-file templates/azuredeploy.json \
  --parameters @parameters/prod.parameters.json
```

#### Using the Azure Portal

1. Navigate to Azure Portal
2. Create a new Logic App resource
3. Open the Logic App Designer
4. Copy/paste workflow definition from JSON files

## Configuration

### Parameters

Environment-specific parameters are stored in the `parameters/` folder:
- `dev.parameters.json` - Development environment
- `prod.parameters.json` - Production environment

Secrets are kept out of source control:
- Create `parameters/dev.secrets.parameters.json` locally (see `parameters/dev.secrets.parameters.example.json`)
- Do not commit `*.secrets.parameters.json` files (they are ignored by `.gitignore`)

Update these files with your specific values before deployment.

### Connections

The `connections.json` file stores API connection configurations. Update this file when using:
- Office 365
- Azure Storage
- SQL Server
- Other managed connectors

## Workflow Definition Schema

All workflows follow the Azure Logic Apps workflow definition schema:
- Schema: `https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#`
- [Full schema documentation](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-definition-language)

## Best Practices

1. **Use Parameters**: Store environment-specific values in parameter files
2. **Version Control**: Commit workflow definitions to source control
3. **Naming Conventions**: Use descriptive names for workflows and actions
4. **Error Handling**: Implement proper error handling with run-after conditions
5. **Testing**: Test workflows in development before deploying to production
6. **Security**: Use managed identities and Key Vault for secrets
7. **Monitoring**: Enable diagnostic settings and Application Insights

## Common Commands

```bash
# List Logic Apps in resource group
az logicapp list --resource-group MyResourceGroup

# Show Logic App details
az logicapp show --name MyLogicApp --resource-group MyResourceGroup

# Delete Logic App
az logicapp delete --name MyLogicApp --resource-group MyResourceGroup
```

## Troubleshooting

### Workflow Not Triggering
- Check trigger configuration and authentication
- Verify callback URL is accessible
- Review run history in Azure Portal

### Deployment Errors
- Validate JSON syntax in workflow files
- Check ARM template parameters match required values
- Ensure Azure CLI is authenticated

### Connection Issues
- Update connections.json with correct connection information
- Verify API connections are authorized in Azure Portal
- Check service limits and quotas

## Resources

- [Azure Logic Apps Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/)
- [Workflow Definition Language](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-definition-language)
- [Connectors Documentation](https://docs.microsoft.com/en-us/connectors/)
- [ARM Template Reference](https://docs.microsoft.com/en-us/azure/templates/microsoft.logic/workflows)

## License

This project template is provided as-is for development purposes.
