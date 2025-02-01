class PromptInjection:
    def __init__(self, persona_data: dict):
        self.persona = persona_data
        self.visual_prompt = self._create_visual_prompt()
        self.code_prompt = self._create_code_prompt()
        self.context_handler_prompt = self._create_context_handler_prompt()

    def _create_visual_prompt(self) -> str:
        """Create persona-specific visual analysis prompt"""
        return f"""
        Analyze this website as {self.persona['name']}, a {self.persona['type']}, who:
        - Uses primarily: {self.persona['digital']['devices']['primary']}
        - Prefers: {self.persona['ux']['visualStyle']['designStyle']} design
        - Expects: {', '.join(self.persona['ux']['expectedFeatures'])}
        - Prioritizes mobile: {self.persona['ux']['navigation']['mobilePriority']}

        Focus on:
        1. Professional Impact
           - Visual hierarchy matching {self.persona['communication']['communicationStyle']} style
           - Brand alignment with business needs
           - Feature visibility for {', '.join(self.persona['nmb']['needs'])}

        2. Efficiency Elements
           - Navigation clarity for {self.persona['consumption']['process']['decisionStyle']} decisions
           - Access to key features
           - Mobile optimization
           - Loading performance

        3. Business Value Indicators
           - ROI/performance visibility
           - Professional credibility signals
           - Time-saving features

        Analyze considering their barriers: {', '.join(self.persona['nmb']['barriers'])}
        """


    def _create_code_prompt(self) -> str:
        """Create persona-specific code generation prompt"""
        return f"""
        Generate test cases that validate the website meets {self.persona['name']}'s requirements:

        Test Categories:
        1. Performance Tests
           - Load time (mobile and desktop)
           - Feature response time
           - API performance

        2. Functionality Tests
           - Core feature validation
           - Mobile responsiveness
           - Cross-device compatibility

        3. Content Tests
           - Value proposition clarity
           - Feature documentation
           - Professional terminology

        Consider their:
        - Decision time: {self.persona['consumption']['process'].get('averageDecisionTime', 'N/A')} hours
        - Key needs: {', '.join(self.persona['nmb']['needs'])}
        - Expected features: {', '.join(self.persona['ux']['expectedFeatures'])}
        """

    def _create_context_handler_prompt(self):
        context_prefix = f"""
        Analyzing as {self.persona['name']}, who:
        - Makes {self.persona['consumption']['process']['decisionStyle']} decisions
        - Needs: {', '.join(self.persona['nmb']['needs'])}
        - Values: {', '.join(self.persona['consumption']['decisionCriteria'])}
        """

        analysis_prompts = {
            "visual": f"""
            {context_prefix}
            Visual Analysis Request:
            - Professional design evaluation
            - Mobile responsiveness assessment
            - Navigation efficiency review
            - Visual hierarchy analysis
            """,
            "textual": f"""
            {context_prefix}
            Textual Analysis Request:
            - Content clarity assessment
            - Business value evaluation
            - Feature description review
            - Technical documentation analysis
            """,
            "functional": f"""
            {context_prefix}
            Functional Analysis Request:
            - Feature completeness check
            - Integration capabilities
            - Performance evaluation
            - Technical implementation review
            """
        }
        return analysis_prompts

    def _create_textual_website_summary_prompt(self, all_summaries, collapsed_summaries):
        summary = f"""
        Generate comprehensive analysis for {self.persona['name']}, considering:

        PERSONA PROFILE:
        - Type: {self.persona['type']}
        - Decision Style: {self.persona['consumption']['process']['decisionStyle']}
        - Key Needs: {', '.join(self.persona['nmb']['needs'])}
        - Barriers: {', '.join(self.persona['nmb']['barriers'])}

        ANALYSIS SECTIONS:
        {all_summaries}

        ADDITIONAL FINDINGS:
        {collapsed_summaries}
        """
        return summary
