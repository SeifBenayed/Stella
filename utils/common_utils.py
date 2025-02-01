import re
import os
from utils.const import azure_supported_models, anthropic_supported_models
from langchain_core.messages import HumanMessage

def beautify(input_string):
    pattern = r"```python(.*?)```"
    # Find all matches
    matches = re.findall(pattern, input_string, re.DOTALL)
    for match in matches:
        return match

def check_env_for_dependent_variables():
    required_vars = [[f"azure_endpoint_{model}", f"azure_api_key_{model}",
                      f"azure_deployment_{model}", f"azure_api_version_{model}"] for model in azure_supported_models]
    required_vars.extend([[f"anthropic_key_{model}"] for model in anthropic_supported_models])
    required_vars = sum(required_vars, [])

    for var in required_vars:
        if os.getenv(var) is None:
            raise ValueError(f"Environment variable {var} is missing")


def anthropic_payload_gen_text_only(query):
    messages = [
        HumanMessage(
            content=
            [
                {"type": "text", "text": query},
            ],
        )
    ]
    return messages
