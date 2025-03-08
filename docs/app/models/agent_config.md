# agent_config

## Module Documentation

::: app.models.agent_config
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\models\agent_config.py`

## Class Diagram

```mermaid
classDiagram
    class WorkflowType
    WorkflowType : +RAG
    WorkflowType : +CHAIN
    WorkflowType : +ROUTING
    WorkflowType : +EVALUATOR
    WorkflowType : +GRAPH
    WorkflowType : +HYBRID
    class ActivationConfig
    ActivationConfig : +model_config
    class ToolConfig
    ToolConfig : +model_config
    class WorkflowStepConfig
    WorkflowStepConfig : +model_config
    class WorkflowConfig
    WorkflowConfig : +model_config
    class AgentConfig
    AgentConfig : +get_default_workflow()
    AgentConfig : +get_workflow_by_name()
    AgentConfig : +model_config
```
