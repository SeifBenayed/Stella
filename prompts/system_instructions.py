from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import datetime


class TestingPhase(Enum):
    INITIAL_SCAN = "initial_scan"
    VISUAL_ASSESSMENT = "visual_assessment"
    FUNCTIONAL_EVALUATION = "functional_evaluation"
    JOURNEY_MAPPING = "journey_mapping"
    FEEDBACK_SYNTHESIS = "feedback_synthesis"


@dataclass
class TestingProtocol:
    phase: TestingPhase
    actions: List[str]
    evaluation_criteria: List[str]
    persona_alignment: List[str]


class PersonaPromptManager:
    def __init__(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client['stella_main']
        self.testing_protocols = self._initialize_testing_protocols()


    def get_persona(self, persona_id: ObjectId) -> Dict[str, Any]:
        """Fetch persona from MongoDB"""
        return self.db['personas'].find_one({"_id": persona_id})

    def _initialize_testing_protocols(self) -> Dict[TestingPhase, TestingProtocol]:
        """Initialize structured testing protocols for each phase"""
        return {
            TestingPhase.INITIAL_SCAN: TestingProtocol(
                phase=TestingPhase.INITIAL_SCAN,
                actions=[
                    "Analyze site architecture",
                    "Document first impressions",
                    "Identify key elements"
                ],
                evaluation_criteria=[
                    "Initial clarity",
                    "Visual hierarchy",
                    "Navigation structure"
                ],
                persona_alignment=[
                    "Style preferences",
                    "Expected features",
                    "Common pain points"
                ]
            ),
            # Add other phases similarly
        }

    def format_persona_context(self, persona: Dict[str, Any]) -> str:
        """Enhanced persona context formatting with structured sections"""

        return f"""
        PERSONA EMBODIMENT INSTRUCTIONS
        ==============================

        1. CORE IDENTITY & CONTEXT
        -------------------------
        Name: {persona['name']}
        Archetype: {persona['type']}
        Background: {persona['profile']['occupation']} based in {persona['profile']['location']}
        Income Level: {persona['profile'].get('income', {}).get('range', 'Not specified')}

        2. DIGITAL BEHAVIOR PROFILE
        -------------------------
        Primary Device: {persona['digital']['devices']['primary']}
        Usage Pattern: {persona['digital']['dailyOnlineHours']} hours daily
        Platform Preferences: {', '.join(persona['digital']['preferredPlatforms'])}
        Technical Proficiency: {persona['digital'].get('techLevel', 'Moderate')}

        3. INTERACTION PREFERENCES
        ------------------------
        Visual Preferences:
        - Style: {persona['ux']['visualStyle']['designStyle']}
        - Colors: {', '.join(persona['ux']['visualStyle']['preferredColors'])}
        - Typography: {persona['ux']['visualStyle'].get('typography', 'Standard')}

        Navigation Expectations:
        - Pattern: {persona['ux']['navigation']['preferredPattern']}
        - Mobile Priority: {'Yes' if persona['ux']['navigation']['mobilePriority'] else 'No'}
        - Key Features: {', '.join(persona['ux']['expectedFeatures'])}

        4. DECISION-MAKING FRAMEWORK
        --------------------------
        Style: {persona['consumption']['process']['decisionStyle']}
        Key Criteria: {', '.join(persona['consumption']['decisionCriteria'])}
        Typical Decision Time: {persona['consumption']['process']['averageDecisionTime']} hours

        5. PSYCHOLOGICAL PROFILE
        ----------------------
        Needs: {', '.join(persona['nmb']['needs'])}
        Motivations: {', '.join(persona['nmb']['motivations'])}
        Barriers: {', '.join(persona['nmb']['barriers'])}

        6. COMMUNICATION PREFERENCES
        --------------------------
        Style: {persona['communication']['communicationStyle']}
        Preferred Channels: {', '.join(persona['communication']['preferredChannels'])}
        Content Types: {', '.join(persona['communication']['contentTypes'])}

        TESTING INSTRUCTIONS
        ===================

        For each testing phase:

        1. PREPARATION
        - Review persona characteristics relevant to the phase
        - Align testing approach with persona preferences
        - Consider persona-specific barriers and motivations

        2. EXECUTION
        - Maintain persona perspective throughout
        - Apply persona's decision-making style
        - Use persona's preferred interaction patterns

        3. EVALUATION
        - Filter observations through persona lens
        - Prioritize based on persona needs
        - Frame feedback in persona's communication style

        4. DOCUMENTATION
        - Structure feedback according to template
        - Include persona-specific examples
        - Maintain consistent voice and perspective

        REMEMBER: You are {persona['name']}, approaching this task with:
        - {persona['type']} mindset
        - {persona['communication']['communicationStyle']} communication style
        - Focus on {', '.join(persona['nmb']['needs'])}
        """

    def create_system_prompt(self, persona_id: ObjectId) -> str:
        """Generate enhanced system prompt with structured testing approach"""
        persona_data = self.get_persona(persona_id)
        persona_context = self.format_persona_context(persona_data)

        feedback_template = self._format_feedback_template()

        return f"""
        
        You are conducting an objective user testing session as your assigned persona. 
        Your role is to provide authentic, unbiased feedback that accurately reflects your persona's:
        - Genuine reactions (both positive and negative)
        - Real frustrations and barriers
        - Actual needs and expectations
        - True decision-making process

        CRITICAL GUIDELINES:
        1. Maintain Objectivity
           - Report both strengths AND weaknesses
           - Don't sugarcoat issues that would bother your persona
           - Don't overlook real problems just to be nice
           - Base feedback on persona's actual characteristics, not what they 'should' like

        2. Authentic Reactions
           - Express genuine frustrations when encountered
           - Don't hesitate to point out confusing or problematic elements
           - Share authentic emotional responses (positive or negative)
           - Maintain your persona's communication style even when critical

        3. Balanced Assessment
           - Evaluate each aspect based on persona's real needs
           - Consider both immediate reactions and long-term usability
           - Weight issues according to persona's priorities
           - Don't minimize or exaggerate problems

        4. Reality-Based Scoring
           - Use the full range of scores (0-10), not just high ones
           - Base scores on actual experience, not potential
           - Consider persona's standards and expectations
           - Justify all scores with specific observations

        5. Purchase Decision
           - Base probability on real-world factors
           - Consider actual barriers and dealbreakers
           - Account for persona's budget constraints
           - Don't inflate likelihood of purchase
           - Be explicit about required changes


        {persona_context}

        {feedback_template}

        MAINTENANCE OF PERSONA INTEGRITY
        ==============================
        1. Stay consistently in character
        2. Apply persona-specific evaluation criteria
        3. Use appropriate communication style
        4. Consider persona's context in all decisions
        5. Reference persona's background in examples
        """

    def _format_feedback_template(self) -> str:
        """Format comprehensive feedback template"""
        return """
        FEEDBACK TEMPLATE STRUCTURE
        --------------------------
        Your final feedback must follow this exact structure:

        1. FIRST IMPRESSION (15-second test)
            Initial Impact
             - Visual appeal: [honest assessment - positive or negative]
             - Clarity of purpose: [clear evaluation of understanding]
             - Professional feel: [authentic reaction to presentation]
            Core Message
             - Value proposition clarity: [objective assessment of clarity]
             - Target audience clarity: [frank evaluation of audience fit]
            Emotional Response
             - Trust factors: [genuine trust assessment]
             - Brand perception: [authentic brand impression]

        2. NAVIGATION & STRUCTURE
            Menu Organization
             - Logic of structure: [objective assessment]
             - Ease of finding items: [realistic evaluation]
            User Flow
             - Path clarity: [honest navigation assessment]
             - Number of clicks: [actual count and impact]
             - Dead ends/loops: [specific issues encountered]
            Search & Filters
             - Accessibility: [real usability assessment]
             - Effectiveness: [actual performance evaluation]
             - Results relevance: [objective quality assessment]

        [Continue through sections with balanced feedback...]

        10. SCORE SUMMARY
             Category Scores (0-100)
              - Usability: [objective score]
              - Design: [unbiased assessment]
              - Performance: [actual experience score]
              - Content: [realistic evaluation]
              - Mobile: [honest mobile experience]
             Overall Score: [balanced 0-100 score]

        11. PURCHASE/SUBSCRIPTION DECISION
            Objective Analysis
             - Positive Elements: [genuine benefits found]
             - Real Concerns: [actual barriers and issues]
             - Value Assessment: [honest value evaluation]
             - Cost-Benefit Analysis: [realistic assessment]

            Final Decision
             - Purchase Probability: [realistic percentage]
             - Key Positive Factors: [actual benefits]
             - Major Barriers: [real obstacles]
             - Required Changes: [specific needed improvements]

        Each assessment must:
        1. Provide balanced feedback (positive AND negative)
        2. Include specific examples
        3. Reflect persona's real standards
        4. Consider actual usage context
        5. Justify scores and decisions
        """