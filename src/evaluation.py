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

# Define evaluation thresholds (configurable via environment variables)
EVALUATION_THRESHOLDS = {
    "conciseness": float(os.getenv("CONCISENESS_THRESHOLD", "0.7")),  # Default: 70%
    "correctness": float(os.getenv("CORRECTNESS_THRESHOLD", "0.8")),  # Default: 80%
    "hallucination": float(os.getenv("HALLUCINATION_THRESHOLD", "0.9"))  # Default: 90% (higher is better for hallucination)
}

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
        "comments": eval_result.get("comment"),
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

# Print detailed results for debugging
print("------------------------------")
print("LLM output: " + str(outputs))
print("------------------------------")

for eval_name, eval_data in evaluation_results["evaluations"].items():
    print(f"{eval_data['type']} Evaluation:")
    print(f"  Score: {eval_data['score']}")
    print(f"  Key: {eval_data['key']}")
    print(f"  Comments: {eval_data['comments']}")
    print("------------------------------")

# Check if any evaluation result is below the threshold
for eval_name, eval_data in evaluation_results["evaluations"].items():
    threshold = EVALUATION_THRESHOLDS.get(eval_name)
    if threshold is not None and eval_data["score"] < threshold:
        print(f"Warning: {eval_data['type']} score {eval_data['score']} is below the threshold {threshold}")

# Save results as JSON file for GitHub Actions
import json
with open('evaluation_results.json', 'w') as f:
    json.dump(evaluation_results, f, indent=2)

print("Results saved to evaluation_results.json")

# Check evaluation thresholds and determine if they pass
def check_thresholds(evaluation_results, thresholds):
    """Check if evaluation scores meet minimum thresholds"""
    threshold_results = {}
    overall_pass = True

    for eval_type, threshold in thresholds.items():
        eval_data = evaluation_results["evaluations"].get(eval_type)
        if eval_data and eval_data["score"] is not None:
            score = float(eval_data["score"])
            passed = score >= threshold
            threshold_results[eval_type] = {
                "score": score,
                "threshold": threshold,
                "passed": passed,
                "difference": score - threshold
            }
            if not passed:
                overall_pass = False
        else:
            # If score is missing, consider it a failure
            threshold_results[eval_type] = {
                "score": None,
                "threshold": threshold,
                "passed": False,
                "difference": None
            }
            overall_pass = False

    return threshold_results, overall_pass

# Perform threshold checking
threshold_results, overall_pass = check_thresholds(evaluation_results, EVALUATION_THRESHOLDS)

# Add threshold results to the evaluation results
evaluation_results["threshold_check"] = {
    "overall_pass": overall_pass,
    "thresholds": EVALUATION_THRESHOLDS,
    "results": threshold_results
}

# Update the JSON file with threshold results
with open('evaluation_results.json', 'w') as f:
    json.dump(evaluation_results, f, indent=2)

# Print threshold check results
print("::group::Threshold Check Results")
print(f"Overall Pass: {overall_pass}")
for eval_type, result in threshold_results.items():
    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"{eval_type}: {status} (Score: {result['score']}, Threshold: {result['threshold']})")
print("::endgroup::")

# Exit with appropriate code for CI/CD
if not overall_pass:
    print("::error::❌ Evaluation thresholds not met! Check the results above.")
    exit(1)
else:
    print("::notice::✅ All evaluation thresholds met!")

# Also output the JSON to stdout for direct consumption
print("::group::Evaluation Results JSON")
print(json.dumps(evaluation_results, indent=2))
print("::endgroup::")
