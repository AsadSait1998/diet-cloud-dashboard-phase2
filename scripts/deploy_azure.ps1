[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]{4,12}$')]
    [string]$NameSuffix,
    [string]$ResourceGroup = 'diet-analysis-rg',
    [string]$Location = 'canadacentral',
    [string]$StaticWebAppLocation = 'centralus'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI is required. Install it, run az login, and rerun this script.'
}
$accountId = az account show --query id --output tsv 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($accountId)) {
    throw 'No active Azure CLI login. Run az login first.'
}

Write-Host "Creating resource group $ResourceGroup in $Location..."
az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) {
    throw "Could not create or access resource group $ResourceGroup. Review the Azure CLI error above."
}

Write-Host 'Deploying Blob Storage, Flex Consumption Function App, monitoring, and Static Web App...'
$deploymentJson = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file (Join-Path $projectRoot 'infra\main.bicep') `
    --parameters nameSuffix=$NameSuffix location=$Location staticWebAppLocation=$StaticWebAppLocation `
    --query properties.outputs `
    --output json
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($deploymentJson)) {
    throw 'Azure resource deployment failed. Review the deployment error above; later upload and publish steps were not run.'
}
$outputs = ($deploymentJson -join [Environment]::NewLine) | ConvertFrom-Json

$storageName = $outputs.storageAccountName.value
$functionName = $outputs.functionAppName.value
$functionApi = $outputs.functionApiBaseUrl.value
$staticName = $outputs.staticWebAppName.value
$staticUrl = $outputs.staticWebAppUrl.value
if ([string]::IsNullOrWhiteSpace($storageName) -or
    [string]::IsNullOrWhiteSpace($functionName) -or
    [string]::IsNullOrWhiteSpace($functionApi) -or
    [string]::IsNullOrWhiteSpace($staticName) -or
    [string]::IsNullOrWhiteSpace($staticUrl)) {
    throw 'Azure deployment completed without all required outputs. Stop here and review the deployment in Azure Portal.'
}
$storageConnection = az storage account show-connection-string --resource-group $ResourceGroup --name $storageName --query connectionString -o tsv
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($storageConnection)) {
    throw "Could not obtain the storage connection string for $storageName. The dataset was not uploaded."
}

Write-Host 'Uploading the Diets Dataset to the private datasets container...'
az storage blob upload `
    --connection-string $storageConnection `
    --container-name datasets `
    --name All_Diets.csv `
    --file (Join-Path $projectRoot 'data\All_Diets.csv') `
    --overwrite true `
    --content-type text/csv `
    --output none
if ($LASTEXITCODE -ne 0) {
    throw 'Dataset upload failed. Review the Azure CLI error above.'
}

if (Get-Command func -ErrorAction SilentlyContinue) {
    Write-Host "Publishing the Python Function App $functionName..."
    Push-Location (Join-Path $projectRoot 'backend')
    try {
        func azure functionapp publish $functionName --python
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Local Function publication failed for $functionName. The Azure resources and dataset are ready; use the included GitHub Actions workflow to deploy backend/."
        }
    }
    finally { Pop-Location }
} else {
    Write-Warning 'Azure Functions Core Tools was not found. Use the included GitHub Actions workflow to publish backend/.'
}

Write-Host ''
Write-Host 'Azure resources are ready.' -ForegroundColor Green
Write-Host "Function API: $functionApi/diet-insights"
Write-Host "Static Web App: $staticUrl"
Write-Host "Function App name (GitHub variable): $functionName"
Write-Host "Static Web App name: $staticName"
Write-Host ''
Write-Host 'Next: add the GitHub secrets described in docs/DEPLOYMENT_GUIDE.md and run both workflows.'
