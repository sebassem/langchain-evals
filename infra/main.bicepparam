using './main.bicep'

param githubOrganization = 'sebassem'
param githubRepo = 'langchain-evals'
param subscriptionId = '2d68328e-bde2-4aeb-a5b4-1a11b4328961'
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
