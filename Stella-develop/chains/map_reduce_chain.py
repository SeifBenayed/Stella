from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts.reduce import reduce_template
from chains.map_chain import MapChain


class MapReduceChain(MapChain):
    reduce_prompt = ChatPromptTemplate([("human", reduce_template)])
    reduce_chain = reduce_prompt | MapChain.selected_llm | StrOutputParser()