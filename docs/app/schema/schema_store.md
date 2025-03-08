# schema_store

## Module Documentation

::: app.schema.schema_store
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\schema\schema_store.py`

## Class Diagram

```mermaid
classDiagram
    class SchemaEnforcedGraphStore
    SchemaEnforcedGraphStore : +add_entity()
    SchemaEnforcedGraphStore : +add_relationship()
    SchemaEnforcedGraphStore : +get_node()
    SchemaEnforcedGraphStore : +get_edge()
    SchemaEnforcedGraphStore : +get_nodes_by_type()
    SchemaEnforcedGraphStore : +get_node_by_name()
    SchemaEnforcedGraphStore : +get_related_nodes()
    SchemaEnforcedGraphStore : +find_path()
    SchemaEnforcedGraphStore : +find_nodes_by_property()
    SchemaEnforcedGraphStore : +save_to_file()
    SchemaEnforcedGraphStore : +load_from_file()
    SchemaEnforcedGraphStore : +clear()
    SchemaEnforcedGraphStore : +delete_node()
    SchemaEnforcedGraphStore : +delete_edge()
```
