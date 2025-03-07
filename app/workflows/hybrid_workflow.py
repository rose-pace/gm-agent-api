"""
Hybrid workflow combining RAG and graph querying for comprehensive answers.
"""
from typing import Dict, Any, Optional, List
import logging

from app.workflows.base_workflow import BaseWorkflow, WorkflowResult
from app.llm.model_provider import ModelProvider
from app.tools.rag_tools import RAGTool
from app.tools.graph_query_tool import GraphQueryTool

logger = logging.getLogger(__name__)

class HybridWorkflow(BaseWorkflow):
    """
    Workflow that combines RAG retrieval with graph database queries.
    """
    
    def __init__(self, name: str, model_provider: ModelProvider, tools: Dict[str, Any] = None,
                 components: Dict[str, Any] = None, top_k: int = 3,
                 system_prompt: str = None):
        """
        Initialize the hybrid workflow
        
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
            'You are a helpful assistant with access to both knowledge documents and '
            'entity relationship information. Use both sources to provide comprehensive answers. '
            'When appropriate, explain connections between entities mentioned in the question.'
        )
        
        # Validate that we have the necessary tools
        if 'rag_tool' not in self.tools:
            raise ValueError('Hybrid workflow requires rag_tool')
        if 'graph_query_tool' not in self.tools:
            raise ValueError('Hybrid workflow requires graph_query_tool')
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the hybrid workflow combining RAG and graph queries
        
        Args:
            query: User query text
            context: Additional context information
            
        Returns:
            Workflow execution result
        """
        try:
            # Step 1: Get RAG results
            rag_tool = self.tools['rag_tool']
            graph_tool = self.tools['graph_query_tool']
            
            # Retrieve relevant documents
            context_str = None
            if context:
                context_str = str(context)
                
            rag_result = await rag_tool.retrieve(
                query=query,
                context=context_str,
                top_k=self.top_k
            )
            
            # Step 2: Enrich with graph data
            enriched_result = await graph_tool.enrich_rag_results(rag_result)
            
            # Step 3: Extract potential entities to query directly from the graph
            # This is a simple implementation - we would use NER in production
            potential_entities = self._extract_potential_entities(query)
            
            graph_context = ""
            graph_sources = []
            
            # Step 4: Get entity information from graph
            for entity in potential_entities:
                entity_data = await graph_tool.get_entity(entity)
                if entity_data:
                    graph_context += f"Entity information for '{entity}':\n"
                    graph_context += f"{entity_data['name']} ({entity_data['type']})\n"
                    for key, value in entity_data.get('properties', {}).items():
                        if key != 'description':
                            graph_context += f"- {key}: {value}\n"
                    
                    # Get relationships
                    related = await graph_tool.get_related_entities(entity_data['id'])
                    if related:
                        graph_context += f"Related to {entity_data['name']}:\n"
                        for rel in related[:3]:  # Limit to top 3 relationships
                            rel_type = rel.get('relationship', {}).get('name', 'connected to')
                            graph_context += f"- {rel['name']} ({rel_type})\n"
                    
                    graph_context += "\n"
                    graph_sources.append({
                        "type": "graph_entity", 
                        "name": entity_data['name'],
                        "id": entity_data['id']
                    })
            
            # Step 5: Prepare the prompt combining both sources
            rag_context = enriched_result.text if enriched_result else ''
            
            prompt = (
                f"Question: {query}\n\n"
                f"Document Knowledge:\n{rag_context}\n\n"
            )
            
            if graph_context:
                prompt += f"Entity Information:\n{graph_context}\n\n"
                
            prompt += "Please provide a comprehensive answer that integrates both document knowledge and entity information:"
            
            # Step 6: Generate the answer
            answer = await self._generate(prompt, self.system_prompt)
            
            # Step 7: Prepare combined sources
            sources = enriched_result.sources if enriched_result else []
            sources.extend(graph_sources)
            
            # Return the result
            return WorkflowResult(
                answer=answer,
                sources=sources,
                metadata={"workflow_type": "hybrid"},
                confidence=0.85  # Higher confidence due to multiple sources
            )
            
        except Exception as e:
            logger.error(f'Error executing Hybrid workflow: {e}', exc_info=True)
            return WorkflowResult(
                answer=f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                confidence=0.0
            )
    
    def _extract_potential_entities(self, query: str) -> List[str]:
        """
        Extract potential entity names from the query
        
        Args:
            query: The user query
            
        Returns:
            List of potential entity names
        """
        # Simple extraction based on capitalized words
        # In a production system, we would use NER or more sophisticated methods
        words = query.split()
        entities = []
        
        for word in words:
            # Check if word starts with capital letter and isn't at the beginning of the sentence
            if word[0].isupper() and word not in ["I", "I'm", "I've", "I'll", "I'd"]:
                # Remove punctuation
                clean_word = word.rstrip(',.?!:;')
                if clean_word:
                    entities.append(clean_word)
                    
        # Also consider 2-word entities (very simplified approach)
        for i in range(len(words) - 1):
            if words[i][0].isupper() and words[i+1][0].isupper():
                entities.append(f"{words[i]} {words[i+1]}".rstrip(',.?!:;'))
                
        return entities