import subprocess
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, WebSocket
from langchain_core.agents import AgentAction
from pydantic import BaseModel
import logging
import json
from datetime import datetime
import asyncio
import uvicorn
import os
from prompts.react import Prompt
from langchain.agents import create_react_agent, AgentExecutor
from bson import ObjectId
from llms.llm import LLM

# Initialize FastAPI
app = FastAPI(
    title="Stella API",
    description="API for website beta testing with virtual personas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Logging setup
class StreamHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        print(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'event': record.event if hasattr(record, 'event') else 'general',
            'message': msg
        }), flush=True)


def setup_logging():
    logger = logging.getLogger('stella')
    logger.setLevel(logging.INFO)
    handler = StreamHandler()
    logger.addHandler(handler)
    return logger


# Request model
class StellaRequest(BaseModel):
    url: str
    llm_id: str
    persona_id: str


# Utility to process data
async def process_data(url: str, llm_id: str, persona_id: str):
    os.environ["llm_id"] = llm_id
    os.environ["persona"] = persona_id

    prompt = Prompt(os.getenv("mongo_db_uri"), ObjectId(persona_id))
    from utils.tools import crawl, query_site_visually, query_site_textually, get_links
    llm = LLM(llm_id).get_llm()
    tools = [crawl, query_site_visually, query_site_textually, get_links]

    react_agent = create_react_agent(tools=tools, llm=llm, prompt=prompt.create_prompt_template())
    agent_executor = AgentExecutor(agent=react_agent, tools=tools, handle_parsing_errors=True, verbose=True)

    async for chunk in agent_executor.astream({"input": url}):
        yield chunk


# Helper function to serialize AgentAction objects
def serialize_agent_action(obj):
    if isinstance(obj, AgentAction):
        return {
            "tool": obj.tool,
            "tool_input": obj.tool_input,
            "log": obj.log
        }
    # Handle AIMessage serialization
    if hasattr(obj, 'content'):
        return {"content": obj.content}
    if hasattr(obj, '__dict__'):
        serialized = {}
        for key, value in obj.__dict__.items():
            try:
                if isinstance(value, (str, int, float, bool, list, dict)):
                    serialized[key] = value
                elif hasattr(value, '__dict__'):
                    serialized[key] = {k: v for k, v in value.__dict__.items()
                                     if isinstance(v, (str, int, float, bool, list, dict))}
            except:
                continue
        return serialized
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# POST Endpoint
@app.post("/call-stella")
async def call_stella(request: StellaRequest):
    logger = setup_logging()
    logger.info(f"Starting analysis for {request.url}", extra={'event': 'tool_start'})

    try:
        result = []
        async for chunk in process_data(request.url, request.llm_id, request.persona_id):
            result.append(chunk)
        logger.info("Stella execution completed successfully", extra={'event': 'tool_complete'})
        return {"output": result}
    except asyncio.TimeoutError:
        logger.error("Stella process timed out after 5 minutes", extra={'event': 'timeout'})
        raise HTTPException(status_code=504, detail="Process timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={'event': 'error'})
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.websocket("/stream-stella")
async def stream_stella(websocket: WebSocket):
    logger = setup_logging()
    await websocket.accept()

    try:
        # Receive parameters from the WebSocket without timeout
        data = await websocket.receive_json()

        url = data.get("url")
        persona_id = data.get("persona_id")

        llm_id = data.get("llm_id")
        os.environ["llm_id"] = llm_id
        os.environ["persona"] = persona_id

        if not url or not llm_id or not persona_id:
            await websocket.send_json({"error": "Invalid input parameters"})
            return

        logger.info(f"Starting streaming analysis for {url}", extra={'event': 'tool_start'})

        prompt = Prompt(os.getenv("mongo_db_uri"), ObjectId(persona_id))
        from utils.tools import crawl, query_site_visually, query_site_textually,analyze_heatmap,  get_links, generate_python_code, run_python_code, generate_feedback, check_for_feedback_reliability

        # Create agent and executor
        llm = LLM(llm_id).get_llm()
        tools = [crawl, query_site_visually, query_site_textually, analyze_heatmap, get_links, generate_python_code,
                 run_python_code, generate_feedback, check_for_feedback_reliability]

        # Create agent and executor
        react_agent = create_react_agent(tools=tools, llm=llm, prompt=prompt.create_prompt_template())
        agent_executor = AgentExecutor(agent=react_agent, tools=tools, handle_parsing_errors=True, verbose=True)

        async for chunk in agent_executor.astream({"input": url}):
            try:
                serializable_chunk = json.dumps(chunk, default=serialize_agent_action)
                await websocket.send_text(serializable_chunk)
            except TypeError as e:
                logger.error(f"Serialization error: {e}")
                await websocket.send_json({"error": "Serialization error"})
                break

        logger.info("Stella streaming completed successfully", extra={'event': 'tool_complete'})

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={'event': 'error'})
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

# Run API using uvicorn
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )