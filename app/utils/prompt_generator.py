from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.utils.prompt_templates import prompt_library, render_prompt, load_prompt_templates

class AgentInstructionParams(BaseModel):
    """
    Parameters for generating agent instructions.
    """
    game_system: Optional[str] = None
    campaign_setting: Optional[str] = None
    additional_instructions: Optional[str] = None

class PromptParams(BaseModel):
    """
    Parameters for generating a prompt.
    """

class RAGQueryParams(BaseModel):
    """
    Parameters for generating RAG queries.
    """
    user_query: str
    context: Optional[str] = None
    query_type: str = 'specific'  # 'specific', 'creative', or 'rules'


def generate_agent_instruction(template_name: str, params: AgentInstructionParams) -> str:
    """
    Generate agent instruction prompt based on provided parameters.
    
    Args:
        params: Parameters for the instruction
        
    Returns:
        Rendered instruction prompt
    """
    return render_prompt(template_name, **params.model_dump(exclude_none=True))

def generate_prompt(template_name: str, params: Dict[str, Any]) -> str:
    """
    Generate a prompt based on the provided template and parameters.
    
    Args:
        template_name: Name of the template to use
        params: Parameters for the prompt
    """
    return render_prompt(template_name, **params)


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
