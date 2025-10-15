import asyncio
from contextlib import asynccontextmanager
from typing import Annotated, Literal, cast
from fastapi import FastAPI, Request
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from veri_agents_aiware.llm_gateway.langchain import AiwareGatewayLLM
from veri_agents_api.fastapi.thread import (
    create_thread_router,
    ThreadContext,
)
from veri_agents_api.fastapi.thread.schema import ToolCallEvent, ToolMessageChunk

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = AiwareGatewayLLM()

# in real use cases, you would probably want to initialize the checkpointer connection in get_thread
checkpointer = InMemorySaver()

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@tool
async def throw_baseball(angle: int, tool_call_id: Annotated[str, InjectedToolCallId]):
    """Throws a baseball at a specified angle."""

    writer = get_stream_writer()

    writer(ToolMessageChunk(tool_call_id=tool_call_id, content=f"Preparing to throw baseball at angle {angle}...\n\n"))
    await asyncio.sleep(2)
    writer(ToolMessageChunk(tool_call_id=tool_call_id, content=f"Starting countdown...\n\n"))
    await asyncio.sleep(1)
    for i in [3,2,1]:
        writer(ToolMessageChunk(tool_call_id=tool_call_id, content=f"{i}..."))
        await asyncio.sleep(1)
    writer(ToolMessageChunk(tool_call_id=tool_call_id, content="\n\n"))
        
    writer(ToolMessageChunk(tool_call_id=tool_call_id, content=f"Baseball thrown!\n\n"))

    return

def _get_thread_id(request: Request) -> str:
    thread_id = request.path_params.get("thread_id")
    if thread_id is None:
        raise Exception("no thread_id provided in request")

    return thread_id

@asynccontextmanager
async def get_thread(request: Request):
    thread_id = _get_thread_id(request)

    graph = cast(CompiledStateGraph, create_react_agent(
        model=llm,
        tools=[multiply, throw_baseball],
        prompt="You are a helpful assistant.",
        checkpointer=checkpointer
    ))

    yield ThreadContext(
        id=thread_id, graph=graph, config={"callbacks": []}
    )


# agents convenience router for chat
chat_thread_router = create_thread_router(
    # same graph for every request
    get_thread=get_thread
)

app.include_router(chat_thread_router, prefix="/chat/{thread_id}")

uvicorn.run(app, host="0.0.0.0", port=5002)
