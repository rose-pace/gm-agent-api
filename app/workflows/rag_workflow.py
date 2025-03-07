"""
RAG (Retrieval Augmented Generation) workflow implementation.
"""
from typing import Dict, Any, Optional, List
import logging

from app.workflows.base_workflow import BaseWorkflow, WorkflowResult
from app.llm.model_provider import ModelProvider
from app.tools.rag_tools import RAGTool

logger = logging.getLogger(__name__)

class RAGWorkflow(BaseWorkflow):
    """
    Basic RAG workflow that retrieves context and generates an answer.
    """
    
    def __init__(self, name: str, model_provider: ModelProvider, tools: Dict[str, Any] = None,
                 components: Dict[str, Any] = None, top_k: int = 3,
                 system_prompt: str = None):
        """
        Initialize the RAG workflow
        
        Args:
            name: Name of the workflow
            model_provider: LLM provider to use
            tools: Dictionary of tools available to the workflow
            components: Dictionary of higher-level components available to the workflow
            top_k: Number of documents to retrieve
            system_prompt: Optional system prompt template
        """
        super().__init__(name, model_provider, tools, components)
        self.top_k = top_k
        self.system_prompt = system_prompt or (
            'You are a helpful assistant. Answer the user\'s question based on the provided context. '
            'If you cannot find the answer in the context, say so clearly and don\'t make up information.'
        )
        
        # Validate that we have the necessary tools
        if 'rag_tool' not in self.tools:
            raise ValueError('RAG workflow requires rag_tool')
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the RAG workflow
        
        Args:
            query: User query text
            context: Additional context information
            
        Returns:
            Workflow execution result
        """
        try:
            # Get the RAG tool
            rag_tool = self.tools['rag_tool']
            
            # Retrieve relevant documents
            context_str = None
            if context:
                context_str = str(context)
                
            rag_result = await rag_tool.retrieve(
                query=query,
                context=context_str,
                top_k=self.top_k
            )
            
            # Prepare the prompt for the model
            retrieved_context = rag_result.text if rag_result else ''
            
            prompt = f"Question: {query}\n\nRelevant Context:\n{retrieved_context}\n\nAnswer:"
            
            # Generate the answer
            answer = await self._generate(prompt, self.system_prompt)
            
            # Prepare sources
            sources = rag_result.sources if rag_result else []
            
            # Return the result
            return WorkflowResult(
                answer=answer,
                sources=sources,
                confidence=0.8  # Fixed confidence for now
            )
            
        except Exception as e:
            logger.error(f'Error executing RAG workflow: {e}')
            return WorkflowResult(
                answer=f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                confidence=0.0
            )
