"""
Stub LLMConfig class for sfn_blueprint.
This provides the interface needed by the schema since the original LLMConfig is not available.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Stub LLM configuration class."""
    
    model_name: str
    logger: Optional[Any] = None
    session: Optional[Any] = None
    
    # Allow any additional fields to be passed
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name: str) -> Any:
        """Return None for any undefined attributes."""
        return None
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting any attribute."""
        object.__setattr__(self, name, value)


def get_model(config: LLMConfig) -> Any:
    """Stub get_model function that returns a mock LLM instance."""
    from unittest.mock import Mock
    
    # Create a mock LLM that has the methods used in reflection_graph.py
    mock_llm = Mock()
    
    # Mock the invoke method
    def mock_invoke(messages):
        mock_response = Mock()
        mock_response.content = "Mock response content"
        return mock_response
    
    mock_llm.invoke = mock_invoke
    
    # Mock the with_structured_output method
    def mock_with_structured_output(output_class):
        return mock_llm
    
    mock_llm.with_structured_output = mock_with_structured_output
    
    return mock_llm
