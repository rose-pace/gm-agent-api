import os
import json
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Check if environment is running it github codespaces
if 'CODESPACES' in os.environ:
    # If so, update the version of sqlite
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Import our agent and tool modules
from app.agents.gm_assistant import GMAssistantAgent
from app.tools.rag_tool import RAGTool
from app.db import VectorStore
from app.models import Query, Response, Document, GraphEdge, GraphNode
from app.utils.prompt_generator import initialize_prompts
from app.db.graph_store import GraphStore
from app.tools.graph_query_tool import GraphQueryTool

load_dotenv()

# Global variables for our agents and tools
gm_agent = None
rag_tool = None
vector_store = None
graph_store = None
graph_tool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager to handle the startup and shutdown of the app
    """  
    global gm_agent, rag_tool, vector_store, graph_store, graph_tool
    
    # Initialize prompt templates
    initialize_prompts()
    
    # Initialize vector store
    vector_store = VectorStore(
        collection_name='campaign_notes',
        persist_directory='./data/vector_db'
    )
    
    # Initialize graph store
    graph_store = GraphStore(file_path='./data/graph_store.json')
    
    # Initialize tools
    rag_tool = RAGTool(vector_store=vector_store)
    graph_tool = GraphQueryTool(graph_store=graph_store)
    
    # Initialize GM assistant agent with tools
    gm_agent = GMAssistantAgent(tools=[rag_tool, graph_tool])

    yield
    
    # Save graph data on shutdown
    if graph_store:
        graph_store.save_to_file('./data/graph_store.json')

# Create FastAPI app
app = FastAPI(
    title='Game Master Assistant API',
    description='An API for an agentic AI that assists game masters with their campaigns',
    version='0.1.0',
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Adjust in production
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/')
async def root():
    return {'message': 'Welcome to the Game Master Assistant API'}

@app.post('/ask', response_model=Response)
async def ask_question(query: Query) -> Response:
    """
    Ask the GM assistant a question about the campaign or setting
    """
    if not gm_agent:
        raise HTTPException(status_code=503, detail='Agent not initialized')
    
    try:
        response = await gm_agent.process_query(query.text, query.context)
        return JSONResponse(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error processing query: {str(e)}')

@app.post('/upload')
async def upload_document(document: Document):
    """
    Upload a document to the campaign notes database
    """
    if not vector_store:
        raise HTTPException(status_code=503, detail='Vector store not initialized')
    
    try:
        vector_store.add_documents([document])
        return {'status': 'success', 'message': 'Document added to the knowledge base'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding document: {str(e)}')

@app.post('/graph/add_entity')
async def add_entity(node: GraphNode):
    """
    Add an entity to the graph store
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail='Graph store not initialized')
    
    try:
        node_id = graph_store.add_node(node)
        return {'status': 'success', 'id': node_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding entity: {str(e)}')

@app.post('/graph/add_relationship')
async def add_relationship(edge: GraphEdge):
    """
    Add a relationship between entities to the graph store
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail='Graph store not initialized')
    
    try:
        edge_id = graph_store.add_edge(edge)
        return {'status': 'success', 'id': edge_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding relationship: {str(e)}')

@app.get('/graph/get_entity/{identifier}')
async def get_entity(identifier: str):
    """
    Get an entity by ID or name
    """
    if not graph_tool:
        raise HTTPException(status_code=503, detail='Graph tool not initialized')
    
    try:
        entity = await graph_tool.get_entity(identifier)
        if entity:
            return entity
        raise HTTPException(status_code=404, detail=f'Entity not found: {identifier}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting entity: {str(e)}')

@app.get('/graph/get_related/{identifier}')
async def get_related(identifier: str, relation_type: Optional[str] = None):
    """
    Get entities related to the specified entity
    """
    if not graph_tool:
        raise HTTPException(status_code=503, detail='Graph tool not initialized')
    
    try:
        related = await graph_tool.get_related_entities(identifier, relation_type)
        return related
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting related entities: {str(e)}')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
