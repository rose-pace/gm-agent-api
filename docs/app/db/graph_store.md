# graph_store

## Module Documentation

::: app.db.graph_store
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\db\graph_store.py`

## Class Diagram

```mermaid
classDiagram
    class GraphStore
    GraphStore : +add_node()
    GraphStore : +add_edge()
    GraphStore : +get_node()
    GraphStore : +get_edge()
    GraphStore : +get_nodes_by_type()
    GraphStore : +get_node_by_name()
    GraphStore : +get_related_nodes()
    GraphStore : +find_path()
    GraphStore : +find_nodes_by_property()
    GraphStore : +save_to_file()
    GraphStore : +load_from_file()
    GraphStore : +clear()
    GraphStore : +delete_node()
    GraphStore : +delete_edge()
```
