# processor_config

## Module Documentation

::: app.models.processor_config
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\models\processor_config.py`

## Class Diagram

```mermaid
classDiagram
    class ChunkingStrategy
    ChunkingStrategy : +FIXED
    ChunkingStrategy : +MARKDOWN
    ChunkingStrategy : +YAML
    ChunkingStrategy : +SLIDING
    class VectorProcessorConfig
    VectorProcessorConfig : +model_config
    class EntityExtractionPattern
    EntityExtractionPattern : +model_config
    class RelationshipExtractionPattern
    RelationshipExtractionPattern : +model_config
    class GraphProcessorConfig
    GraphProcessorConfig : +model_config
    class ProcessorRegistry
    ProcessorRegistry : +Config()
    ProcessorRegistry : +model_config
```
