const fs = require('fs');
const path = require('path');

function readJson(relPath) {
  const fullPath = path.join(__dirname, '..', relPath);
  return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
}

function ordered(obj) {
  // For readability only: JS preserves insertion order for string keys.
  return obj;
}

function newDvConnectionResource(nameExpr, displayNameExpr) {
  return ordered({
    type: 'Microsoft.Web/connections',
    apiVersion: '2016-06-01',
    name: nameExpr,
    location: "[parameters('location')]",
    properties: ordered({
      displayName: displayNameExpr,
      api: ordered({ id: "[variables('dataverseManagedApiId')]" }),
      parameterValues: ordered({
        'token:TenantId': "[parameters('dataverseTenantId')]",
        'token:clientId': "[parameters('dataverseClientId')]",
        'token:clientSecret': "[parameters('dataverseClientSecret')]",
        'token:grantType': 'client_credentials',
        'token:resourceUri': "[parameters('dataverseBaseUrl')]",
      }),
    }),
  });
}

function writeTemplate() {
  const ccas = readJson('workflows/CCASGetConversation.json');
  const analyse = readJson('workflows/AnalyseCustomer.json');
  const version2 = readJson('workflows/AnalyseCustomerVersion2.json');

  const parameters = ordered({
    logicAppName: ordered({ type: 'string', metadata: { description: 'Name of the Logic App' } }),
    analyseCustomerLogicAppName: ordered({
      type: 'string',
      defaultValue: 'AnalyseCustomer',
      metadata: { description: 'Name of the AnalyseCustomer Logic App' },
    }),
    analyseCustomer2LogicAppName: ordered({
      type: 'string',
      defaultValue: 'AnalyseCustomer2',
      metadata: { description: 'Name of the AnalyseCustomer2 Logic App' },
    }),
    analyseCustomerVersion2LogicAppName: ordered({
      type: 'string',
      defaultValue: 'AnalyseCustomerVersion2',
      metadata: { description: 'Name of the AnalyseCustomerVersion2 Logic App' },
    }),
    location: ordered({
      type: 'string',
      defaultValue: '[resourceGroup().location]',
      metadata: { description: 'Location for all resources' },
    }),

    dataverseBaseUrl: ordered({
      type: 'string',
      metadata: {
        description: 'Base URL of the Dataverse environment, e.g. https://<org>.crm4.dynamics.com',
      },
    }),
    dataverseTenantId: ordered({ type: 'string', metadata: { description: 'Azure AD Tenant ID' } }),
    dataverseClientId: ordered({ type: 'string', metadata: { description: 'Application (client) ID' } }),
    dataverseClientSecret: ordered({
      type: 'securestring',
      metadata: { description: 'Client secret for the app registration' },
    }),

    openAiEndpoint: ordered({
      type: 'string',
      defaultValue: 'https://mjopenai2.openai.azure.com/',
      metadata: { description: 'Azure OpenAI endpoint, e.g. https://<resource>.openai.azure.com/' },
    }),
    openAiDeployment: ordered({
      type: 'string',
      defaultValue: 'gpt-4o',
      metadata: { description: 'Azure OpenAI deployment name' },
    }),
    openAiApiVersion: ordered({
      type: 'string',
      defaultValue: '2024-10-21',
      metadata: { description: 'Azure OpenAI API version' },
    }),
    openAiApiKey: ordered({ type: 'securestring', metadata: { description: 'Azure OpenAI API key' } }),
  });

  const variables = ordered({
    logicAppDataverseConnectionName: "[concat(parameters('logicAppName'), '-dataverse')]",
    analyseCustomerDataverseConnectionName: "[concat(parameters('analyseCustomerLogicAppName'), '-dataverse')]",
    analyseCustomer2DataverseConnectionName: "[concat(parameters('analyseCustomer2LogicAppName'), '-dataverse')]",
    analyseCustomerVersion2DataverseConnectionName:
      "[concat(parameters('analyseCustomerVersion2LogicAppName'), '-dataverse')]",
    dataverseManagedApiId:
      "[concat(subscription().id, '/providers/Microsoft.Web/locations/', parameters('location'), '/managedApis/commondataservice')]",
  });

  const resources = [
    newDvConnectionResource(
      "[variables('logicAppDataverseConnectionName')]",
      "[concat(parameters('logicAppName'), ' Dataverse')]",
    ),
    newDvConnectionResource(
      "[variables('analyseCustomerDataverseConnectionName')]",
      "[concat(parameters('analyseCustomerLogicAppName'), ' Dataverse')]",
    ),
    newDvConnectionResource(
      "[variables('analyseCustomer2DataverseConnectionName')]",
      "[concat(parameters('analyseCustomer2LogicAppName'), ' Dataverse')]",
    ),
    newDvConnectionResource(
      "[variables('analyseCustomerVersion2DataverseConnectionName')]",
      "[concat(parameters('analyseCustomerVersion2LogicAppName'), ' Dataverse')]",
    ),

    ordered({
      type: 'Microsoft.Logic/workflows',
      apiVersion: '2019-05-01',
      name: "[parameters('logicAppName')]",
      location: "[parameters('location')]",
      dependsOn: ["[resourceId('Microsoft.Web/connections', variables('logicAppDataverseConnectionName'))]"],
      properties: ordered({
        state: 'Enabled',
        definition: ccas,
        parameters: ordered({
          $connections: ordered({
            value: ordered({
              commondataservice: ordered({
                connectionId: "[resourceId('Microsoft.Web/connections', variables('logicAppDataverseConnectionName'))]",
                connectionName: "[variables('logicAppDataverseConnectionName')]",
                id: "[variables('dataverseManagedApiId')]",
              }),
            }),
          }),
          dataverseBaseUrl: { value: "[parameters('dataverseBaseUrl')]" },
          dataverseTenantId: { value: "[parameters('dataverseTenantId')]" },
          dataverseClientId: { value: "[parameters('dataverseClientId')]" },
          dataverseClientSecret: { value: "[parameters('dataverseClientSecret')]" },
        }),
      }),
    }),

    ordered({
      type: 'Microsoft.Logic/workflows',
      apiVersion: '2019-05-01',
      name: "[parameters('analyseCustomerLogicAppName')]",
      location: "[parameters('location')]",
      dependsOn: [
        "[resourceId('Microsoft.Web/connections', variables('analyseCustomerDataverseConnectionName'))]",
      ],
      properties: ordered({
        state: 'Enabled',
        definition: analyse,
        parameters: ordered({
          $connections: ordered({
            value: ordered({
              commondataservice: ordered({
                connectionId:
                  "[resourceId('Microsoft.Web/connections', variables('analyseCustomerDataverseConnectionName'))]",
                connectionName: "[variables('analyseCustomerDataverseConnectionName')]",
                id: "[variables('dataverseManagedApiId')]",
              }),
            }),
          }),
          dataverseBaseUrl: { value: "[parameters('dataverseBaseUrl')]" },
          dataverseTenantId: { value: "[parameters('dataverseTenantId')]" },
          dataverseClientId: { value: "[parameters('dataverseClientId')]" },
          dataverseClientSecret: { value: "[parameters('dataverseClientSecret')]" },
          openAiEndpoint: { value: "[parameters('openAiEndpoint')]" },
          openAiDeployment: { value: "[parameters('openAiDeployment')]" },
          openAiApiVersion: { value: "[parameters('openAiApiVersion')]" },
          openAiApiKey: { value: "[parameters('openAiApiKey')]" },
        }),
      }),
    }),

    ordered({
      type: 'Microsoft.Logic/workflows',
      apiVersion: '2019-05-01',
      name: "[parameters('analyseCustomer2LogicAppName')]",
      location: "[parameters('location')]",
      dependsOn: [
        "[resourceId('Microsoft.Web/connections', variables('analyseCustomer2DataverseConnectionName'))]",
        "[resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName'))]",
      ],
      properties: ordered({
        state: 'Enabled',
        definition:
          "[reference(resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName')), '2019-05-01').definition]",
        parameters: ordered({
          $connections: ordered({
            value: ordered({
              commondataservice: ordered({
                connectionId:
                  "[resourceId('Microsoft.Web/connections', variables('analyseCustomer2DataverseConnectionName'))]",
                connectionName: "[variables('analyseCustomer2DataverseConnectionName')]",
                id: "[variables('dataverseManagedApiId')]",
              }),
            }),
          }),
          dataverseBaseUrl: { value: "[parameters('dataverseBaseUrl')]" },
          dataverseTenantId: { value: "[parameters('dataverseTenantId')]" },
          dataverseClientId: { value: "[parameters('dataverseClientId')]" },
          dataverseClientSecret: { value: "[parameters('dataverseClientSecret')]" },
          openAiEndpoint: { value: "[parameters('openAiEndpoint')]" },
          openAiDeployment: { value: "[parameters('openAiDeployment')]" },
          openAiApiVersion: { value: "[parameters('openAiApiVersion')]" },
          openAiApiKey: { value: "[parameters('openAiApiKey')]" },
        }),
      }),
    }),

    ordered({
      type: 'Microsoft.Logic/workflows',
      apiVersion: '2019-05-01',
      name: "[parameters('analyseCustomerVersion2LogicAppName')]",
      location: "[parameters('location')]",
      dependsOn: [
        "[resourceId('Microsoft.Web/connections', variables('analyseCustomerVersion2DataverseConnectionName'))]",
        "[resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName'))]",
      ],
      properties: ordered({
        state: 'Enabled',
        definition: version2,
        parameters: ordered({
          $connections: ordered({
            value: ordered({
              commondataservice: ordered({
                connectionId:
                  "[resourceId('Microsoft.Web/connections', variables('analyseCustomerVersion2DataverseConnectionName'))]",
                connectionName: "[variables('analyseCustomerVersion2DataverseConnectionName')]",
                id: "[variables('dataverseManagedApiId')]",
              }),
            }),
          }),
          dataverseBaseUrl: { value: "[parameters('dataverseBaseUrl')]" },
          dataverseTenantId: { value: "[parameters('dataverseTenantId')]" },
          dataverseClientId: { value: "[parameters('dataverseClientId')]" },
          dataverseClientSecret: { value: "[parameters('dataverseClientSecret')]" },
          openAiEndpoint: { value: "[parameters('openAiEndpoint')]" },
          openAiDeployment: { value: "[parameters('openAiDeployment')]" },
          openAiApiVersion: { value: "[parameters('openAiApiVersion')]" },
          openAiApiKey: { value: "[parameters('openAiApiKey')]" },
        }),
      }),
    }),
  ];

  const template = ordered({
    $schema: 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#',
    contentVersion: '1.0.0.0',
    parameters,
    variables,
    resources,
    outputs: ordered({
      logicAppUrl: ordered({
        type: 'string',
        value:
          "[listCallbackURL(concat(resourceId('Microsoft.Logic/workflows', parameters('logicAppName')), '/triggers/manual'), '2019-05-01').value]",
      }),
      analyseCustomerVersion2Url: ordered({
        type: 'string',
        value:
          "[listCallbackURL(concat(resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerVersion2LogicAppName')), '/triggers/When_an_HTTP_request_is_received'), '2019-05-01').value]",
      }),
    }),
  });

  const outPath = path.join(__dirname, '..', 'templates', 'azuredeploy.json');
  fs.writeFileSync(outPath, JSON.stringify(template, null, 2) + '\n', 'utf8');
  console.log('WROTE templates/azuredeploy.json');
}

writeTemplate();
