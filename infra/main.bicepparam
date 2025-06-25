using './main.bicep'

param location = 'eastus2'
param githubOrganization = 'sebassem'
param githubRepo = 'langchain-evals'
param models = [
  {
    name: 'llm-deployment'
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
    sku: {
      capacity: 40
      name: 'GlobalStandard'
    }
  }
  {
    name: 'eval-judge-deployment'
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    sku: {
      capacity: 40
      name: 'GlobalStandard'
    }
  }
]

param deployAiSearch = false

