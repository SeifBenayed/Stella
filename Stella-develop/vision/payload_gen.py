import os
from utils.const import azure_supported_models, anthropic_supported_models
from langchain_core.messages import HumanMessage


class CreateVisionPayload:
    def __init__(self, lch, system_instructions, query, image_path):
        self.system_instructions = system_instructions
        self.query = query
        self.llm_id = os.getenv("llm_id")
        self.base64_image = lch.encode_image(image_path)
        self.message = []
        # self.system_instructions = "you are an expert in generating UAT test cases"

    def create_azure_vision_payload(self):
        self.message = [
            {"role": "system", "content": self.system_instructions},
            {"role": "user", "content": [
                {"type": "text", "text": self.query},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{self.base64_image}"}
                 }
            ]}
        ]

    def create_claude_vision_payload(self):
        self.message = [
            HumanMessage(
                content=
                [
                    {"type": "text", "text": self.system_instructions},
                    {"type": "text", "text": self.query},
                    {
                        "type": "image_url",
                        "image_url":
                            {
                                "url": f"data:image/png;base64,{self.base64_image}"
                            },
                    },
                ],
            )
        ]

    def get_message(self):
        if self.llm_id in anthropic_supported_models:
            self.create_azure_vision_payload()
            return self.message
        if self.llm_id in azure_supported_models:
            self.create_azure_vision_payload()
            return self.message