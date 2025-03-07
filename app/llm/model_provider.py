"""
Model provider interface and implementations for different LLM providers.
"""
from typing import Dict, Any, Optional, List, Union
import os
import logging
from abc import ABC, abstractmethod

from app.models.model_config import (
    ModelProviderType, BaseModelConfig, 
    HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig
)

# Configure logging
logger = logging.getLogger(__name__)

class ModelProvider(ABC):
    """Abstract base class for model providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response from the model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            
        Returns:
            Generated text response from the model
        """
        pass
    
    @abstractmethod
    def get_client(self) -> Any:
        """
        Get the underlying client for direct API access
        
        Returns:
            The provider-specific client
        """
        pass


class HuggingFaceModelProvider(ModelProvider):
    """Model provider for Hugging Face models"""
    
    def __init__(self, config: HuggingFaceModelConfig):
        """
        Initialize the Hugging Face model provider
        
        Args:
            config: Configuration for the model
        """
        self.config = config
        self._client = None
        
        # Initialize the client
        if config.use_local:
            try:
                # Import here to avoid dependencies if not using local models
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                # Set token if provided
                if config.token:
                    os.environ["HUGGINGFACE_TOKEN"] = config.token
                
                # Configure quantization if specified
                if config.quantization == '4bit':
                    kwargs = {"load_in_4bit": True}
                elif config.quantization == '8bit':
                    kwargs = {"load_in_8bit": True}
                else:
                    kwargs = {}
                
                self.tokenizer = AutoTokenizer.from_pretrained(config.model)
                self.model = AutoModelForCausalLM.from_pretrained(
                    config.model,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    **kwargs
                )
                logger.info(f'Loaded local model: {config.model}')
                
            except ImportError as e:
                logger.error(f'Failed to import required packages for local model: {e}')
                raise
            except Exception as e:
                logger.error(f'Error loading local model {config.model}: {e}')
                raise
        else:
            # Use the Hugging Face API
            try:
                from huggingface_hub import InferenceClient
                
                # Configure API token
                token = config.token or os.environ.get("HUGGINGFACE_TOKEN")
                
                # Set up the API client
                self._client = InferenceClient(
                    model=config.endpoint or config.model,
                    token=token
                )
                logger.info(f'Initialized Hugging Face API client for model: {config.model}')
                
            except ImportError as e:
                logger.error(f'Failed to import required packages: {e}')
                raise
            except Exception as e:
                logger.error(f'Error initializing Hugging Face client: {e}')
                raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using the Hugging Face model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            
        Returns:
            Generated text response from the model
        """
        try:
            if self._client:  # API mode
                # Format messages
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                
                # Add history if provided
                if history:
                    messages.extend(history)
                
                # Add current prompt
                messages.append({"role": "user", "content": prompt})
                
                # Get response
                response = self._client.chat_completion(
                    messages,
                    model=self.config.model,
                    **self.config.parameters
                )
                
                return response.choices[0].message.content
            
            else:  # Local model mode
                # Format input for local inference
                input_text = ""
                if system_message:
                    input_text += f"<|system|>\n{system_message}\n\n"
                
                # Add history if provided
                if history:
                    for msg in history:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        input_text += f"<|{role}|>\n{content}\n\n"
                
                # Add current prompt
                input_text += f"<|user|>\n{prompt}\n\n<|assistant|>\n"
                
                # Generate response
                inputs = self.tokenizer(input_text, return_tensors="pt").to("cuda")
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.parameters.get("max_length", 1024),
                    temperature=self.config.parameters.get("temperature", 0.7),
                    top_p=self.config.parameters.get("top_p", 0.95),
                    do_sample=True
                )
                
                # Decode and return only the assistant's response
                full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                assistant_response = full_response.split("<|assistant|>\n")[-1].strip()
                return assistant_response
                
        except Exception as e:
            logger.error(f'Error generating text with Hugging Face model: {e}')
            return f"Error generating response: {str(e)}"
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client or self.model


class AzureOpenAIModelProvider(ModelProvider):
    """Model provider for Azure OpenAI models"""
    
    def __init__(self, config: AzureOpenAIModelConfig):
        """
        Initialize the Azure OpenAI model provider
        
        Args:
            config: Configuration for the model
        """
        self.config = config
        
        try:
            from openai import AsyncAzureOpenAI
            
            # Get API key from config or environment
            api_key = config.api_key or os.environ.get("AZURE_OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Azure OpenAI API key not provided in config or environment")
            
            # Get endpoint from config or environment
            endpoint = config.endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
            if not endpoint:
                raise ValueError("Azure OpenAI endpoint not provided in config or environment")
            
            # Initialize the client
            self._client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version=config.api_version,
                azure_endpoint=endpoint
            )
            
            logger.info(f'Initialized Azure OpenAI client for model: {config.model} (deployment: {config.deployment_name})')
            
        except ImportError as e:
            logger.error(f'Failed to import required packages: {e}')
            raise
        except Exception as e:
            logger.error(f'Error initializing Azure OpenAI client: {e}')
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using the Azure OpenAI model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            
        Returns:
            Generated text response from the model
        """
        try:
            # Format messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add history if provided
            if history:
                messages.extend(history)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Get response
            response = await self._client.chat.completions.create(
                model=self.config.deployment_name,  # Azure uses deployment name, not model name
                messages=messages,
                **self.config.parameters
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f'Error generating text with Azure OpenAI model: {e}')
            return f"Error generating response: {str(e)}"
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client


class AnthropicModelProvider(ModelProvider):
    """Model provider for Anthropic Claude models"""
    
    def __init__(self, config: AnthropicModelConfig):
        """
        Initialize the Anthropic model provider
        
        Args:
            config: Configuration for the model
        """
        self.config = config
        
        try:
            from anthropic import AsyncAnthropic
            
            # Get API key from config or environment
            api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided in config or environment")
            
            # Initialize the client
            self._client = AsyncAnthropic(api_key=api_key)
            
            logger.info(f'Initialized Anthropic client for model: {config.model}')
            
        except ImportError as e:
            logger.error(f'Failed to import required packages: {e}')
            raise
        except Exception as e:
            logger.error(f'Error initializing Anthropic client: {e}')
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using the Anthropic model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            
        Returns:
            Generated text response from the model
        """
        try:
            # Format messages
            messages = []
            
            # Add history if provided
            if history:
                for msg in history:
                    role = msg.get("role", "user")
                    # Map roles to Anthropic format
                    if role == "system":
                        # We'll handle system prompt separately
                        continue
                    elif role == "assistant":
                        anthropic_role = "assistant"
                    else:
                        anthropic_role = "user"
                    
                    messages.append({
                        "role": anthropic_role,
                        "content": msg.get("content", "")
                    })
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Get response
            response = await self._client.messages.create(
                model=self.config.model,
                messages=messages,
                system=system_message,
                **self.config.parameters
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f'Error generating text with Anthropic model: {e}')
            return f"Error generating response: {str(e)}"
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client


class ModelProviderFactory:
    """Factory for creating model providers"""
    
    @staticmethod
    def create_provider(config: Union[HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig]) -> ModelProvider:
        """
        Create a model provider based on the configuration
        
        Args:
            config: Model configuration
            
        Returns:
            Appropriate model provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if config.provider == ModelProviderType.HUGGINGFACE:
            return HuggingFaceModelProvider(config)
        elif config.provider == ModelProviderType.AZURE_OPENAI:
            return AzureOpenAIModelProvider(config)
        elif config.provider == ModelProviderType.ANTHROPIC:
            return AnthropicModelProvider(config)
        else:
            raise ValueError(f"Unsupported model provider: {config.provider}")
