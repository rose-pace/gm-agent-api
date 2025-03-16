"""
Standardized model response format for handling text responses and tool calls.
"""
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
import json


class ToolCall(BaseModel):
    """
    Represents a tool call requested by the model.
    
    Attributes:
        tool_name: Name of the tool to call
        arguments: Arguments to pass to the tool
        tool_call_id: Optional ID for tracking the tool call (used by some providers)
    """
    tool_name: str
    arguments: Dict[str, Any]
    tool_call_id: Optional[str] = None


class ModelResponse:
    """
    Standardized response from a model provider.
    Can represent either a text response or a request to use tools.
    """
    
    def __init__(self, 
                 content: Optional[str] = None, 
                 history: Optional[List[Dict[str, Any]]] = None,
                 tool_calls: Optional[List[ToolCall]] = None,
                 raw_response: Any = None):
        """
        Initialize a model response.
        
        Args:
            content: Text content if this is a text response
            tool_calls: List of tool calls if the model requests tool use
            raw_response: The original provider-specific response
        """
        self.content = content
        self.history = history or []
        self.tool_calls = tool_calls or []
        self.raw_response = raw_response
        
    @property
    def is_tool_call(self) -> bool:
        """
        Check if this response contains a tool call request.
        
        Returns:
            True if this response contains tool calls, False otherwise
        """
        return bool(self.tool_calls)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary representation.
        
        Returns:
            Dictionary representation of this response
        """
        return {
            'content': self.content,
            'tool_calls': [tc.model_dump() for tc in self.tool_calls] if self.tool_calls else [],
            'is_tool_call': self.is_tool_call
        }
    
    @classmethod
    def from_openai_response(cls, response: Any) -> 'ModelResponse':
        """
        Create a ModelResponse from an OpenAI API response.
        
        Args:
            response: OpenAI API response object
            
        Returns:
            Standardized ModelResponse
        """
        message = response.choices[0].message
        content = message.content
        
        # Check if there are tool calls
        tool_calls = []
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except (json.JSONDecodeError, AttributeError):
                    arguments = {}
                
                tool_calls.append(ToolCall(
                    tool_name=tool_call.function.name,
                    arguments=arguments,
                    tool_call_id=tool_call.id
                ))
        
        return cls(content=content, tool_calls=tool_calls, raw_response=response)
    
    @classmethod
    def from_anthropic_response(cls, response: Any) -> 'ModelResponse':
        """
        Create a ModelResponse from an Anthropic API response.
        
        Args:
            response: Anthropic API response object
            
        Returns:
            Standardized ModelResponse
        """
        content = None
        tool_calls = []
        
        # Check if there's a tool_use block in the response
        if hasattr(response, 'content'):
            for block in response.content:
                if block.type == 'text':
                    content = block.text
                elif block.type == 'tool_use':
                    try:
                        arguments = block.input if isinstance(block.input, dict) else json.loads(block.input)
                    except (json.JSONDecodeError, AttributeError):
                        arguments = {}
                        
                    tool_calls.append(ToolCall(
                        tool_name=block.name,
                        arguments=arguments,
                        tool_call_id=block.id if hasattr(block, 'id') else None
                    ))
        
        return cls(content=content, tool_calls=tool_calls, raw_response=response)
    
    @classmethod
    def from_huggingface_response(cls, response: Any) -> 'ModelResponse':
        """
        Create a ModelResponse from a HuggingFace API response.
        
        Args:
            response: HuggingFace API response object
            
        Returns:
            Standardized ModelResponse
        """
        content = None
        tool_calls = []
        
        # Parse HuggingFace response
        # This will need customization based on the specific format returned
        try:
            if hasattr(response, 'choices') and response.choices:
                message = response.choices[0].message
                content = message.content
                
                # Check for tool calls in the HuggingFace format
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        try:
                            arguments = json.loads(tool_call.parameters) if isinstance(tool_call.parameters, str) else tool_call.parameters
                        except (json.JSONDecodeError, AttributeError):
                            arguments = {}
                            
                        tool_calls.append(ToolCall(
                            tool_name=tool_call.name,
                            arguments=arguments,
                            tool_call_id=tool_call.id if hasattr(tool_call, 'id') else None
                        ))
        except Exception:
            # Fallback for other response formats
            content = str(response)
        
        return cls(content=content, tool_calls=tool_calls, raw_response=response)
