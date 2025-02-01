from dataclasses import dataclass
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from prompts.system_instructions import PersonaPromptManager
from bson import ObjectId


@dataclass
class TestingSection:
    name: str
    subsections: List[str]
    evaluation_criteria: List[str]
    priority_level: str


@dataclass
class FeedbackStructure:
    sections: List[TestingSection]
    scoring_categories: List[str]
    assessment_requirements: List[str]


class Prompt:
    def __init__(self, mongo_uri: str, persona_id: ObjectId):
        self.persona_manager = PersonaPromptManager(mongo_uri)
        self.system_prompt = self.persona_manager.create_system_prompt(persona_id)

    def create_prompt_template(self) -> PromptTemplate:
        """Create the final prompt template with emphasis on objectivity"""
        prompt = f"""

        {self.system_prompt}

        tools: {{tools}}

        invoke the tools in this order
        1. crawl
        2. query_site_visually
        3. query_site_textually 
        4. analyze_heatmap
        5. generate_feedback
        6. check_for_feedback_reliability
        
        Use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{{tool_names}}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Remember:
        - Be honest about both positives AND negatives
        - Don't soften critical feedback
        - Stay true to persona's perspective
        - Use specific examples for all feedback
        - Base all assessments on persona characteristics
        - Consider real-world usage scenarios
        - Maintain objectivity throughout

        All responses(Thought, Action, Action Input, Observation, Final Answer) must begin on a new line.

        Begin!

        Question: {{input}}
        Thought: {{agent_scratchpad}}
        """

        return PromptTemplate.from_template(prompt)