# configuration

## Module Documentation

::: app.models.configuration
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\models\configuration.py`

## Class Diagram

```mermaid
classDiagram
    class ModelProviderType
    ModelProviderType : +HUGGINGFACE
    ModelProviderType : +AZURE_OPENAI
    ModelProviderType : +ANTHROPIC
    class BaseModelConfig
    BaseModelConfig : +model_config
    class HuggingFaceModelConfig
    HuggingFaceModelConfig : +validate_parameters
    HuggingFaceModelConfig : +model_config
    class AzureOpenAIModelConfig
    AzureOpenAIModelConfig : +validate_parameters
    AzureOpenAIModelConfig : +model_config
    class AnthropicModelConfig
    AnthropicModelConfig : +validate_parameters
    AnthropicModelConfig : +model_config
    class ModelConfig
    ModelConfig : +get_model_by_name()
    ModelConfig : +model_config
    BaseModelConfig <|-- HuggingFaceModelConfig
    BaseModelConfig <|-- AzureOpenAIModelConfig
    BaseModelConfig <|-- AnthropicModelConfig
```
