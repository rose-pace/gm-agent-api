"""
Base workflow interface for agent workflows.
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from app.llm.model_provider import ModelProvider


class WorkflowResult:
    """Result from a workflow execution"""
    
    def __init__(self, answer: str, sources: List[Dict[str, Any]] = None, 
                 metadata: Dict[str, Any] = None, confidence: float = 1.0):
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


class BaseWorkflow(ABC):
    """Base class for all workflows"""
    
    def __init__(self, name: str, model_provider: ModelProvider, tools: Dict[str, Any] = None,
                 components: Dict[str, Any] = None):
        """
        Initialize the workflow
        
        Args:
            name: Name of the workflow
            model_provider: LLM provider to use
            tools: Dictionary of tools available to the workflow
            components: Dictionary of higher-level components available to the workflow
        """
        self.name = name
        self.model_provider = model_provider
        self.tools = tools or {}
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
                      history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate text using the model provider
        
        Args:
            prompt: User query to send to the model
            system_message: Optional system message
            history: Optional conversation history
            
        Returns:
            Generated text response
        """
        return await self.model_provider.generate(prompt, system_message, history)
