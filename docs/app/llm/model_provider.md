# model_provider

## Module Documentation

::: app.llm.model_provider
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\llm\model_provider.py`

## Class Diagram

```mermaid
classDiagram
    class ModelProvider
    ModelProvider : +generate()
    ModelProvider : +get_client()
    class HuggingFaceModelProvider
    HuggingFaceModelProvider : +generate()
    HuggingFaceModelProvider : +get_client()
    class AzureOpenAIModelProvider
    AzureOpenAIModelProvider : +generate()
    AzureOpenAIModelProvider : +get_client()
    class AnthropicModelProvider
    AnthropicModelProvider : +generate()
    AnthropicModelProvider : +get_client()
    class ModelProviderFactory
    ModelProviderFactory : +create_provider()
    ModelProvider <|-- HuggingFaceModelProvider
    ModelProvider <|-- AzureOpenAIModelProvider
    ModelProvider <|-- AnthropicModelProvider
```
