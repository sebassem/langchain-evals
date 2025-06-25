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
    return {
        "role": data["role"],
        "content": data["prompt"]
    }

#OPENAI_API_KEY = SecretStr(os.getenv("AZURE_OPENAI_API_KEY", ""))

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
    {
        "role": "user",
        "content": "Who are the top players in foundational models?"
    },
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

reference_outputs = "The top players are OpenAI, Microsoft, Google DeepMind,Anthropic, Hugging face and Meta AI. There are many other players in the field, but these are the most prominent ones."


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


print("------------------------------")
print("LLM output: " + str(outputs))
print("------------------------------")
print("Conciseness Evaluation result: ")
score = conciseness_eval_result.get("score")
key = conciseness_eval_result.get("key")
comments = conciseness_eval_result.get("comments")
print(conciseness_eval_result)

print("------------------------------")
print("Correctness Evaluation result: ")
print(correctness_eval_result)
score = correctness_eval_result.get("score")
key = correctness_eval_result.get("key")
comments = correctness_eval_result.get("comments")

print("------------------------------")
print("Hallucination Evaluation result: ")
print(hallucination_eval_result)
score = hallucination_eval_result.get("score")
key = hallucination_eval_result.get("key")
comments = hallucination_eval_result.get("comments")
