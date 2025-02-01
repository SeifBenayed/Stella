from langchain_core.prompts import ChatPromptTemplate
from llms.llm import LLM
from langchain_core.output_parsers import StrOutputParser
import os

class MapChain(LLM):
    llm_id = "gpt-4o"
    llm_obj = LLM(llm_id)
    selected_llm = llm_obj.get_llm()
    map_prompt = ChatPromptTemplate.from_messages(
        [("system", "get relevant buttons links info etc with description:\\n\\n{context}")]
    )
    map_chain = map_prompt | selected_llm | StrOutputParser()
