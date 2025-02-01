from langchain_openai import AzureChatOpenAI
from langchain_anthropic import ChatAnthropic


import os
from dotenv import load_dotenv
from utils.const import azure_supported_models, anthropic_supported_models
from utils.common_utils import check_env_for_dependent_variables

# Load environment variables
load_dotenv()

# Define the LLM class
class LLM:
    def __init__(self, llm_id):
        self.llm_id = llm_id
        # Validate that required variables are set
        check_env_for_dependent_variables()

    def get_llm(self):
        if self.llm_id in azure_supported_models and not self.llm_id == "gpt-o1":
            self.llm_selected = AzureChatOpenAI(
                azure_endpoint=os.environ[f"azure_endpoint_{self.llm_id}"],
                api_key=os.environ[f"azure_api_key_{self.llm_id}"],
                azure_deployment=os.environ[f"azure_deployment_{self.llm_id}"],
                api_version=os.environ[f"azure_api_version_{self.llm_id}"],
                temperature=0.2,
                max_tokens=None,
                timeout=None,
                streaming=True,
                max_retries=5)

        elif self.llm_id == "gpt-o1-minilla":
            self.llm_selected = AzureChatOpenAI(
                azure_endpoint=os.environ[f"azure_endpoint_{self.llm_id}"],
                api_key=os.environ[f"azure_api_key_{self.llm_id}"],
                azure_deployment=os.environ[f"azure_deployment_{self.llm_id}"],
                api_version=os.environ[f"azure_api_version_{self.llm_id}"],
                temperature=1,
                streaming = True,
                max_tokens=None,
                timeout=None,
                max_retries=5)

        elif self.llm_id in anthropic_supported_models:
            self.llm_selected = ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                api_key=os.environ[f"anthropic_key_{self.llm_id}"],
                temperature=0.2,
                streaming=True,
                max_tokens=1024,
                timeout=None,
                max_retries=2,
            )
        return self.llm_selected