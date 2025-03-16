from typing import Dict, List, Any, Union
from app.models.tool_use import Tool, ToolParameter

"""
Utility module for converting Tool objects to formats required by different LLM providers.
"""



def convert_to_openai_format(tools: List[Tool]) -> List[Dict[str, Any]]:
    """
    Convert Tool objects to OpenAI tools format.
    
    Args:
        tools: List of Tool objects to convert
        
    Returns:
        List of tool specifications in OpenAI's format
    """
    openai_tools = []
    
    for tool in tools:
        tool_spec = {
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
        }
        
        for param in tool.parameters:
            tool_spec['function']['parameters']['properties'][param.name] = {
                'type': param.type,
                'description': param.description
            }
            
            if param.enum is not None:
                tool_spec['function']['parameters']['properties'][param.name]['enum'] = param.enum
                
            if param.default is not None:
                tool_spec['function']['parameters']['properties'][param.name]['default'] = param.default
                
            if param.required:
                tool_spec['function']['parameters']['required'].append(param.name)
        
        openai_tools.append(tool_spec)
    
    return openai_tools


def convert_to_anthropic_format(tools: List[Tool]) -> Dict[str, Any]:
    """
    Convert Tool objects to Anthropic tools format.
    
    Args:
        tools: List of Tool objects to convert
        
    Returns:
        Dictionary containing tools specification in Anthropic's format
    """
    anthropic_tools = {
        'tools': []
    }
    
    for tool in tools:
        tool_spec = {
            'name': tool.name,
            'description': tool.description,
            'input_schema': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }
        
        for param in tool.parameters:
            tool_spec['input_schema']['properties'][param.name] = {
                'type': param.type,
                'description': param.description
            }
            
            if param.enum is not None:
                tool_spec['input_schema']['properties'][param.name]['enum'] = param.enum
                
            if param.default is not None:
                tool_spec['input_schema']['properties'][param.name]['default'] = param.default
                
            if param.required:
                tool_spec['input_schema']['required'].append(param.name)
        
        anthropic_tools['tools'].append(tool_spec)
    
    return anthropic_tools


def convert_to_huggingface_format(tools: List[Tool]) -> List[Dict[str, Any]]:
    """
    Convert Tool objects to HuggingFace tools format.
    
    Args:
        tools: List of Tool objects to convert
        
    Returns:
        List of tool specifications in HuggingFace's format
    """
    huggingface_tools = []
    
    for tool in tools:
        tool_spec = {
            'name': tool.name,
            'description': tool.description,
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }
        
        for param in tool.parameters:
            tool_spec['parameters']['properties'][param.name] = {
                'type': param.type,
                'description': param.description
            }
            
            if param.enum is not None:
                tool_spec['parameters']['properties'][param.name]['enum'] = param.enum
                
            if param.default is not None:
                tool_spec['parameters']['properties'][param.name]['default'] = param.default
                
            if param.required:
                tool_spec['parameters']['required'].append(param.name)
        
        huggingface_tools.append(tool_spec)
    
    return huggingface_tools


def get_provider_format(tools: List[Tool], provider: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert Tool objects to the appropriate format for the specified provider.
    
    Args:
        tools: List of Tool objects to convert
        provider: The model provider name ('openai', 'anthropic', or 'huggingface')
        
    Returns:
        Tool specifications in the provider's required format
        
    Raises:
        ValueError: If an unsupported provider is specified
    """
    provider = provider.lower()
    
    if provider in ('azure_openai', 'openai', 'azureopenai'):
        return convert_to_openai_format(tools)
    elif provider == 'anthropic':
        return convert_to_anthropic_format(tools)
    elif provider == 'huggingface':
        return convert_to_huggingface_format(tools)
    else:
        raise ValueError(f'Unsupported provider: {provider}')