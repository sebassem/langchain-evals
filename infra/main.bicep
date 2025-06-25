targetScope = 'managementGroup'

param location string = 'swedencentral'
param infraResourceGroupName string = 'rg-ai-dev-${namingPrefix}'
param storageAccountName string = 'aistg${take(uniqueString(deployment().name,location,namingPrefix),5)}'
param namingPrefix string = take(newGuid(),5)
param models array
param githubOrganization string = 'githubOrganization'
param githubRepo string = 'sampleRepository'
param subscriptionId string

module infraResourceGroup 'br/public:avm/res/resources/resource-group:0.4.1' = {
  name: 'deployment-Infra-resourceGroup'
  scope: subscription(subscriptionId)
  params: {
    name: infraResourceGroupName
    location: location
  }
}

module umiRoleAssignment 'br/public:avm/ptn/authorization/role-assignment:0.2.2' = {
  params: {
    principalId: userAssignedIdentity.outputs.principalId
    subscriptionId: subscriptionId
    resourceGroupName: infraResourceGroupName
    principalType: 'ServicePrincipal'
    roleDefinitionIdOrName: 'Contributor'
  }
}

module storageAccount 'br/public:avm/res/storage/storage-account:0.18.1' = {
  scope: resourceGroup(subscriptionId,infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  name: 'deployment-storage-account'
  params: {
    name: storageAccountName
    location: location
    accessTier: 'Cold'
    allowBlobPublicAccess: true
    kind: 'BlobStorage'
    skuName: 'Standard_LRS'
    blobServices: {
      containers: [
        {
          name: 'data'
          publicAccess: 'None'
        }
      ]
    }
  }
}

module storageAccountRoleAssignment 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = {
  name: 'deployment-storage-account-role-assignment'
    scope: resourceGroup(subscriptionId,infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  params: {
    principalId: deployer().objectId
    resourceId: storageAccount.outputs.resourceId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'User'
  }
}
module userAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.0' = {
    scope: resourceGroup(subscriptionId,infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  name: 'deployment-user-assigned-identity'
  params: {
    name: 'msi-ai-001'
    federatedIdentityCredentials: [
      {
        name: 'github_OIDC'
        audiences: [
              'api://AzureADTokenExchange'
            ]
            issuer: 'https://token.actions.githubusercontent.com'
            subject: 'repo:${githubOrganization}/${githubRepo}:ref:refs/heads/main'
      }
    ]
  }
}

module azureOpenAI 'br/public:avm/res/cognitive-services/account:0.11.0' = {
  name: 'deployment-azure-openai'
    scope: resourceGroup(subscriptionId,infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  params: {
    name: 'openai${take(uniqueString(deployment().name,location,namingPrefix),5)}'
    kind: 'OpenAI'
    location: location
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    networkAcls: {
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    sku: 'S0'
    deployments: models
    managedIdentities: {
      systemAssigned: true
    }
    roleAssignments:[
      {
        principalId: deployer().objectId
        roleDefinitionIdOrName: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
        description: 'Cognitive Services Account Contributor'
        principalType: 'User'
      }
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
        description: 'Cognitive Services Account Contributor'
        principalType: 'User'
      }
    ]
  }
}

output aiendpoint string = azureOpenAI.outputs.endpoint