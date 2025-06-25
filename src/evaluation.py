import os
import json
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_openai import AzureChatOpenAI
from openevals.llm import create_llm_as_judge
from openevals.prompts import CONCISENESS_PROMPT
from openevals.prompts import CORRECTNESS_PROMPT
from openevals.prompts import HALLUCINATION_PROMPT
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Load environment variables from .env
load_dotenv()

# Validate required environment variables
required_env_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_LLM_DEPLOYMENT",
    "AZURE_OPENAI_JUDGE_DEPLOYMENT",
    "AZURE_OPENAI_API_VERSION"
]

for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Required environment variable {var} is not set")

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

# Load system prompt from JSON file
def load_system_prompt():
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "llm.json")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    # Find the system prompt in the array
    for item in data:
        if item["name"] == "system_prompt":
            return {
                "role": item["role"],
                "content": item["prompt"]
            }
    raise ValueError("System prompt not found in llm.json")

# Load user prompt from JSON file
def load_user_prompt():
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "llm.json")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    # Find the user prompt in the array
    for item in data:
        if item["name"] == "user_prompt":
            return {
                "role": item["role"],
                "content": item["prompt"]
            }
    raise ValueError("User prompt not found in llm.json")

# Load reference outputs from JSON file
def load_reference_outputs():
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "llm.json")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    # Find the reference outputs in the array
    for item in data:
        if item["name"] == "reference_outputs":
            return item["content"]
    raise ValueError("Reference outputs not found in llm.json")

# Create a ChatOpenAI model
model = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    openai_api_type="azure_ad",
    azure_ad_token_provider=token_provider,
    max_tokens=300,
    temperature=0.5
)

# Create a judge ChatOpenAI model
judge_model = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_JUDGE_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    openai_api_type="azure_ad",
    azure_ad_token_provider=token_provider,
    max_tokens=300,
    temperature=0.5
)

# Invoke the model with a message
messages = [
    load_user_prompt(),
    load_system_prompt()
]

result = model.invoke(messages)

conciseness_evaluator = create_llm_as_judge(
    prompt=CONCISENESS_PROMPT,
    feedback_key="correctness",
    judge=judge_model,
    continuous=True
)

correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    judge=judge_model,
    continuous=True
)

hallucination_evaluator = create_llm_as_judge(
    prompt=HALLUCINATION_PROMPT,
    feedback_key="hallucination",
    judge=judge_model,
    continuous=True
)

reference_outputs = load_reference_outputs()


outputs = result.content
conciseness_eval_result = conciseness_evaluator(
    inputs=messages,
    outputs=outputs
)

correctness_eval_result = correctness_evaluator(
    inputs=messages,
    outputs=outputs,
    reference_outputs=reference_outputs
)

hallucination_eval_result = hallucination_evaluator(
    inputs=messages,
    outputs=outputs,
    context=reference_outputs,
    reference_outputs=reference_outputs
)


# Extract evaluation results
def extract_eval_results(eval_result, eval_type):
    """Extract score, key, and comments from evaluation result"""
    return {
        "type": eval_type,
        "score": eval_result.get("score"),
        "key": eval_result.get("key"),
        "comments": eval_result.get("comments"),
        "full_result": eval_result
    }

# Process all evaluation results
conciseness_result = extract_eval_results(conciseness_eval_result, "Conciseness")
correctness_result = extract_eval_results(correctness_eval_result, "Correctness")
hallucination_result = extract_eval_results(hallucination_eval_result, "Hallucination")

# Compile all results
evaluation_results = {
    "llm_output": str(outputs),
    "evaluations": {
        "conciseness": conciseness_result,
        "correctness": correctness_result,
        "hallucination": hallucination_result
    }
}

# Print detailed results
print("------------------------------")
print("LLM output: " + str(outputs))
print("------------------------------")

for eval_name, eval_data in evaluation_results["evaluations"].items():
    print(f"{eval_data['type']} Evaluation:")
    print(f"  Score: {eval_data['score']}")
    print(f"  Key: {eval_data['key']}")
    print(f"  Comments: {eval_data['comments']}")
    print(f"  Full Result: {eval_data['full_result']}")
    print("------------------------------")

# Create GitHub Actions summary format
def create_github_summary():
    """Create formatted summary for GitHub Actions"""
    summary_lines = [
        "# LLM Evaluation Results",
        "",
        f"**LLM Output:** {evaluation_results['llm_output'][:200]}{'...' if len(evaluation_results['llm_output']) > 200 else ''}",
        "",
        "## Evaluation Scores",
        "",
        "| Evaluation Type | Score | Key | Comments |",
        "|----------------|-------|-----|----------|"
    ]

    for eval_name, eval_data in evaluation_results["evaluations"].items():
        score = eval_data['score'] if eval_data['score'] is not None else "N/A"
        key = eval_data['key'] if eval_data['key'] is not None else "N/A"
        comments = eval_data['comments'][:100] if eval_data['comments'] else "N/A"
        if len(str(eval_data['comments'])) > 100:
            comments += "..."

        summary_lines.append(f"| {eval_data['type']} | {score} | {key} | {comments} |")

    return "\n".join(summary_lines)

# Generate and print GitHub summary
github_summary = create_github_summary()
print("\n" + "=" * 50)
print("GITHUB ACTIONS SUMMARY")
print("=" * 50)
print(github_summary)

# Export results as JSON for GitHub Actions
import json
results_json = json.dumps(evaluation_results, indent=2)
print("\n" + "=" * 50)
print("JSON RESULTS FOR GITHUB ACTIONS")
print("=" * 50)
print(results_json)
