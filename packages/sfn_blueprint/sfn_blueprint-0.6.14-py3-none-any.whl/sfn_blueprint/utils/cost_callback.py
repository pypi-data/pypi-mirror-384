"""
Simple cost callback handler for sfn_blueprint.
This is a stub implementation since the original CostCallbackHandler is not available.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from langchain.callbacks.base import BaseCallbackHandler


class SimpleCostCallbackHandler(BaseCallbackHandler):
    """Simple cost callback handler that logs cost information."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.total_cost = 0.0
        self.total_tokens = 0
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Log when LLM starts."""
        self.logger.debug(f"LLM started with {len(prompts)} prompts")
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Log when LLM ends."""
        self.logger.debug("LLM completed")
    
    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Log when LLM errors."""
        self.logger.error(f"LLM error: {error}")
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Log new token generation."""
        pass  # Don't log every token to avoid spam
    
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Log when chain starts."""
        self.logger.debug("Chain started")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Log when chain ends."""
        self.logger.debug("Chain completed")
    
    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Log when chain errors."""
        self.logger.error(f"Chain error: {error}")
    
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Log when tool starts."""
        self.logger.debug("Tool started")
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when tool ends."""
        self.logger.debug("Tool completed")
    
    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Log when tool errors."""
        self.logger.error(f"Tool error: {error}")
    
    def on_text(self, text: str, **kwargs: Any) -> None:
        """Log text."""
        pass  # Don't log text to avoid spam
    
    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Log agent action."""
        self.logger.debug(f"Agent action: {action}")
    
    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Log agent finish."""
        self.logger.debug("Agent finished")
    
    def on_retriever_start(
        self, serialized: Dict[str, Any], query: str, **kwargs: Any
    ) -> None:
        """Log when retriever starts."""
        self.logger.debug("Retriever started")
    
    def on_retriever_end(self, documents: List[Any], **kwargs: Any) -> None:
        """Log when retriever ends."""
        self.logger.debug(f"Retriever completed with {len(documents)} documents")
    
    def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Log when retriever errors."""
        self.logger.error(f"Retriever error: {error}")
    
    def get_cost_info(self) -> Dict[str, float]:
        """Get cost information."""
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens
        }
