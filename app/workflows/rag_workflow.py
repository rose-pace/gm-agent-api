"""
RAG (Retrieval Augmented Generation) workflow implementation.
"""
from typing import Dict, Any, Optional, List
import logging

from app.workflows.base_workflow import BaseWorkflow, WorkflowResult

# Configure logging
logger = logging.getLogger(__name__)

class RAGWorkflow(BaseWorkflow):
    """RAG workflow implementation that retrieves context and generates responses"""
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the RAG workflow
        
        Args:
            query: User query
            context: Optional context information
            
        Returns:
            Workflow result with the answer and sources
        """
        context = context or {}
        
        # Get RAG tool
        rag_tool = None
        for tool in self.components.values():
            if hasattr(tool, 'retrieve') and callable(getattr(tool, 'retrieve')):
                rag_tool = tool
                break
        
        if not rag_tool:
            logger.warning("No RAG tool found in components")
            # Fall back to simple LLM query without retrieval
            response = await self._generate(query)
            return WorkflowResult(
                answer=response.content or "I couldn't retrieve relevant information for your query.",
                confidence=0.5
            )
        
        # Retrieve relevant documents
        try:
            retrieval_results = await rag_tool.retrieve(query)
            documents = retrieval_results.get('documents', [])
            sources = retrieval_results.get('sources', [])
            
            if not documents:
                logger.info("No relevant documents found")
                response = await self._generate(query)
                return WorkflowResult(
                    answer=response.content or "I couldn't find any relevant information for your query.",
                    confidence=0.5
                )
            
            # Create prompt with retrieved context
            context_str = "\n\n".join(documents)
            prompt = f"Use the following information to answer the question:\n\n{context_str}\n\nQuestion: {query}\n\nAnswer:"
            
            # Generate response with context
            response = await self._generate(prompt)
            
            # Check if the model wants to use tools
            if response.is_tool_call:
                # If the model wants to use tools, handle them
                final_response = await self.handle_tool_calls(response, query)
                result_text = final_response.content
            else:
                # Otherwise, use the text response
                result_text = response.content
            
            # Create the workflow result
            return WorkflowResult(
                answer=result_text or "I couldn't generate an answer from the retrieved information.",
                sources=sources,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error in RAG workflow: {e}", exc_info=True)
            response = await self._generate(query)
            return WorkflowResult(
                answer=response.content or f"An error occurred: {str(e)}",
                confidence=0.2
            )
    
    async def handle_tool_calls(self, response, prompt):
        """Handle any tool calls by executing them and getting a final response"""
        # Keep track of all tool results to send back to the model
        all_tool_results = []
        
        # Process all tool calls
        for tool_call in response.tool_calls:
            tool_result = await self.execute_tool({
                'tool_name': tool_call.tool_name,
                'arguments': tool_call.arguments,
                'tool_call_id': tool_call.tool_call_id
            })
            all_tool_results.append(tool_result)
            
        # Now send the tool results back to the model for a final response
        logger.info(f"Sending {len(all_tool_results)} tool results back to the model")
        final_response = await self._generate(
            prompt=prompt,
            tool_results=all_tool_results
        )
        
        return final_response
