from arix_chatbot.app.ai_factory_pipeline import AiFactoryPipeline
from arix_chatbot.state_manager.state_store import SessionStatus
from arix_chatbot.app.agent_registry import AgentRegistry
from fastapi import FastAPI, HTTPException
from typing import Optional, Dict, Any
from arix_chatbot.agents.agents_pool import AGENTS
from pydantic import BaseModel
from pathlib import Path
import argparse
import uvicorn
import logging
import sys


# add root as resource path
sys.path.append(Path(__file__).parent.parent.as_posix())
logger = logging.getLogger(__name__)


def set_pipeline():
    agents_store_ = AgentRegistry(agents=AGENTS)
    ai_factory_pipeline = AiFactoryPipeline(agents_store=agents_store_, root_agent=AGENTS[0].agent_id)
    return ai_factory_pipeline


pipeline = set_pipeline()
app = FastAPI(title="Arix-AI-Factory")


class StartRunRequest(BaseModel):
    input: str
    initial_agent: Optional[str] = "qa_analyzer"


class HumanInputRequest(BaseModel):
    payload: Dict[str, Any]


@app.post("/v1/new")
async def start_run():
    """Start a new run."""
    print("Received request to start a new run")
    try:
        state = await pipeline.start_run()
        if state.status == SessionStatus.WAIT_HUMAN.value:
            return {"run_id": state.run_id, "chat": state.user_outbox}
        return {"run_id": state.run_id}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to start run: {e}")
        raise HTTPException(500, "Internal server error")


@app.get("/v1/{run_id}")
async def get_run(run_id: str):
    """Get run state."""
    state = await pipeline.get_run_state(run_id)
    if not state:
        raise HTTPException(404, "Run not found")
    return state


@app.post("/v1/{run_id}/chat")
async def inject_user_input(run_id: str, request: HumanInputRequest):
    """Inject human input."""
    try:
        state = await pipeline.inject_human_input(run_id, request.payload["chat"]["msg"])
        # if state.status == SessionStatus.WAIT_HUMAN.value:
        # return {"run_id": run_id}
        return {"run_id": state.run_id, "chat": state.user_outbox}
    except Exception as e:
        raise HTTPException(400, e)


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "agents": len(pipeline.agent_registry.agents)}


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Agent Pipeline API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    print(f"Starting Agent Pipeline API Server")
    print(f"Host: {args.host}:{args.port}")

    uvicorn.run(
        "app.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()
