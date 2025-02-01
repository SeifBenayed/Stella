import os
import pprint
from bson import ObjectId
from dotenv import load_dotenv
from prompts.react import Prompt
from langchain.agents import create_react_agent, AgentExecutor
import asyncio
import logging
from llms.llm import LLM
from utils.tools import crawl, query_site_visually, query_site_textually, get_links, analyze_heatmap, generate_python_code, \
    generate_feedback, run_python_code, check_for_feedback_reliability
from utils.crawl_website import WebCrawler
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure required environment variables are present
if not os.getenv("mongo_db_uri") or not os.getenv("persona") or not os.getenv("llm_id"):
    raise EnvironmentError("Ensure 'mongo_db_uri', 'persona', and 'llm_id' are set in the .env file.")


def clean_urls_single_product(base_url, url_list):
    base_domain = urlparse(base_url).netloc
    seen = set()
    clean_urls = []
    product_found = False

    for url in url_list:
        parsed = urlparse(url)
        if parsed.netloc == base_domain and not url.endswith('#') and '#' not in url:
            if '/product/' in url:
                if not product_found:
                    clean_urls.append(url)
                    product_found = True
            else:
                if url not in seen:
                    clean_urls.append(url)
                    seen.add(url)

    return clean_urls

def verify_and_filter_domains(base_url, url_list):
    base_domain = urlparse(base_url).netloc
    return [url for url in url_list if urlparse(url).netloc == base_domain]


# Define main function
async def main(url):
    prompt = Prompt(os.getenv("mongo_db_uri"), ObjectId(os.getenv("persona")))
    llm_id = os.getenv("llm_id")
    # os.environ["llm_id"] = "gpt-4o" # supports gpt-4o and sonnet-3-5 does not support gpt-o1
    # Import tools
    llm = LLM(llm_id).get_llm()

    tools = [crawl, query_site_visually, query_site_textually, analyze_heatmap, get_links, generate_python_code,
             run_python_code, generate_feedback, check_for_feedback_reliability]

    # Create agent and executor
    react_agent = create_react_agent(tools=tools, llm=llm, prompt=prompt.create_prompt_template())
    agent_executor = AgentExecutor(agent=react_agent, tools=tools, handle_parsing_errors=True, verbose=True)

    # Execute asynchronously
    chunks = []

    async for chunk in agent_executor.astream({"input": url}):
        chunks.append(chunk)
        pprint.pprint(chunk, depth=1)

    return chunks

if __name__ == "__main__":

    url = "https://askhedi.com/"
    logger.info(f"Processing URL: {url}")
    os.environ["crawl_mode"] = "initial"
    os.environ["crawl_mode"] = "gpt-4o"
    llm_id = os.getenv("mongo_db_uri")
    urls = [url]
    wc = WebCrawler(llm_id)
    wc.browse(url)
    parsed_urls = list(set(wc.links))
    if urls[0] not in parsed_urls:
        urls.extend(parsed_urls)
    else:
        urls = parsed_urls
    urls = [url for url in urls if url.strip()]
    urls = clean_urls_single_product(url, urls)
    for url in urls[3]:
        chunks = asyncio.run(main(url))
        logger.info("Execution completed.")
