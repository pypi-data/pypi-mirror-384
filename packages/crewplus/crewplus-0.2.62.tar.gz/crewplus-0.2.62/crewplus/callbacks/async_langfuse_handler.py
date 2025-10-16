# File: crewplus/callbacks/async_langfuse_handler.py
import asyncio
import contextvars
from contextlib import contextmanager
from typing import Any, Dict, List, Union, Optional, Sequence
from uuid import UUID

try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    from langchain_core.callbacks import AsyncCallbackHandler
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import BaseMessage
    from langchain.schema.agent import AgentAction, AgentFinish
    from langchain.schema.document import Document
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseCallbackHandler = None
    AsyncCallbackHandler = object
    # Define dummy types if langchain is not available
    LLMResult = object
    BaseMessage = object
    AgentAction = object
    AgentFinish = object
    Document = object


_ASYNC_CONTEXT_TOKEN = "in_async_context"
in_async_context = contextvars.ContextVar(_ASYNC_CONTEXT_TOKEN, default=False)

@contextmanager
def async_context():
    """A context manager to signal that we are in an async execution context."""
    token = in_async_context.set(True)
    try:
        yield
    finally:
        in_async_context.reset(token)

class AsyncLangfuseCallbackHandler(AsyncCallbackHandler):
    """
    Wraps the synchronous LangfuseCallbackHandler to make it fully compatible with
    LangChain's async methods by handling all relevant events.
    """
    def __init__(self, *args: Any, **kwargs: Any):
        if not LANGFUSE_AVAILABLE:
            raise ImportError("Langfuse is not available. Please install it with 'pip install langfuse'")
        self.sync_handler = LangfuseCallbackHandler(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.sync_handler, name)

    # LLM Events
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        corrected_prompts = prompts if isinstance(prompts, list) else [prompts]
        await asyncio.to_thread(
            self.sync_handler.on_llm_start, serialized, corrected_prompts, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_chat_model_start, serialized, messages, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_llm_end(
        self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        await asyncio.to_thread(
            self.sync_handler.on_llm_end, response, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        await asyncio.to_thread(
            self.sync_handler.on_llm_error, error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    # Chain Events
    async def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_chain_start, serialized, inputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_chain_end(
        self, outputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_chain_end, outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_chain_error, error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    # Tool Events
    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_tool_start, serialized, input_str, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_tool_end(
        self, output: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_tool_end, output, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_tool_error, error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )
        
    # Retriever Events
    async def on_retriever_start(
        self, serialized: Dict[str, Any], query: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_retriever_start, serialized, query, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_retriever_end(
        self, documents: Sequence[Document], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_retriever_end, documents, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_retriever_error(
        self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_retriever_error, error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )
        
    # Agent Events
    async def on_agent_action(
        self, action: AgentAction, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_agent_action, action, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    async def on_agent_finish(
        self, finish: AgentFinish, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        await asyncio.to_thread(
            self.sync_handler.on_agent_finish, finish, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )
