from typing import Dict, List, Optional, Any, Union, Callable
from pydantic import BaseModel, Field

class ToolParameter(BaseModel):
    """
    Represents a parameter for a tool.
    
    Attributes:
        name: The name of the parameter
        type: The data type of the parameter (e.g., 'string', 'integer', 'boolean')
        description: A description of the parameter
        required: Whether the parameter is required
        enum: Optional list of allowed values for the parameter
        default: Optional default value for the parameter
    """
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None


class Tool(BaseModel):
    """
    Represents a tool that can be used by an LLM.
    
    This class abstracts away the details about how the tool will be sent to the LLM's API.
    It can be converted to different formats required by various LLM providers.
    
    Attributes:
        name: Unique identifier for the tool
        description: A description of what the tool does
        parameters: List of parameters that the tool accepts
        function: Optional callable that implements the tool's functionality
        version: Optional version of the tool
        meta: Optional dictionary for additional metadata
    """
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    function: Optional[Callable] = None
    version: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)

    def add_parameter(self, 
                     name: str, 
                     type_: str, 
                     description: str, 
                     required: bool = True,
                     enum: Optional[List[Any]] = None,
                     default: Optional[Any] = None) -> 'Tool':
        """
        Add a parameter to the tool.
        
        Args:
            name: The name of the parameter
            type_: The data type of the parameter
            description: A description of the parameter
            required: Whether the parameter is required
            enum: Optional list of allowed values
            default: Optional default value
            
        Returns:
            Self for method chaining
        """
        param = ToolParameter(
            name=name,
            type=type_,
            description=description,
            required=required,
            enum=enum,
            default=default
        )
        self.parameters.append(param)
        return self
        
    class Config:
        arbitrary_types_allowed = True  # To allow the function field to be any callable