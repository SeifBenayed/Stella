from typing import Dict, Any, List, Literal
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate



@dataclass
class PersonaMapReduceChain:
    persona_data: Dict[str, Any]

    def create_persona_map_prompt(self) -> ChatPromptTemplate:
        """Create persona-specific map prompt"""
        return ChatPromptTemplate.from_messages([
            ("system", f"""
            Analyze this content from {self.persona_data['name']}'s perspective:
            - Decision Style: {self.persona_data['consumption']['process']['decisionStyle']}
            - Expected Features: {', '.join(self.persona_data['ux']['expectedFeatures'])}

            Extract relevant information about:
            - First impression
            - Business value indicators
            - Professional features
            - Efficiency elements
            - Mobile functionality
            - Purchase Decision

            Content to analyze:
            {{context}}
            """)
        ])

    def create_persona_reduce_prompt(self) -> ChatPromptTemplate:
        """Create persona-specific reduce prompt"""
        return ChatPromptTemplate.from_messages([
            ("system", f"""
            Synthesize the findings for {self.persona_data['name']}, a {self.persona_data['type']}.

            Consider their:
            - Needs: {', '.join(self.persona_data['nmb']['needs'])}
            - Barriers: {', '.join(self.persona_data['nmb']['barriers'])}
            - Communication Style: {self.persona_data['communication']['communicationStyle']}

            Previous analyses:
            {{documents}}
            """)
        ])
