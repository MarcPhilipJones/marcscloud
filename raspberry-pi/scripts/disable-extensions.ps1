$disableList = @(
    "azurite.azurite",
    "bencoleman.armview",
    "danish-naglekar.dataverse-devtools",
    "danish-naglekar.pcf-builder",
    "dbaeumer.vscode-eslint",
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "microsoft-isvexptools.powerplatform-vscode",
    "ms-azuretools.vscode-azurefunctions",
    "ms-azuretools.vscode-azurelogicapps",
    "ms-azuretools.vscode-azureresourcegroups",
    "ms-azuretools.vscode-bicep",
    "ms-azuretools.vscode-containers",
    "ms-azuretools.vscode-docker",
    "ms-azuretools.vscode-logicapps",
    "ms-dotnettools.csdevkit",
    "ms-dotnettools.csharp",
    "ms-dotnettools.vscode-dotnet-runtime",
    "ms-sarifvscode.sarif-viewer",
    "ms-vscode.azure-account",
    "ms-vscode.azurecli",
    "njpwerner.autodocstring",
    "rangav.vscode-thunder-client",
    "anthropic.claude-code"
)

$workspace = "c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\raspberry-pi"

$args = @()
foreach ($ext in $disableList) {
    $args += "--disable-extension"
    $args += $ext
}

Write-Host "Relaunching VS Code with $($disableList.Count) extensions disabled for this workspace..."
& code $args $workspace
