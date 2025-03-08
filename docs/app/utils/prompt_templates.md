# prompt_templates

## Module Documentation

::: app.utils.prompt_templates
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\utils\prompt_templates.py`

## Class Diagram

```mermaid
classDiagram
    class PromptTemplate
    PromptTemplate : +Config()
    PromptTemplate : +render()
    PromptTemplate : +model_config
    class PromptLibrary
    PromptLibrary : +add_template()
    PromptLibrary : +load_template_from_file()
    PromptLibrary : +get_template()
    PromptLibrary : +render_template()
    PromptLibrary : +load_all_templates()
```
