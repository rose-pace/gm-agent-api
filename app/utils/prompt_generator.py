from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.utils.prompt_templates import prompt_library, render_prompt, load_prompt_templates

class Tool(BaseModel):
    """
    Represents a tool that can be used by the agent.
    """
    name: str
    description: str


class AgentInstructionParams(BaseModel):
    """
    Parameters for generating agent instructions.
    """
    game_system: Optional[str] = None
    campaign_setting: Optional[str] = None
    tools: Optional[List[Tool]] = None
    additional_instructions: Optional[str] = None


class RAGQueryParams(BaseModel):
    """
    Parameters for generating RAG queries.
    """
    user_query: str
    context: Optional[str] = None
    query_type: str = 'specific'  # 'specific', 'creative', or 'rules'


def generate_agent_instruction(params: AgentInstructionParams) -> str:
    """
    Generate agent instruction prompt based on provided parameters.
    
    Args:
        params: Parameters for the instruction
        
    Returns:
        Rendered instruction prompt
    """
    return render_prompt('agent_instruction', **params.model_dump(exclude_none=True))


def generate_rag_query(params: RAGQueryParams) -> str:
    """
    Generate a RAG query prompt based on provided parameters.
    
    Args:
        params: Parameters for the RAG query
        
    Returns:
        Rendered RAG query prompt
    """
    return render_prompt('rag_query', **params.model_dump(exclude_none=True))


def initialize_prompts() -> None:
    """
    Initialize all prompt templates.
    """
    load_prompt_templates()
