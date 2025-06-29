# LangChain Evaluations Framework demo

A demonstration of a simple evaluation framework for Large Language Models (LLMs) using LangChain and Azure OpenAI, with automated quality assessment through AI judges.

## 🚀 Overview

This project provides a framework for evaluating LLM responses across three critical dimensions:

- **Conciseness**: How direct and to-the-point the response is
- **Correctness**: How accurate the response is compared to reference outputs
- **Hallucination**: How much the response contains fabricated or unsupported information

## 🏗️ Architecture

The project consists of:

- **Evaluation Engine**: Python-based evaluation system using LangChain and OpenEvals
- **Azure Infrastructure**: Bicep templates for deploying Azure OpenAI resources
- **Configuration Data**: JSON-based prompt and threshold management
- **CI/CD Ready**: Exit codes and JSON outputs for integration with GitHub Actions

## 📁 Project Structure

```python
├── data/
│   └── llm.json              # Prompts, reference outputs, and thresholds
├── infra/
│   ├── main.bicep            # Azure infrastructure definition
│   └── main.bicepparam       # Infrastructure parameters
├── src/
│   ├── evaluation.py         # Main evaluation script
│   └── requirements.txt      # Python dependencies
└── README.md                 # This file
```

## ⚙️ Setup

### Prerequisites

- Python 3.8+
- Azure subscription
- Azure OpenAI resource with GPT-4 models
- Azure CLI (for infrastructure deployment)

### 1. Install Dependencies

```bash
cd src
pip install -r requirements.txt
```

### 2. Deploy Azure Infrastructure

```bash
cd infra
az deployment mg create \
  --management-group-id <your-management-group-id> \
  --location eastus2 \
  --template-file main.bicep \
  --parameters main.bicepparam
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_LLM_DEPLOYMENT=llm-deployment
AZURE_OPENAI_JUDGE_DEPLOYMENT=eval-judge-deployment
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional: Override evaluation thresholds
CONCISENESS_THRESHOLD=0.7
CORRECTNESS_THRESHOLD=0.8
HALLUCINATION_THRESHOLD=0.7
```

## 🎯 Usage

### Basic Evaluation

Run the evaluation script:

```bash
cd src
python evaluation.py
```

The script will:

1. Load prompts and configuration from `data/llm.json`
2. Generate a response using the configured LLM
3. Evaluate the response using AI judges
4. Output detailed results and save to `evaluation_results.json`
5. Exit with code 0 (success) or 1 (failure) based on thresholds

### Customizing Evaluations

Edit `data/llm.json` to modify:

- **System and user prompts**: Change the `prompt` field
- **Reference outputs**: Update the `content` field for comparison
- **Evaluation thresholds**: Adjust minimum acceptable scores

Example threshold configuration:

```json
{
  "name": "evaluation_thresholds",
  "content": {
    "conciseness": 0.7,     # Minimum conciseness score (0-1)
    "correctness": 0.8,     # Minimum correctness score (0-1)
    "hallucination": 0.7    # Maximum hallucination tolerance (0-1)
  }
}
```

## 📊 Output Format

The evaluation produces a JSON file with:

```json
{
  "llm_output": "The actual LLM response",
  "evaluations": {
    "conciseness": {
      "type": "Conciseness",
      "score": 0.85,
      "comments": "Response is well-structured and direct"
    },
    "correctness": {
      "type": "Correctness",
      "score": 0.92,
      "comments": "Accurate information with good coverage"
    },
    "hallucination": {
      "type": "Hallucination",
      "score": 0.05,
      "comments": "No fabricated information detected"
    }
  },
  "threshold_check": {
    "overall_pass": true,
    "thresholds": {...},
    "results": {...}
  }
}
```

## 🔧 Configuration

### Azure OpenAI Models

The infrastructure deploys two model deployments:

- **LLM Deployment** (`gpt-4o-mini`): For generating responses
- **Judge Deployment** (`gpt-4.1-mini`): For evaluating responses

### Evaluation Criteria

| Metric | Description | Scoring |
|--------|-------------|---------|
| **Conciseness** | Measures directness and brevity | 0.0 (verbose) - 1.0 (concise) |
| **Correctness** | Compares against reference outputs | 0.0 (incorrect) - 1.0 (accurate) |
| **Hallucination** | Detects fabricated information | 0.0 (no hallucination) - 1.0 (high hallucination) |

## 🔐 Security & Authentication

The framework uses Azure Managed Identity for secure authentication:

- **User-Assigned Managed Identity** for service-to-service authentication
- **Azure AD Token Provider** for seamless credential management
- **Federated Identity Credentials** for GitHub Actions integration

## 🚀 CI/CD Integration

The evaluation script is designed for CI/CD pipelines:

- **Exit Codes**: 0 for success, 1 for threshold failures
- **JSON Output**: Structured results for further processing
- **GitHub Actions Ready**: Pre-configured with OIDC authentication

---

Built with ❤️ using LangChain, Azure OpenAI, and OpenEvals
