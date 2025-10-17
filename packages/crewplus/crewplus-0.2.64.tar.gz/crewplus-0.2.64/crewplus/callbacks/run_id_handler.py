# File: crewplus/callbacks/run_id_handler.py

from typing import Any, Dict
from uuid import UUID
import logging

# Langfuse imports with graceful fallback
try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    from .async_langfuse_handler import AsyncLangfuseCallbackHandler
    from langfuse import get_client
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # Define dummy base classes if langfuse is not available to avoid runtime errors
    class LangfuseCallbackHandler: pass
    class AsyncLangfuseCallbackHandler: pass
    get_client = None

# --- Custom Callback Handlers to capture the run_id ---
if LANGFUSE_AVAILABLE:
    class RunIdCallbackHandler(LangfuseCallbackHandler):
        """
        A custom synchronous callback handler that captures the Langchain run_id
        and adds it to the Langfuse trace metadata.
        """
        def on_chain_start(
            self,
            serialized: Dict[str, Any],
            inputs: Dict[str, Any],
            run_id: UUID,
            **kwargs: Any,
        ) -> Any:
            # First, let the base handler do its work, which includes creating the trace
            run = super().on_chain_start(serialized, inputs, run_id, **kwargs)

            try:
                # Then, update the created trace with the run_id as metadata
                langfuse_client = get_client()
                langfuse_client.update_current_trace(
                    metadata={"langchain_run_id": str(run_id)}
                )
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to add run_id to Langfuse trace: {e}")

            return run

    class AsyncRunIdCallbackHandler(AsyncLangfuseCallbackHandler):
        """
        A custom asynchronous callback handler that captures the Langchain run_id
        and adds it to the Langfuse trace metadata.
        """
        async def on_chain_start(
            self,
            serialized: Dict[str, Any],
            inputs: Dict[str, Any],
            run_id: UUID,
            **kwargs: Any,
        ) -> Any:
            # First, let the base handler do its work, which includes creating the trace
            run = await super().on_chain_start(serialized, inputs, run_id, **kwargs)

            try:
                # The get_client() is thread-safe and can be used in async contexts
                # for this type of single, atomic update.
                langfuse_client = get_client()
                langfuse_client.update_current_trace(
                    metadata={"langchain_run_id": str(run_id)}
                )
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to add run_id to async Langfuse trace: {e}")

            return run
