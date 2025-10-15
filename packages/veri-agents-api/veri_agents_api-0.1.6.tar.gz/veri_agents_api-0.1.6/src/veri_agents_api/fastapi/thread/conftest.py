"""
expects env vars:
LLM_GATEWAY_KEY
AIWARE_SESSION or AIWARE_API_KEY
LLM_GATEWAY_MODEL
"""

from langchain_core.messages import HumanMessage
from langgraph.graph.message import MessagesState
import pytest
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal, cast
from fastapi import FastAPI, Request
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt import create_react_agent
from fastapi.testclient import TestClient

from veri_agents_aiware.llm_gateway.langchain import AiwareGatewayLLM
from veri_agents_api.fastapi.thread import (
    create_thread_router,
    ThreadContext,
)
from veri_agents_api.fastapi.thread.schema import ToolCallEvent

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

def _app_with_chat(graph: CompiledStateGraph):
    app = FastAPI()

    def _get_thread_id(request: Request) -> str:
        thread_id = request.path_params.get("thread_id")
        if thread_id is None:
            raise Exception("no thread_id provided in request")

        return thread_id

    @asynccontextmanager
    async def get_thread(request: Request):
        thread_id = _get_thread_id(request)

        yield ThreadContext(
            id=thread_id, graph=graph, config={"callbacks": []}
        )


    # agents convenience router for chat
    chat_thread_router = create_thread_router(
        # same graph for every request
        get_thread=get_thread
    )

    app.include_router(chat_thread_router, prefix="/chat/{thread_id}")

    return app

@pytest.fixture
def simple_app():
    def echo_node(state) -> MessagesState:
        return {"messages": [HumanMessage(content=f"Echo: {state['input']}")]}

    graph = StateGraph(state_schema=dict)  # pyright: ignore[reportArgumentType]
    graph.add_node("echo", echo_node)
    graph.set_entry_point("echo")
    graph.set_finish_point("echo")
    compiled_graph = graph.compile()

    app = _app_with_chat(compiled_graph)
    yield app

@pytest.fixture
def simple_client(simple_app: FastAPI):
    client = TestClient(simple_app)
    yield client
