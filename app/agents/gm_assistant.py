from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import yaml
import logging
from pathlib import Path

from app.utils.prompt_generator import generate_agent_instruction, AgentInstructionParams, Tool
from app.workflows.workflow_manager import WorkflowManager
from app.tools.rag_tools import RAGTool
from app.tools.graph_query_tool import GraphQueryTool
from app.tools.graph_query_handler import GraphQueryHandler
from app.models.agent_config import AgentConfig

# Configure logging
logger = logging.getLogger(__name__)

class GMAssistantAgent:
    """
    Game Master Assistant Agent that helps with campaign and setting questions
    using a configurable workflow system.
    """
    
    def __init__(self, tools=None, components=None, game_system=None, campaign_setting=None, 
                 config_path: Optional[str] = None):
        """
        Initialize the GM Assistant Agent with the given tools
        
        Args:
            tools: List of tools the agent can use
            components: Dictionary of components the agent can use
            game_system: Optional game system to specialize in
            campaign_setting: Optional campaign setting
            config_path: Path to agent configuration file
        """
        self.game_system = game_system
        self.campaign_setting = campaign_setting
        
        # Initialize tool and component registries
        self.tools_registry = {}
        self.components_registry = {}
        
        # Register provided tools
        if tools:
            for tool in tools:
                tool_name = getattr(tool, 'name', tool.__class__.__name__).lower()
                self.tools_registry[tool_name] = tool
                
                # If this is a graph tool, also create a graph handler
                if isinstance(tool, GraphQueryTool) and 'graph_query_handler' not in self.components_registry:
                    handler = GraphQueryHandler(graph_tool=tool)
                    self.components_registry['graph_query_handler'] = handler
        
        # Register provided components
        if components:
            for name, component in components.items():
                self.components_registry[name] = component
        
        # Default config path if none provided
        if not config_path:
            config_path = os.environ.get('AGENT_CONFIG_PATH', './configs/agent_config.yaml')
        
        # Create or load workflow manager
        self.workflow_manager = self._initialize_workflow_manager(config_path)
        
        # Generate the system prompt for the agent
        tool_models = []
        for name, tool in self.tools_registry.items():
            tool_desc = getattr(tool, 'description', 'No description available')
            tool_models.append(Tool(name=name, description=tool_desc))
        
        self.system_prompt = generate_agent_instruction(
            AgentInstructionParams(
                game_system=self.game_system,
                campaign_setting=self.campaign_setting,
                tools=tool_models
            )
        )
    
    def _initialize_workflow_manager(self, config_path: str) -> WorkflowManager:
        """
        Initialize the workflow manager with configuration
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Initialized workflow manager
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        # Check if config exists
        path = Path(config_path)
        
        if not path.exists():
            # Raise exception if config doesn't exist
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        try:
            # Create workflow manager with existing tools and components
            workflow_manager = WorkflowManager(
                config_path=config_path,
                tools=self.tools_registry,
                components=self.components_registry
            )
            return workflow_manager
            
        except Exception as e:
            logger.error(f"Error initializing workflow manager: {e}", exc_info=True)
            raise
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query from the user and return a response
        
        Args:
            query: The text query from the user
            context: Optional contextual information
            
        Returns:
            A dictionary with the answer, sources, and optionally confidence score
        """
        try:
            # Process the query using the workflow manager
            result = await self.workflow_manager.process_query(query, context)
            
            # Format the response
            response = {
                'answer': result.answer,
                'sources': result.sources,
                'confidence': result.confidence,
                'metadata': result.metadata
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'answer': f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'metadata': {'error': str(e)}
            }
