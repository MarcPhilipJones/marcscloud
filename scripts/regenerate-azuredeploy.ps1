$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$ccas = Get-Content -Raw -Path 'workflows/CCASGetConversation.json' | ConvertFrom-Json -Depth 200
$analyse = Get-Content -Raw -Path 'workflows/AnalyseCustomer.json' | ConvertFrom-Json -Depth 200
$version2 = Get-Content -Raw -Path 'workflows/AnalyseCustomerVersion2.json' | ConvertFrom-Json -Depth 200

$parameters = [ordered]@{
  logicAppName = [ordered]@{ type = 'string'; metadata = [ordered]@{ description = 'Name of the Logic App' } }
  analyseCustomerLogicAppName = [ordered]@{ type = 'string'; defaultValue = 'AnalyseCustomer'; metadata = [ordered]@{ description = 'Name of the AnalyseCustomer Logic App' } }
  analyseCustomer2LogicAppName = [ordered]@{ type = 'string'; defaultValue = 'AnalyseCustomer2'; metadata = [ordered]@{ description = 'Name of the AnalyseCustomer2 Logic App' } }
  analyseCustomerVersion2LogicAppName = [ordered]@{ type = 'string'; defaultValue = 'AnalyseCustomerVersion2'; metadata = [ordered]@{ description = 'Name of the AnalyseCustomerVersion2 Logic App' } }
  location = [ordered]@{ type = 'string'; defaultValue = '[resourceGroup().location]'; metadata = [ordered]@{ description = 'Location for all resources' } }

  dataverseBaseUrl = [ordered]@{ type = 'string'; metadata = [ordered]@{ description = 'Base URL of the Dataverse environment, e.g. https://<org>.crm4.dynamics.com' } }
  dataverseTenantId = [ordered]@{ type = 'string'; metadata = [ordered]@{ description = 'Azure AD Tenant ID' } }
  dataverseClientId = [ordered]@{ type = 'string'; metadata = [ordered]@{ description = 'Application (client) ID' } }
  dataverseClientSecret = [ordered]@{ type = 'securestring'; metadata = [ordered]@{ description = 'Client secret for the app registration' } }

  openAiEndpoint = [ordered]@{ type = 'string'; defaultValue = 'https://mjopenai2.openai.azure.com/'; metadata = [ordered]@{ description = 'Azure OpenAI endpoint, e.g. https://<resource>.openai.azure.com/' } }
  openAiDeployment = [ordered]@{ type = 'string'; defaultValue = 'gpt-4o'; metadata = [ordered]@{ description = 'Azure OpenAI deployment name' } }
  openAiApiVersion = [ordered]@{ type = 'string'; defaultValue = '2024-10-21'; metadata = [ordered]@{ description = 'Azure OpenAI API version' } }
  openAiApiKey = [ordered]@{ type = 'securestring'; metadata = [ordered]@{ description = 'Azure OpenAI API key' } }
}

$variables = [ordered]@{
  logicAppDataverseConnectionName = "[concat(parameters('logicAppName'), '-dataverse')]"
  analyseCustomerDataverseConnectionName = "[concat(parameters('analyseCustomerLogicAppName'), '-dataverse')]"
  analyseCustomer2DataverseConnectionName = "[concat(parameters('analyseCustomer2LogicAppName'), '-dataverse')]"
  analyseCustomerVersion2DataverseConnectionName = "[concat(parameters('analyseCustomerVersion2LogicAppName'), '-dataverse')]"
  dataverseManagedApiId = "[concat(subscription().id, '/providers/Microsoft.Web/locations/', parameters('location'), '/managedApis/commondataservice')]"
}

function New-DvConnectionResource([string]$nameExpr, [string]$displayNameExpr) {
  return [ordered]@{
    type = 'Microsoft.Web/connections'
    apiVersion = '2016-06-01'
    name = $nameExpr
    location = "[parameters('location')]"
    properties = [ordered]@{
      displayName = $displayNameExpr
      api = [ordered]@{ id = "[variables('dataverseManagedApiId')]" }
      parameterValues = [ordered]@{
        'token:TenantId' = "[parameters('dataverseTenantId')]"
        'token:clientId' = "[parameters('dataverseClientId')]"
        'token:clientSecret' = "[parameters('dataverseClientSecret')]"
        'token:grantType' = 'client_credentials'
        'token:resourceUri' = "[parameters('dataverseBaseUrl')]"
      }
    }
  }
}

$resources = @(
  (New-DvConnectionResource "[variables('logicAppDataverseConnectionName')]" "[concat(parameters('logicAppName'), ' Dataverse')]"),
  (New-DvConnectionResource "[variables('analyseCustomerDataverseConnectionName')]" "[concat(parameters('analyseCustomerLogicAppName'), ' Dataverse')]"),
  (New-DvConnectionResource "[variables('analyseCustomer2DataverseConnectionName')]" "[concat(parameters('analyseCustomer2LogicAppName'), ' Dataverse')]"),
  (New-DvConnectionResource "[variables('analyseCustomerVersion2DataverseConnectionName')]" "[concat(parameters('analyseCustomerVersion2LogicAppName'), ' Dataverse')]"),

  ([ordered]@{
    type = 'Microsoft.Logic/workflows'
    apiVersion = '2019-05-01'
    name = "[parameters('logicAppName')]"
    location = "[parameters('location')]"
    dependsOn = @(
      "[resourceId('Microsoft.Web/connections', variables('logicAppDataverseConnectionName'))]"
    )
    properties = [ordered]@{
      state = 'Enabled'
      definition = $ccas
      parameters = [ordered]@{
        '$connections' = [ordered]@{
          value = [ordered]@{
            commondataservice = [ordered]@{
              connectionId = "[resourceId('Microsoft.Web/connections', variables('logicAppDataverseConnectionName'))]"
              connectionName = "[variables('logicAppDataverseConnectionName')]"
              id = "[variables('dataverseManagedApiId')]"
            }
          }
        }
        dataverseBaseUrl = [ordered]@{ value = "[parameters('dataverseBaseUrl')]" }
        dataverseTenantId = [ordered]@{ value = "[parameters('dataverseTenantId')]" }
        dataverseClientId = [ordered]@{ value = "[parameters('dataverseClientId')]" }
        dataverseClientSecret = [ordered]@{ value = "[parameters('dataverseClientSecret')]" }
      }
    }
  }),

  ([ordered]@{
    type = 'Microsoft.Logic/workflows'
    apiVersion = '2019-05-01'
    name = "[parameters('analyseCustomerLogicAppName')]"
    location = "[parameters('location')]"
    dependsOn = @(
      "[resourceId('Microsoft.Web/connections', variables('analyseCustomerDataverseConnectionName'))]"
    )
    properties = [ordered]@{
      state = 'Enabled'
      definition = $analyse
      parameters = [ordered]@{
        '$connections' = [ordered]@{
          value = [ordered]@{
            commondataservice = [ordered]@{
              connectionId = "[resourceId('Microsoft.Web/connections', variables('analyseCustomerDataverseConnectionName'))]"
              connectionName = "[variables('analyseCustomerDataverseConnectionName')]"
              id = "[variables('dataverseManagedApiId')]"
            }
          }
        }
        dataverseBaseUrl = [ordered]@{ value = "[parameters('dataverseBaseUrl')]" }
        dataverseTenantId = [ordered]@{ value = "[parameters('dataverseTenantId')]" }
        dataverseClientId = [ordered]@{ value = "[parameters('dataverseClientId')]" }
        dataverseClientSecret = [ordered]@{ value = "[parameters('dataverseClientSecret')]" }
        openAiEndpoint = [ordered]@{ value = "[parameters('openAiEndpoint')]" }
        openAiDeployment = [ordered]@{ value = "[parameters('openAiDeployment')]" }
        openAiApiVersion = [ordered]@{ value = "[parameters('openAiApiVersion')]" }
        openAiApiKey = [ordered]@{ value = "[parameters('openAiApiKey')]" }
      }
    }
  }),

  ([ordered]@{
    type = 'Microsoft.Logic/workflows'
    apiVersion = '2019-05-01'
    name = "[parameters('analyseCustomer2LogicAppName')]"
    location = "[parameters('location')]"
    dependsOn = @(
      "[resourceId('Microsoft.Web/connections', variables('analyseCustomer2DataverseConnectionName'))]",
      "[resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName'))]"
    )
    properties = [ordered]@{
      state = 'Enabled'
      definition = "[reference(resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName')), '2019-05-01').definition]"
      parameters = [ordered]@{
        '$connections' = [ordered]@{
          value = [ordered]@{
            commondataservice = [ordered]@{
              connectionId = "[resourceId('Microsoft.Web/connections', variables('analyseCustomer2DataverseConnectionName'))]"
              connectionName = "[variables('analyseCustomer2DataverseConnectionName')]"
              id = "[variables('dataverseManagedApiId')]"
            }
          }
        }
        dataverseBaseUrl = [ordered]@{ value = "[parameters('dataverseBaseUrl')]" }
        dataverseTenantId = [ordered]@{ value = "[parameters('dataverseTenantId')]" }
        dataverseClientId = [ordered]@{ value = "[parameters('dataverseClientId')]" }
        dataverseClientSecret = [ordered]@{ value = "[parameters('dataverseClientSecret')]" }
        openAiEndpoint = [ordered]@{ value = "[parameters('openAiEndpoint')]" }
        openAiDeployment = [ordered]@{ value = "[parameters('openAiDeployment')]" }
        openAiApiVersion = [ordered]@{ value = "[parameters('openAiApiVersion')]" }
        openAiApiKey = [ordered]@{ value = "[parameters('openAiApiKey')]" }
      }
    }
  }),

  ([ordered]@{
    type = 'Microsoft.Logic/workflows'
    apiVersion = '2019-05-01'
    name = "[parameters('analyseCustomerVersion2LogicAppName')]"
    location = "[parameters('location')]"
    dependsOn = @(
      "[resourceId('Microsoft.Web/connections', variables('analyseCustomerVersion2DataverseConnectionName'))]",
      "[resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerLogicAppName'))]"
    )
    properties = [ordered]@{
      state = 'Enabled'
      definition = $version2
      parameters = [ordered]@{
        '$connections' = [ordered]@{
          value = [ordered]@{
            commondataservice = [ordered]@{
              connectionId = "[resourceId('Microsoft.Web/connections', variables('analyseCustomerVersion2DataverseConnectionName'))]"
              connectionName = "[variables('analyseCustomerVersion2DataverseConnectionName')]"
              id = "[variables('dataverseManagedApiId')]"
            }
          }
        }
        dataverseBaseUrl = [ordered]@{ value = "[parameters('dataverseBaseUrl')]" }
        dataverseTenantId = [ordered]@{ value = "[parameters('dataverseTenantId')]" }
        dataverseClientId = [ordered]@{ value = "[parameters('dataverseClientId')]" }
        dataverseClientSecret = [ordered]@{ value = "[parameters('dataverseClientSecret')]" }
        openAiEndpoint = [ordered]@{ value = "[parameters('openAiEndpoint')]" }
        openAiDeployment = [ordered]@{ value = "[parameters('openAiDeployment')]" }
        openAiApiVersion = [ordered]@{ value = "[parameters('openAiApiVersion')]" }
        openAiApiKey = [ordered]@{ value = "[parameters('openAiApiKey')]" }
      }
    }
  })
)

$template = [ordered]@{
  '$schema' = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
  contentVersion = '1.0.0.0'
  parameters = $parameters
  variables = $variables
  resources = $resources
  outputs = [ordered]@{
    logicAppUrl = [ordered]@{
      type = 'string'
      value = "[listCallbackURL(concat(resourceId('Microsoft.Logic/workflows', parameters('logicAppName')), '/triggers/manual'), '2019-05-01').value]"
    }
    analyseCustomerVersion2Url = [ordered]@{
      type = 'string'
      value = "[listCallbackURL(concat(resourceId('Microsoft.Logic/workflows', parameters('analyseCustomerVersion2LogicAppName')), '/triggers/When_an_HTTP_request_is_received'), '2019-05-01').value]"
    }
  }
}

$template | ConvertTo-Json -Depth 200 | Set-Content -Path 'templates/azuredeploy.json' -Encoding utf8
Write-Host 'WROTE templates/azuredeploy.json'
