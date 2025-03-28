"""
Model provider interface and implementations for different LLM providers.
"""
from typing import Dict, Any, Optional, List, Union
import os
import logging
import json
from abc import ABC, abstractmethod

from app.models.configuration import (
    ModelProviderType, BaseModelConfig, 
    HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig,
    GitHubOpenAIModelConfig, AzureAIInferenceModelConfig
)
from app.models.tool_use import Tool
from app.models.model_response import ModelResponse, ToolCall
from app.utils.tool_use_converter import get_provider_format

# Configure logging
logger = logging.getLogger(__name__)

class ModelProvider(ABC):
    """Abstract base class for model providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None,
                     tools: Optional[List[Tool]] = None,
                     tool_results: Optional[List[Dict[str, Any]]] = None) -> ModelResponse:
        """
        Generate a response from the model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            
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
                    os.environ["HUGGINGFACEHUB_API_TOKEN"] = config.token
                
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
                logger.error(f'Failed to import required packages for local model: {e}', exc_info=True)
                raise
            except Exception as e:
                logger.error(f'Error loading local model {config.model}: {e}', exc_info=True)
                raise
        else:
            # Use the Hugging Face API
            try:
                from huggingface_hub import InferenceClient
                
                # Configure API token
                token = config.token or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
                
                # Set up the API client
                self._client = InferenceClient(
                    provider="hf-inference",
                    model=config.endpoint or config.model,
                    token=token
                )
                logger.info(f'Initialized Hugging Face API client for model: {config.model}')
                
            except ImportError as e:
                logger.error(f'Failed to import required packages: {e}', exc_info=True)
                raise
            except Exception as e:
                logger.error(f'Error initializing Hugging Face client: {e}', exc_info=True)
                raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None,
                     tools: Optional[List[Tool]] = None) -> str:
        """
        Generate a response using the Hugging Face model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            
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
                
                # Prepare API call parameters
                api_params = dict(self.config.parameters)
                
                # Add tools if provided
                if tools:
                    try:
                        formatted_tools = get_provider_format(tools, 'huggingface')
                        api_params['tools'] = formatted_tools
                    except Exception as e:
                        logger.warning(f'Error formatting tools for Hugging Face: {e}')
                
                # Get response
                response = self._client.chat_completion(
                    messages,
                    model=self.config.model,
                    **api_params
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
            logger.error(f'Error generating text with Hugging Face model: {e}', exc_info=True)
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
            logger.error(f'Failed to import required packages: {e}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'Error initializing Azure OpenAI client: {e}', exc_info=True)
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None,
                     tools: Optional[List[Tool]] = None) -> str:
        """
        Generate a response using the Azure OpenAI model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            
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
            
            # Prepare API call parameters
            api_params = dict(self.config.parameters)
            
            # Add tools if provided
            if tools:
                try:
                    formatted_tools = get_provider_format(tools, 'azure_openai')
                    api_params['tools'] = formatted_tools
                except Exception as e:
                    logger.warning(f'Error formatting tools for Azure OpenAI: {e}')
            
            # Get response
            response = await self._client.chat.completions.create(
                model=self.config.deployment_name,  # Azure uses deployment name, not model name
                messages=messages,
                **api_params
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f'Error generating text with Azure OpenAI model: {e}', exc_info=True)
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
            logger.error(f'Failed to import required packages: {e}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'Error initializing Anthropic client: {e}', exc_info=True)
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None,
                     tools: Optional[List[Tool]] = None) -> str:
        """
        Generate a response using the Anthropic model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            
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
            
            # Prepare API call parameters
            api_params = dict(self.config.parameters)
            
            # Add tools if provided
            if tools:
                try:
                    formatted_tools = get_provider_format(tools, 'anthropic')
                    # Anthropic expects tools in a specific format
                    api_params.update(formatted_tools)
                except Exception as e:
                    logger.warning(f'Error formatting tools for Anthropic: {e}')
            
            # Get response
            response = await self._client.messages.create(
                model=self.config.model,
                messages=messages,
                system=system_message,
                **api_params
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f'Error generating text with Anthropic model: {e}', exc_info=True)
            return f"Error generating response: {str(e)}"
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client


class GitHubOpenAIModelProvider(ModelProvider):
    """Model provider for GitHub models through OpenAI interface"""
    
    def __init__(self, config: GitHubOpenAIModelConfig):
        """
        Initialize the GitHub OpenAI model provider
        
        Args:
            config: Configuration for the model
        """
        self.config = config
        
        try:
            from openai import AsyncOpenAI
            
            # Get API key from config or environment
            api_key = config.api_key or os.environ.get('GITHUB_TOKEN')
            if not api_key:
                raise ValueError('GitHub API token not provided in config or environment (GITHUB_TOKEN)')
            
            # Initialize the client
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=config.endpoint
            )
            
            logger.info(f'Initialized GitHub OpenAI client for model: {config.model}')
            
        except ImportError as e:
            logger.error(f'Failed to import required packages: {e}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'Error initializing GitHub OpenAI client: {e}', exc_info=True)
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, str]]] = None,
                     tools: Optional[List[Tool]] = None,
                     tool_results: Optional[List[Dict[str, Any]]] = None) -> ModelResponse:
        """
        Generate a response using the GitHub OpenAI model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            
        Returns:
            Generated text response from the model
        """
        try:
            # Format messages
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            
            # Add history if provided
            if history:
                messages.extend(history)

            if tool_results:
                for result in tool_results:
                    messages.append({'role': 'tool', 'tool_call_id': result.get('tool_call_id', ''), 'content': result.get('result', '')})
            
            # Add current prompt
            if prompt:
                messages.append({'role': 'user', 'content': prompt})
            
            # Prepare API call parameters
            api_params = dict(self.config.parameters)
            
            # Add tools if provided
            if tools:
                try:
                    formatted_tools = get_provider_format(tools, 'openai')
                    api_params['tools'] = formatted_tools
                except Exception as e:
                    logger.warning(f'Error formatting tools for GitHub OpenAI: {e}')
            
            # Get response
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                **api_params
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f'Error generating text with GitHub OpenAI model: {e}', exc_info=True)
            return f'Error generating response: {str(e)}'
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client


class AzureAIInferenceModelProvider(ModelProvider):
    """Model provider for Azure AI Inference API"""
    
    def __init__(self, config: AzureAIInferenceModelConfig):
        """
        Initialize the Azure AI Inference model provider
        
        Args:
            config: Configuration for the model
        """
        self.config = config
        
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            # Get API key from config or environment
            endpoint = config.endpoint or os.environ.get('AZURE_AI_INFERENCE_ENDPOINT')
            api_key = config.api_key or os.environ.get('AZURE_AI_INFERENCE_API_KEY') or os.environ.get('GITHUB_TOKEN')
            if not api_key:
                raise ValueError('Azure AI Inference API key not provided in config or environment (AZURE_AI_INFERENCE_API_KEY) or (GITHUB_TOKEN)')
            
            # Initialize the client
            self._client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            
            logger.info(f'Initialized Azure AI Inference client for model: {config.model}')
            
        except ImportError as e:
            logger.error(f'Failed to import required packages: {e}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'Error initializing Azure AI Inference client: {e}', exc_info=True)
            raise
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, 
                     history: Optional[List[Dict[str, Any]]] = None,
                     tools: Optional[List[Tool]] = None,
                     tool_results: Optional[List[Dict[str, Any]]] = None) -> ModelResponse:
        """
        Generate a response using the Azure AI Inference model
        
        Args:
            prompt: User prompt to send to the model
            system_message: Optional system message for context
            history: Optional conversation history
            tools: Optional list of Tool objects to use
            tool_results: Optional list of tool execution results
            
        Returns:
            ModelResponse containing either text content or tool call requests
        """
        try:            
            from azure.ai.inference.models import (
                AssistantMessage, SystemMessage, UserMessage, 
                ToolMessage, ChatCompletionsToolCall
            )
            from azure.core.exceptions import HttpResponseError
            
            # Format messages
            messages = []
            if system_message:
                messages.append(SystemMessage(system_message))
            
            # Add history if provided
            if history:
                for msg in history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    tool_calls = msg.get('tool_calls')
                    # Map roles to Azure AI Inference format
                    if role == 'system':
                        continue  # System messages are handled separately
                    elif role == 'assistant':
                        if tool_calls:
                            tool_calls = [ChatCompletionsToolCall(tc) if isinstance(tc, dict) else tc for tc in tool_calls]
                        messages.append(AssistantMessage(content=content, tool_calls=tool_calls))
                    elif role == 'tool':
                        messages.append(ToolMessage(content, tool_call_id=msg.get('tool_call_id', '')))
                    else:
                        messages.append(UserMessage(content))
            
            # Insert tool results if provided
            if tool_results:
                for result in tool_results:
                    messages.append(ToolMessage(
                        content=str(result.get('result', '')),
                        tool_call_id=result.get('tool_call_id')
                    ))
            else:
                # Add current prompt
                messages.append(UserMessage(prompt))
            
            # Prepare parameters based on configuration
            params = {
                'temperature': self.config.parameters.get('temperature', 1),
                'max_tokens': self.config.parameters.get('max_tokens', 500),
                'top_p': self.config.parameters.get('top_p', 1),
            }
            
            # Include other parameters from config
            for key, value in self.config.parameters.items():
                if key not in params:
                    params[key] = value
            
            # Add tools if provided
            if tools:
                try:
                    from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition
                    
                    # Azure AI Inference API uses a special format
                    formatted_tools = get_provider_format(tools, 'azure_openai')  # Uses same format as OpenAI
                    
                    # Convert to Azure SDK format
                    azure_tools = []
                    for tool in formatted_tools:
                        if tool['type'] == 'function':
                            function_def = tool['function']
                            azure_tools.append(ChatCompletionsToolDefinition(
                                function=FunctionDefinition(
                                    name=function_def['name'],
                                    description=function_def['description'],
                                    parameters=function_def['parameters']
                                )
                            ))
                    
                    if azure_tools:
                        params['tools'] = azure_tools
                        # params['tool_choice'] = ChatCompletionsNamedToolChoice(
                        #     mapping={"type": "function", "function": {"name": "rag_tool"}}
                        # )
                except Exception as e:
                    logger.warning(f'Error formatting tools for Azure AI Inference: {e}')
            
            # Get response using the deployment name if specified, otherwise use model
            model_name = self.config.deployment_name or self.config.model
            
            response = self._client.complete(
                model=model_name,
                messages=messages,
                **params
            )            

            # update history
            if not history:
                history = [
                    { 'role': 'system', 'content': system_message }
                ]
            last_msg = messages[-1]
            if isinstance(last_msg, ToolMessage):
                history.append({ 'role': 'tool', 'content': last_msg.content, 'tool_call_id': last_msg.tool_call_id })
            else:
                history.append({ 'role': 'user', 'content': last_msg.content })
            
            # Convert response to standardized format
            assistant_msg = response.choices[0].message
            content = assistant_msg.content
            tool_calls = []
            
            # Check for tool calls in the message
            if assistant_msg.tool_calls:
                for tool_call in assistant_msg.tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, AttributeError):
                        arguments = {}
                    
                    tool_calls.append(ToolCall(
                        tool_name=tool_call.function.name,
                        arguments=arguments,
                        tool_call_id=tool_call.id
                    ))

            # append to history
            history.append({ 'role': 'assistant', 'content': content, 'tool_calls': assistant_msg.tool_calls })
            
            return ModelResponse(
                content=content,
                history=history,
                tool_calls=tool_calls,
                raw_response=response
            )
        
        except HttpResponseError as http_err:
            logger.error(f'Http error generating text with Azure AI Inference model: {http_err.message}', exc_info=True)
            return ModelResponse(content=f'HTTP error generating response: {str(http_err)}')
            
        except Exception as e:
            logger.error(f'Error generating text with Azure AI Inference model: {e}', exc_info=True)
            return ModelResponse(content=f'Error generating response: {str(e)}')
    
    def get_client(self) -> Any:
        """Get the underlying client"""
        return self._client


class ModelProviderFactory:
    """Factory for creating model providers"""
    
    @staticmethod
    def create_provider(config: Union[HuggingFaceModelConfig, AzureOpenAIModelConfig, AnthropicModelConfig, 
                               GitHubOpenAIModelConfig, AzureAIInferenceModelConfig]) -> ModelProvider:
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
        elif config.provider == ModelProviderType.GITHUB_OPENAI:
            return GitHubOpenAIModelProvider(config)
        elif config.provider == ModelProviderType.AZURE_AI_INFERENCE:
            return AzureAIInferenceModelProvider(config)
        else:
            raise ValueError(f"Unsupported model provider: {config.provider}")
