from typing import Dict, Any, List, Literal
from dataclasses import dataclass
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents.reduce import (
    acollapse_docs,
    split_list_of_docs,
)
from langchain_core.documents import Document
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from utils.helper_functions import HelperFunct
import asyncio
from datetime import datetime
import logging
import os
from states.state import SummaryState, OverallState
from chains.map_reduce_chain import MapReduceChain
from handlers.PersonaContextProcessor import PersonaMapReduceChain
from emb.embeddings import Embeddings


@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters"""
    token_max: int = 1000
    chunk_count_limit: int = 10
    recursion_limit: int = 10


@dataclass
class AnalysisSection:
    """Structure for analysis sections"""
    type: str
    content: str
    timestamp: str
    analyzer: str
    persona_type: str


class EnhancedLongContextHandler(HelperFunct):
    """Enhanced context handler for processing website content with persona context"""

    def __init__(self, tmp_folder: str, prompt, beau):
        """Initialize the enhanced context handler"""
        # Initialize parent
        super().__init__(tmp_folder)

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Prompt
        self.prompt = prompt

        # Beautify
        self.beau = beau

        # Store persona data
        self.persona_data = self.prompt.persona
        self.persona_chains = PersonaMapReduceChain(self.prompt.persona)

        # Initialize base map-reduce chains
        self.map_chain = MapReduceChain.map_chain
        self.reduce_chain = MapReduceChain.reduce_chain

        # Create persona-specific chains
        self.persona_map_chain = (
                self.persona_chains.create_persona_map_prompt() |
                MapReduceChain.selected_llm |
                StrOutputParser()
        )

        self.persona_reduce_chain = (
                self.persona_chains.create_persona_reduce_prompt() |
                MapReduceChain.selected_llm |
                StrOutputParser()
        )

        # Initialize analysis parameters
        self.config = AnalysisConfig()
        self.token_max = self.config.token_max
        self.chunk_count_limit = self.config.chunk_count_limit

        # Initialize state
        self.summary = ""
        self.split_docs = []
        self.analysis_sections = {
            "visual": [],
            "textual": [],
            "functional": []
        }

        # Initialize scratchpad
        self._init_scratchpad()

    def _init_scratchpad(self):
        """Initialize scratchpad with error handling"""
        try:
            if not os.path.exists(self.agent_scratchpad_path):
                self.write_file(self.agent_scratchpad_path, "")
                self.logger.info(f"Created new scratchpad at {self.agent_scratchpad_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize scratchpad: {str(e)}")
            raise

    def generate_chunks(self):
        """Generate chunks from HTML content"""
        try:
            self.split_docs = self.create_chunks()[:self.chunk_count_limit]
            self.logger.info(f"Generated {len(self.split_docs)} documents like {type(self.split_docs[0])}")
        except Exception as e:
            self.logger.error(f"Error generating chunks: {str(e)}")
            raise

    async def process_section(self, section_type: str, content: str) -> None:
        """Process sections with specific analysis chains"""
        try:
            # Create section-specific prompt

            analysis_prompts = self.prompt.context_handler_prompt
            prompt = analysis_prompts.get(section_type)
            if not prompt:
                raise ValueError(f"Unknown section type: {section_type}")

            # Add content to prompt
            full_prompt = f"{prompt}\nContent: {content}"

            # Get analysis
            response = await self.persona_map_chain.ainvoke({"context": full_prompt})
            response_str = str(response)

            # Create analysis section
            analysis = AnalysisSection(
                type=section_type,
                content=response_str,
                timestamp=datetime.now().isoformat(),
                analyzer=self.persona_data['name'],
                persona_type=self.persona_data['type']
            )

            # Store analysis
            self.analysis_sections[section_type].append(response_str)

            formatted_analysis = self.beau.beautify_with_logs(analysis)
            self.append_to_agent_scratchpad(formatted_analysis, "query_site_textually")
            self.logger.info(f"Processed {section_type} analysis successfully")

        except Exception as e:
            error_msg = f"Error processing {section_type} analysis: {str(e)}"
            self.logger.error(error_msg)
            self.append_to_agent_scratchpad(f"ERROR: {error_msg}")
            raise

    async def generate_summary(self, state: SummaryState) -> Dict[str, List[str]]:
        """Generate summary using persona-specific map chain"""
        try:
            response = await self.persona_map_chain.ainvoke({"context": state['content']})
            return {"summaries": [str(response)]}
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            raise

    @staticmethod
    def map_summaries(state: OverallState) -> List[Dict[str, Any]]:
        """Map contents to summaries"""
        return [
            Send("generate_summary", {"content": content})
            for content in state["contents"]
        ]

    @staticmethod
    def collect_summaries(state: OverallState) -> Dict[str, List[Document]]:
        """Collect summaries into documents"""
        return {
            "collapsed_summaries": [Document(summary) for summary in state["summaries"]]
        }

    async def collapse_summaries(self, state: OverallState) -> Dict[str, List[Document]]:
        """Collapse summaries using persona-specific reduce chain"""
        try:
            doc_lists = split_list_of_docs(
                state["collapsed_summaries"],
                self.length_function,
                self.token_max
            )

            results = []
            for doc_list in doc_lists:
                collapsed = await acollapse_docs(doc_list, self.reduce_chain.ainvoke)
                results.extend(collapsed)

            return {"collapsed_summaries": results}
        except Exception as e:
            self.logger.error(f"Error collapsing summaries: {str(e)}")
            raise

    def should_collapse(self, state: OverallState) -> Literal["collapse_summaries", "generate_final_summary"]:
        """Determine if summaries should be collapsed"""
        try:
            num_tokens = self.length_function(state["collapsed_summaries"])
            return "collapse_summaries" if num_tokens > self.token_max else "generate_final_summary"
        except Exception as e:
            self.logger.error(f"Error in collapse decision: {str(e)}")
            raise

    async def generate_final_summary(self, state: OverallState) -> Dict[str, str]:
        """Generate final summary using persona-specific reduce chain"""
        try:
            # Combine all sections
            section_summaries = []
            for section_type, contents in self.analysis_sections.items():
                if contents:
                    summary = f"{section_type.upper()} ANALYSIS:\n"
                    summary += "\n".join(str(content) for content in contents)
                    section_summaries.append(summary)

            all_summaries = "\n\n".join(section_summaries)

            # Add collapsed summaries if they exist
            collapsed_summaries = "\n".join([
                doc.page_content for doc in state['collapsed_summaries']
            ]) if 'collapsed_summaries' in state else ""

            # Create final prompt
            final_prompt = self.prompt._create_textual_website_summary_prompt(all_summaries, collapsed_summaries)

            final_summary = await self.persona_reduce_chain.ainvoke({"documents": final_prompt})

            summary_log = self.beau.beautify_with_logs_final_summary(final_summary)
            self.append_to_agent_scratchpad(summary_log, "query_text_textually")

            return {"final_summary": str(final_summary)}

        except Exception as e:
            error_msg = f"Error generating final summary: {str(e)}"
            self.logger.error(error_msg)
            raise

    def build_graph(self):
        """Build the processing graph"""
        try:
            graph = StateGraph(OverallState)

            # Add nodes
            graph.add_node("generate_summary", self.generate_summary)
            graph.add_node("collect_summaries", self.collect_summaries)
            graph.add_node("collapse_summaries", self.collapse_summaries)
            graph.add_node("generate_final_summary", self.generate_final_summary)

            # Add edges
            graph.add_conditional_edges(START, self.map_summaries, ["generate_summary"])
            graph.add_edge("generate_summary", "collect_summaries")
            graph.add_conditional_edges("collect_summaries", self.should_collapse)
            graph.add_conditional_edges("collapse_summaries", self.should_collapse)
            graph.add_edge("generate_final_summary", END)

            self.app = graph.compile()
            self.logger.info("Graph built successfully")
        except Exception as e:
            self.logger.error(f"Error building graph: {str(e)}")
            raise

    async def get_result(self):
        """Process results through the graph"""
        try:
            async for step in self.app.astream(
                    {"contents": [doc.page_content for doc in self.split_docs]},
                    {"recursion_limit": self.config.recursion_limit},
            ):
                if "content" in step:
                    await self.process_section(
                        "textual" if "text" in step else "visual",
                        step["content"]
                    )
                self.logger.debug(f"Processing step: {list(step.keys())}")
                print(list(step.keys()), step)
            self.logger.info("Result generation completed")
        except Exception as e:
            self.logger.error(f"Error getting results: {str(e)}")
            raise

    def lg_invoke(self):
        """Main invocation method"""
        try:
            self.logger.info("Starting analysis process")
            self.generate_chunks()
            self.build_graph()
            asyncio.run(self.get_result())
            self.logger.info("Analysis completed successfully")
        except Exception as e:
            error_msg = f"Error during invocation: {str(e)}"
            self.logger.error(error_msg)
            raise