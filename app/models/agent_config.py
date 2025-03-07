"""
Agent configuration models for the agent orchestration system.
Defines workflows, tools, and activation conditions.
"""
from typing import Dict, List, Any, Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field

from app.models.model_config import ModelConfig, HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig


class WorkflowType(str, Enum):
    """Types of agent workflows"""
    RAG = 'rag'
    CHAIN = 'chain'
    ROUTING = 'routing'
    EVALUATOR = 'evaluator'
    GRAPH = 'graph'
    HYBRID = 'hybrid'


class ActivationConfig(BaseModel):
    """Configuration for when a workflow should be activated"""
    keywords: List[str] = Field(default_factory=list)
    priority: int = 1  # Higher priority workflows are checked first
    default: bool = False  # Whether this workflow is the default fallback
    min_confidence: float = 0.0  # Minimum confidence score needed to activate this workflow


class ToolConfig(BaseModel):
    """Configuration for a tool used in a workflow"""
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStepConfig(BaseModel):
    """Configuration for a step in a multi-step workflow"""
    name: str
    tool: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    use_result_as_input: bool = True


class WorkflowConfig(BaseModel):
    """Configuration for an agent workflow"""
    name: str
    description: Optional[str] = None
    type: WorkflowType = WorkflowType.RAG
    model: Optional[str] = None  # Reference to a model in the config
    activation: ActivationConfig = Field(default_factory=ActivationConfig)
    tools: List[ToolConfig] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)  # Higher-level components like graph_query_handler
    steps: List[WorkflowStepConfig] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Overall agent configuration"""
    name: str
    description: Optional[str] = None
    model_config: ModelConfig
    workflows: List[WorkflowConfig]
    
    def get_default_workflow(self) -> Optional[WorkflowConfig]:
        """Get the default workflow"""
        for workflow in self.workflows:
            if workflow.activation.default:
                return workflow
        # If no default is explicitly set, use the first workflow
        return self.workflows[0] if self.workflows else None
    
    def get_workflow_by_name(self, name: str) -> Optional[WorkflowConfig]:
        """Get a workflow by name"""
        for workflow in self.workflows:
            if workflow.name == name:
                return workflow
        return None
