# document_processor

## Module Documentation

::: app.db.document_processor
    options:
        show_source: true
        heading_level: 3
        members_order: source

## Source File

`app\db\document_processor.py`

## Class Diagram

```mermaid
classDiagram
    class DocumentProcessor
    DocumentProcessor : +extract_yaml_blocks()
    DocumentProcessor : +process_document()
    DocumentProcessor : +chunk_document()
    DocumentProcessor : +fixed_size_chunking()
    DocumentProcessor : +yaml_structure_chunking()
    DocumentProcessor : +markdown_chunking()
    DocumentProcessor : +sliding_window_chunking()
    DocumentProcessor : +add_chunks_to_db()
```
