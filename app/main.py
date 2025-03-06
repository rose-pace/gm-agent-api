from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import our agent and tool modules
from app.agents.gm_assistant import GMAssistantAgent
from app.tools.rag_tools import RAGTool
from app.db import VectorStore
from app.models import Query, Response, Document
from app.utils.prompt_generator import initialize_prompts

load_dotenv()

# Global variables for our agents and tools
gm_agent = None
rag_tool = None
vector_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager to handle the startup and shutdown of the app
    """  
    global gm_agent, rag_tool, vector_store
    
    # Initialize prompt templates
    initialize_prompts()
    
    # Initialize vector store
    vector_store = VectorStore(
        collection_name='campaign_notes',
        persist_directory='./data/vector_db'
    )
    
    # Initialize RAG tool
    rag_tool = RAGTool(vector_store=vector_store)
    
    # Initialize GM assistant agent with tools
    gm_agent = GMAssistantAgent(tools=[rag_tool])

    yield

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
async def ask_question(query: Query):
    """
    Ask the GM assistant a question about the campaign or setting
    """
    if not gm_agent:
        raise HTTPException(status_code=503, detail='Agent not initialized')
    
    try:
        response = await gm_agent.process_query(query.text, query.context)
        return response
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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
