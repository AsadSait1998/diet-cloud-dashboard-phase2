@description('Azure region for the Function App and storage resources.')
param location string = resourceGroup().location

@description('Azure Static Web Apps region.')
param staticWebAppLocation string = 'centralus'

@description('Short lowercase suffix that makes public resource names globally unique.')
@minLength(4)
@maxLength(12)
param nameSuffix string

param namePrefix string = 'dietdash'

var token = toLower(replace('${namePrefix}${nameSuffix}', '-', ''))
var storageName = take('${token}store', 24)
var functionName = take('${token}-func', 60)
var staticSiteName = take('${token}-web', 60)
var planName = take('${token}-flex', 60)
var workspaceName = take('${token}-logs', 63)
var insightsName = take('${token}-insights', 255)
var deploymentContainerName = 'function-releases'
var datasetContainerName = 'datasets'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource deploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: deploymentContainerName
  properties: { publicAccess: 'None' }
}

resource datasetContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: datasetContainerName
  properties: { publicAccess: 'None' }
}

resource logWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    retentionInDays: 30
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: insightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logWorkspace.id
  }
}

resource flexPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  kind: 'functionapp'
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  properties: { reserved: true }
}

resource staticSite 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticSiteName
  location: staticWebAppLocation
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

var storageKey = storage.listKeys().keys[0].value
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageKey}'
var frontendOrigin = 'https://${staticSite.properties.defaultHostname}'

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: flexPlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      cors: {
        allowedOrigins: [frontendOrigin]
        supportCredentials: false
      }
      appSettings: [
        { name: 'AzureWebJobsStorage', value: storageConnectionString }
        { name: 'DEPLOYMENT_STORAGE_CONNECTION_STRING', value: storageConnectionString }
        { name: 'DIET_STORAGE_CONNECTION_STRING', value: storageConnectionString }
        { name: 'DATA_CONTAINER_NAME', value: datasetContainerName }
        { name: 'DATA_BLOB_NAME', value: 'All_Diets.csv' }
        { name: 'CACHE_TTL_SECONDS', value: '300' }
        { name: 'CORS_ALLOWED_ORIGIN', value: frontendOrigin }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
      ]
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}${deploymentContainerName}'
          authentication: {
            type: 'StorageAccountConnectionString'
            storageAccountConnectionStringName: 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
          }
        }
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 40
        instanceMemoryMB: 2048
      }
    }
  }
  dependsOn: [deploymentContainer, datasetContainer]
}

output functionAppName string = functionApp.name
output functionApiBaseUrl string = 'https://${functionApp.properties.defaultHostName}/api'
output staticWebAppName string = staticSite.name
output staticWebAppUrl string = frontendOrigin
output storageAccountName string = storage.name
output resourceGroupName string = resourceGroup().name
