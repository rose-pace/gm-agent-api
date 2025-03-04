# Game Master Assistant API

An agentic AI system designed to assist Game Masters (GMs) with their tabletop roleplaying campaigns by providing intelligent responses based on campaign notes and world-building documents.

## Overview

This API powers an AI assistant specifically tailored for Game Masters running tabletop RPG sessions. The system uses Retrieval-Augmented Generation (RAG) to provide contextually relevant information from your campaign documents, helping GMs maintain consistency and recall important details during gameplay.

## Features

- **Document Storage**: Upload and store campaign notes, world-building documents, and session recaps
- **Intelligent Retrieval**: Query the system using natural language to find relevant information
- **Context-Aware Responses**: The assistant considers provided context to deliver more accurate responses
- **Vector-Based Search**: Utilizes semantic search to find information even when exact terms don't match

## Technical Architecture

The Game Master Assistant API is built on:
- **FastAPI**: High-performance web framework
- **ChromaDB**: Vector database for semantic document storage
- **Pydantic**: Data validation and settings management
- **Agentic AI**: Custom agent framework for intelligent response generation

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gm-agent-api.git
   cd gm-agent-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Project

Start the API server:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

### Importing Documents

To import your campaign documents into the system:

1. Place your markdown (.md) and YAML (.yaml) files in the `documents` directory at the root of the project.

2. Run the import script:

   ```bash
   python import_documents.py
   ```

   This will process all documents and add them to the vector store, overwriting any existing documents.

3. To append new documents without removing existing ones:

   ```bash
   python import_documents.py -a
   ```

The import script automatically processes files using appropriate chunking strategies based on file type (markdown or YAML).

## API Endpoints

### `GET /`
Returns a welcome message to confirm the API is running.

### `POST /ask`
Ask the GM assistant a question about the campaign or setting.

**Request Body:**
```json
{
  "text": "What is the name of the tavern in Northaven?",
  "context": {
    "campaign": "Shadows of Eldoria",
    "current_location": "Northaven"
  }
}
```

**Response:**
```json
{
  "answer": "The tavern in Northaven is called 'The Rusty Flagon'. It's run by a dwarf named Durgan Stonebrew who is known for his special honey mead.",
  "sources": [
    {
      "title": "Northaven Town Guide",
      "content_snippet": "...features the popular tavern 'The Rusty Flagon' run by Durgan Stonebrew...",
      "relevance": 0.92
    }
  ],
  "confidence": 0.89
}
```

### `POST /upload`
Upload a document to the campaign notes database.

**Request Body:**
```json
{
  "content": "Northaven is a small fishing town on the eastern coast. The town features the popular tavern 'The Rusty Flagon' run by Durgan Stonebrew, a dwarf known for his honey mead recipe.",
  "metadata": {
    "title": "Northaven Town Guide",
    "type": "location_description",
    "author": "GM",
    "date_created": "2023-06-15"
  },
  "id": "LOC-CIT-NORTHAVEN-0023"
}
```

## Example Usage

### Uploading Campaign Notes

```python
import requests

api_url = "http://localhost:8000/upload"
document = {
    "content": "The ancient ruins of Kalindor contain a hidden chamber beneath the main altar. The chamber can only be accessed by placing the four elemental gems in the correct order: fire, water, earth, air.",
    "metadata": {
        "title": "Kalindor Ruins Secret",
        "type": "location_secret",
        "importance": "high",
        "campaign": "Shadows of Eldoria"
    },
    "id": "LOC-SEC-KALINDOR_RUINS-3009"
}

response = requests.post(api_url, json=document)
print(response.json())
```

### Querying the Assistant

```python
import requests

api_url = "http://localhost:8000/ask"
query = {
    "text": "How do I access the hidden chamber in the Kalindor ruins?",
    "context": {
        "player_knowledge": "The party has found three of the four elemental gems",
        "campaign": "Shadows of Eldoria"
    }
}

response = requests.post(api_url, json=query)
print(response.json())
```

## License

[MIT License](LICENSE)
