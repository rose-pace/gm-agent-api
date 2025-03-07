"""
Graph query workflow implementation.
"""
from typing import Dict, Any, Optional, List
import logging

from app.workflows.base_workflow import BaseWorkflow, WorkflowResult
from app.llm.model_provider import ModelProvider
from app.tools.graph_query_handler import GraphQueryHandler

logger = logging.getLogger(__name__)

class GraphWorkflow(BaseWorkflow):
    """
    Workflow for answering questions about entities and relationships in the graph database.
    """
    
    def __init__(self, name: str, model_provider: ModelProvider, tools: Dict[str, Any] = None,
                 components: Dict[str, Any] = None, system_prompt: str = None):
        """
        Initialize the graph workflow
        
        Args:
            name: Name of the workflow
            model_provider: LLM provider to use
            tools: Dictionary of tools available to the workflow
            components: Dictionary of higher-level components available to the workflow
            system_prompt: Optional system prompt template
        """
        super().__init__(name, model_provider, tools, components)
        self.system_prompt = system_prompt or (
            'You are a helpful assistant with expertise in analyzing relationships between entities. '
            'Use the graph information provided to answer questions about relationships, '
            'connections, and properties of entities.'
        )
        
        # Validate that we have the necessary components
        if 'graph_query_handler' not in self.components:
            raise ValueError('Graph workflow requires graph_query_handler component')
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the graph workflow
        
        Args:
            query: User query text about graph entities and relationships
            context: Additional context information
            
        Returns:
            Workflow execution result
        """
        try:
            # Get the graph query handler
            graph_handler = self.components['graph_query_handler']
            
            # Get direct answer from graph
            graph_answer = await graph_handler.answer_query(query)
            
            # If we got a useful answer from the graph, return it
            if graph_answer and not graph_answer.startswith("I couldn't"):
                # Return the result without LLM processing
                return WorkflowResult(
                    answer=graph_answer,
                    sources=[{"type": "graph_database", "content": "Information from graph database"}],
                    confidence=0.9
                )
                
            # If we didn't get a useful answer, use the LLM to help interpret
            prompt = (
                f"Question about entities and relationships: {query}\n\n"
                f"Graph database information: {graph_answer}\n\n"
                "Please provide a helpful response based on this information."
            )
            
            # Generate the answer
            answer = await self._generate(prompt, self.system_prompt)
            
            # Return the result
            return WorkflowResult(
                answer=answer,
                sources=[{"type": "graph_database", "content": "Information from graph database"}],
                confidence=0.7  # Lower confidence since we needed the LLM to interpret
            )
            
        except Exception as e:
            logger.error(f'Error executing Graph workflow: {e}')
            return WorkflowResult(
                answer=f"I'm sorry, I encountered an error while processing your graph query: {str(e)}",
                confidence=0.0
            )
