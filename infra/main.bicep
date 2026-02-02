// main.bicep
// Minimal, portfolio-friendly deployment. Expand as needed.

param location string = resourceGroup().location
param prefix string = 'gy-scm'
param environment string = 'dev'

var storageName = toLower('${replace(prefix, '-', '')}${environment}${uniqueString(resourceGroup().id)}')
var adfName = '${prefix}-adf-${environment}'
var kvName = toLower('${replace(prefix, '-', '')}-kv-${environment}-${uniqueString(resourceGroup().id)}')
var laName = '${prefix}-la-${environment}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    isHnsEnabled: true // ADLS Gen2
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: adfName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {}
}

resource kv 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { name: 'standard' family: 'A' }
    accessPolicies: []
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    publicNetworkAccess: 'Enabled'
  }
}

resource la 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: laName
  location: location
  properties: {
    retentionInDays: 30
  }
}

output storageAccountName string = storage.name
output dataFactoryName string = adf.name
output keyVaultName string = kv.name
output logAnalyticsName string = la.name
