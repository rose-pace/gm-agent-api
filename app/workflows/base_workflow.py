"""
Base workflow interface for agent workflows.
"""
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import logging

from app.llm.model_provider import ModelProvider
from app.models.tool_use import Tool
from app.models.model_response import ModelResponse

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowResult:
    """Result from a workflow execution"""
    
    def __init__(self, answer: str, sources: List[Dict[str, Any]] = None, 
                 metadata: Dict[str, Any] = None, confidence: float = 0.0, history: List[Dict[str, Any]] = None):
        """
        Initialize a workflow result
        
        Args:
            answer: The generated answer text
            sources: Optional list of source references
            metadata: Optional additional metadata about the result
            confidence: Confidence score (0-1)
        """
        self.answer = answer
        self.sources = sources or []
        self.metadata = metadata or {}
        self.confidence = confidence
        self.history = history


class BaseWorkflow(ABC):
    """Base class for all workflows"""
    
    def __init__(self, name: str, model_provider: ModelProvider, tools: List[Tool] = None,
                 components: Dict[str, Any] = None):
        """
        Initialize the workflow
        
        Args:
            name: Name of the workflow
            model_provider: LLM provider to use
            tools: List of tools available to the workflow
            components: Dictionary of higher-level components available to the workflow
        """
        self.name = name
        self.model_provider = model_provider
        self.tools = tools or []
        self.components = components or {}
    
    @abstractmethod
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the workflow
        
        Args:
            query: User query text
            context: Additional context
            
        Returns:
            Workflow execution result
        """
        pass
    
    async def _generate(self, prompt: str, system_message: Optional[str] = None, 
                      history: Optional[List[Dict[str, str]]] = None,
                      tool_results: Optional[List[Dict[str, Any]]] = None) -> ModelResponse:
        """
        Generate text using the model provider
        
        Args:
            prompt: User query to send to the model
            system_message: Optional system message
            history: Optional conversation history
            tool_results: Optional tool execution results to pass back to the model
            
        Returns:
            ModelResponse containing either text content or tool call requests
        """
        return await self.model_provider.generate(
            prompt=prompt, 
            system_message=system_message, 
            history=history, 
            tools=self.tools,
            tool_results=tool_results
        )
    
    async def execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool based on a tool call
        
        Args:
            tool_call: Tool call information including name and arguments
            
        Returns:
            Dictionary containing the tool execution result
            
        Raises:
            ValueError: If the tool is not found
        """
        tool_name = tool_call.get('tool_name')
        arguments = tool_call.get('arguments', {})
        tool_call_id = tool_call.get('tool_call_id')
        
        logger.info(f'Executing tool: {tool_name} with args: {arguments}')
        
        # Find the tool with the specified name
        tool = None
        for t in self.tools:
            if t.name == tool_name:
                tool = t
                break
        
        if not tool:
            error_msg = f'Tool not found: {tool_name}'
            logger.warning(error_msg)
            return {
                'name': tool_name,
                'result': error_msg,
                'tool_call_id': tool_call_id
            }
        
        # Execute the tool
        try:
            if tool.function:
                result = await tool.function(**arguments) if callable(tool.function) else tool.function
                return {
                    'name': tool_name,
                    'result': result,
                    'arguments': arguments,
                    'tool_call_id': tool_call_id
                }
            else:
                error_msg = f'Tool {tool_name} has no function implementation'
                logger.warning(error_msg)
                return {
                    'name': tool_name,
                    'result': error_msg,
                    'arguments': arguments,
                    'tool_call_id': tool_call_id
                }
                
        except Exception as e:
            error_msg = f'Error executing tool {tool_name}: {str(e)}'
            logger.error(error_msg, exc_info=True)
            return {
                'name': tool_name,
                'result': error_msg,
                'arguments': arguments,
                'tool_call_id': tool_call_id
            }
