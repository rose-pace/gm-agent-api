# prompt_utils

## Module Documentation

::: app.utils.prompt_utils
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\utils\prompt_utils.py`

## Class Diagram

```mermaid
classDiagram
    class ChromaFilter
    ChromaFilter : +field()
    ChromaFilter : +equals()
    ChromaFilter : +not_equals()
    ChromaFilter : +in_list()
    ChromaFilter : +not_in_list()
    ChromaFilter : +greater_than()
    ChromaFilter : +greater_than_equals()
    ChromaFilter : +less_than()
    ChromaFilter : +less_than_equals()
    ChromaFilter : +contains()
    ChromaFilter : +and_group()
    ChromaFilter : +or_group()
    ChromaFilter : +generate()
```
