from datetime import datetime

class ScratchpadBeautify:
    def __init__(self, prompt):
        self.prompt = prompt


    def beautify_python_code_run_results(self, result):
        # Add persona context to test results
        test_summary = f"""
Test Results for {self.prompt.persona['name']}:
- Decision Style: {self.prompt.persona['consumption']['process']['decisionStyle']}
- Key Requirements: {', '.join(self.prompt.persona['nmb']['needs'])}

Execution Output:
{result}
"""
        return test_summary

    def beautify_extracted_links(self, result):
        # Add persona context to link analysis
        enhanced_text = f"""
        Analyzing links for {self.prompt.persona['name']}, who:
        - Prioritizes: {', '.join(self.prompt.persona['consumption']['decisionCriteria'])}
        - Needs: {', '.join(self.prompt.persona['nmb']['needs'])}
    
        Content to analyze:
        {result}
        """
        return  enhanced_text


    @staticmethod
    def beautify_with_logs(analysis):
        formatted_logs =f"""
        === {analysis.type.upper()} Analysis [{analysis.timestamp}] ===
        Analyzer: {analysis.analyzer} ({analysis.persona_type})

        {analysis.content}

        === End Analysis ===
        """
        return formatted_logs

    @staticmethod
    def beautify_with_logs_final_summary(final_summary):
        # Log final summary
        timestamp = datetime.now().isoformat()
        final_summary = f"""
=== FINAL ANALYSIS SUMMARY [{timestamp}] ===
{str(final_summary)}
=== END SUMMARY ===
"""
        return final_summary