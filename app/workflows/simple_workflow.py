"""
Workflow for handling tool-using conversations with LLMs.
"""
import os
from typing import Dict, Any, Optional, List
import logging
import json

from app.workflows.base_workflow import BaseWorkflow, WorkflowResult
from app.models.model_response import ModelResponse
from app.llm.model_provider import ModelProvider
from app.utils.prompt_generator import generate_agent_instruction, AgentInstructionParams

# Configure logging
logger = logging.getLogger(__name__)

class SimpleWorkflow(BaseWorkflow):
    """
    Workflow that manages tool execution with LLMs that support function calling.
    """
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the tool execution workflow
        
        Args:
            query: User query
            context: Optional context information
            
        Returns:
            Workflow result with the final answer
        """
        context = context or {}
        system_message = generate_agent_instruction(
            'simple_instruction',
            AgentInstructionParams(
                game_system=os.environ.get('GAME_SYSTEM'),
                campaign_setting=os.environ.get('CAMPAIGN_SETTING')
            )
        )
        history = context.get('history', [])
        
        # Get the initial model response
        response = await self._generate(query, system_message, history)

        history = response.history
        
        # If the model wants to use tools, execute them and continue the conversation
        if response.is_tool_call:
            # Process all tool calls and get final response
            final_response = await self._handle_tool_calls(response, query, system_message, history)
        else:
            # No tools needed, use initial response
            final_response = response
        
        # Create the workflow result
        result = WorkflowResult(
            answer=final_response.content or "I couldn't generate a proper response.",
            metadata={
                'used_tools': final_response.is_tool_call,
                'raw_response': str(final_response.raw_response)
            },
            history=final_response.history
        )
        
        return result
    
    async def _handle_tool_calls(self, response: ModelResponse, prompt: str, 
                              system_message: Optional[str] = None,
                              history: Optional[List[Dict[str, str]]] = None, 
                              max_iterations: int = 5) -> ModelResponse:
        """
        Handle tool calls and follow-up with the model
        
        Args:
            response: Model response containing tool calls
            prompt: Original user prompt
            system_message: Optional system message
            history: Optional conversation history
            max_iterations: Maximum number of tool-calling iterations
            
        Returns:
            Final model response after tool execution
        """
        iteration = 0
        current_response = response
        all_tool_results = []
        
        while current_response.is_tool_call and iteration < max_iterations:
            iteration += 1
            logger.info(f"Tool calling iteration {iteration}/{max_iterations}")
            
            # Execute all tools in the current response
            for tool_call in current_response.tool_calls:
                tool_result = await self.execute_tool({
                    'tool_name': tool_call.tool_name,
                    'arguments': tool_call.arguments,
                    'tool_call_id': tool_call.tool_call_id
                })
                all_tool_results.append(tool_result)
            
            # Get the next response with tool results
            current_response = await self._generate(
                prompt=prompt,
                system_message=system_message,
                history=history,
                tool_results=all_tool_results
            )

            history = current_response.history
        
        if iteration >= max_iterations:
            logger.warning(f"Reached maximum tool calling iterations ({max_iterations})")
            # If we hit the limit, create a text response informing about the limit
            current_response = ModelResponse(
                content=f"I've used tools multiple times but couldn't complete the task within the {max_iterations} iteration limit. Here's what I've learned so far: " + 
                (current_response.content or "No final conclusion reached."),
                raw_response=current_response.raw_response
            )
        
        return current_response
