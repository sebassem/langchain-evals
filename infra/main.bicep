targetScope = 'subscription'

param location string = 'swedencentral'
param infraResourceGroupName string = 'rg-ai-dev-${namingPrefix}'
param storageAccountName string = 'aistg${take(uniqueString(deployment().name,location,namingPrefix),5)}'
param namingPrefix string = take(newGuid(),5)
param models array
param deployAiSearch bool = false
param githubOrganization string = 'githubOrganization'
param githubRepo string = 'sampleRepository'

module infraResourceGroup 'br/public:avm/res/resources/resource-group:0.4.1' = {
  name: 'deployment-Infra-resourceGroup'
  params: {
    name: infraResourceGroupName
    location: location
  }
}


module storageAccount 'br/public:avm/res/storage/storage-account:0.18.1' = {
  scope: resourceGroup(infraResourceGroupName)
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
  scope: resourceGroup(infraResourceGroupName)
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

module aiSearchStorageAccountRoleAssignment 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = if(deployAiSearch) {
  name: 'deployment-ai-storage-account-role-assignment'
  scope: resourceGroup(infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  params: {
    principalId: userAssignedIdentity.outputs.principalId
    resourceId: storageAccount.outputs.resourceId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'ServicePrincipal'
  }
}

module userAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.0' = {
  scope: resourceGroup(infraResourceGroupName)
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
  scope: resourceGroup(infraResourceGroupName)
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
      userAssignedResourceIds: [
        userAssignedIdentity.outputs.resourceId
      ]
    }
    roleAssignments: deployAiSearch ? [
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
        principalType: 'ServicePrincipal'
      }
      {
        principalId: deployer().objectId
        roleDefinitionIdOrName: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
        description: 'Cognitive Services Account Contributor'
        principalType: 'User'
      }
    ] : [
      {
        principalId: deployer().objectId
        roleDefinitionIdOrName: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
        description: 'Cognitive Services Account Contributor'
        principalType: 'User'
      }
    ]
  }
}

module aiSearch 'br/public:avm/res/search/search-service:0.9.1' = if (deployAiSearch) {
  name: 'deployment-ai-search'
  scope: resourceGroup(infraResourceGroupName)
  dependsOn: [
    infraResourceGroup
  ]
  params: {
    name: 'search${take(uniqueString(deployment().name,location,namingPrefix),5)}'
    location: location
    managedIdentities: {
      userAssignedResourceIds: [
        userAssignedIdentity.outputs.resourceId
      ]
    }
    sku: 'standard'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    roleAssignments: [
          {
            principalId: userAssignedIdentity.outputs.principalId
            roleDefinitionIdOrName: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
            principalType: 'ServicePrincipal'
            description: 'Search Index Data Reader'
          }
          {
            principalId: userAssignedIdentity.outputs.principalId
            roleDefinitionIdOrName: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
            principalType: 'ServicePrincipal'
            description: 'Search Service Contributor'
          }
        ]
  }
}

output aiendpoint string = azureOpenAI.outputs.endpoint