"""
Model configuration models for the agent orchestration system.
Defines the available LLM providers and their configuration parameters.
"""
from typing import Dict, Any, Optional, List, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ModelProviderType(str, Enum):
    """Supported model providers"""
    HUGGINGFACE = 'huggingface'
    AZURE_OPENAI = 'azure_openai'
    ANTHROPIC = 'anthropic'
    GITHUB_OPENAI = 'github_openai'
    AZURE_AI_INFERENCE = 'azure_ai_inference'


class BaseModelConfig(BaseModel):
    """Base configuration for all model providers"""
    name: str
    provider: ModelProviderType
    model: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class HuggingFaceModelConfig(BaseModelConfig):
    """Configuration for Hugging Face models"""
    provider: Literal[ModelProviderType.HUGGINGFACE] = ModelProviderType.HUGGINGFACE
    endpoint: Optional[str] = None  # Optional API endpoint for hosted inference
    use_local: bool = False  # Whether to load model locally
    token: Optional[str] = None  # API token for Hugging Face
    quantization: Optional[str] = None  # Optional quantization setting (e.g., '4bit', '8bit')
    
    @field_validator('parameters')
    def validate_parameters(cls, v):
        """Ensure required parameters have defaults if not provided"""
        defaults = {
            'temperature': 0.7,
            'max_tokens': 1024,
            'top_p': 0.95,
        }
        
        for key, value in defaults.items():
            if key not in v:
                v[key] = value
        
        return v


class AzureOpenAIModelConfig(BaseModelConfig):
    """Configuration for Azure OpenAI models"""
    provider: Literal[ModelProviderType.AZURE_OPENAI] = ModelProviderType.AZURE_OPENAI
    api_key: Optional[str] = None  # Will be loaded from env if not provided
    api_version: str = '2023-05-15'
    deployment_name: str
    endpoint: Optional[str] = None
    
    @field_validator('parameters')
    def validate_parameters(cls, v):
        """Ensure required parameters have defaults if not provided"""
        defaults = {
            'temperature': 0.7,
            'max_tokens': 800,
            'top_p': 0.95,
        }
        
        for key, value in defaults.items():
            if key not in v:
                v[key] = value
        
        return v


class AnthropicModelConfig(BaseModelConfig):
    """Configuration for Anthropic Claude models"""
    provider: Literal[ModelProviderType.ANTHROPIC] = ModelProviderType.ANTHROPIC
    api_key: Optional[str] = None  # Will be loaded from env if not provided
    
    @field_validator('parameters')
    def validate_parameters(cls, v):
        """Ensure required parameters have defaults if not provided"""
        defaults = {
            'temperature': 0.7,
            'max_tokens_to_sample': 1000,
            'top_p': 0.95,
        }
        
        for key, value in defaults.items():
            if key not in v:
                v[key] = value
        
        return v


class GitHubOpenAIModelConfig(BaseModelConfig):
    """Configuration for GitHub models through OpenAI framework"""
    provider: Literal[ModelProviderType.GITHUB_OPENAI] = ModelProviderType.GITHUB_OPENAI
    endpoint: str = 'https://models.inference.ai.azure.com'  # Default endpoint for GitHub models
    api_key: Optional[str] = None  # Will be loaded from GITHUB_TOKEN env if not provided
    
    @field_validator('parameters')
    def validate_parameters(cls, v):
        """Ensure required parameters have defaults if not provided"""
        defaults = {
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 0.95,
        }
        
        for key, value in defaults.items():
            if key not in v:
                v[key] = value
        
        return v


class AzureAIInferenceModelConfig(BaseModelConfig):
    """Configuration for Azure AI Inference service models"""
    provider: Literal[ModelProviderType.AZURE_AI_INFERENCE] = ModelProviderType.AZURE_AI_INFERENCE
    endpoint: str  # Required endpoint URL
    api_key: Optional[str] = None  # Will be loaded from env if not provided
    api_version: str = '2023-10-01-preview'  # Default API version
    deployment_name: Optional[str] = None  # Optional deployment name
    
    @field_validator('parameters')
    def validate_parameters(cls, v):
        """Ensure required parameters have defaults if not provided"""
        defaults = {
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 0.95,
        }
        
        for key, value in defaults.items():
            if key not in v:
                v[key] = value
        
        return v


class ModelConfig(BaseModel):
    """Combined model configuration"""
    default_llm: Union[str, HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig, GitHubOpenAIModelConfig, AzureAIInferenceModelConfig]
    models: List[Union[HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig, GitHubOpenAIModelConfig, AzureAIInferenceModelConfig]] = Field(default_factory=list)

    def get_model_by_name(self, name: str) -> Optional[Union[HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig, GitHubOpenAIModelConfig, AzureAIInferenceModelConfig]]:
        """Get a model configuration by name"""
        for model in self.models:
            if model.name == name:
                return model
        return None
    
    def get_default_model(self) -> Optional[Union[HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig, GitHubOpenAIModelConfig, AzureAIInferenceModelConfig]]:
        """
        Get the default model configuration.
        
        Returns:
            The default model configuration object
        """
        if isinstance(self.default_llm, str):
            return self.get_model_by_name(self.default_llm)
        return self.default_llm
