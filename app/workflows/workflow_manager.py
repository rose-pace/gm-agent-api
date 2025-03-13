"""
Workflow Manager for orchestrating agent workflows based on configuration.
"""
from typing import Dict, Any, Optional, List, Type
import os
import yaml
import json
import logging
from pathlib import Path

from app.models.agent_config import AgentConfig, WorkflowConfig, WorkflowType
from app.models.configuration import ModelConfig
from app.llm.model_provider import ModelProviderFactory
from app.workflows.base_workflow import BaseWorkflow, WorkflowResult
from app.workflows.rag_workflow import RAGWorkflow
from app.workflows.graph_workflow import GraphWorkflow
from app.workflows.hybrid_workflow import HybridWorkflow

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Manager for loading, configuring, and executing agent workflows.
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 config: Optional[AgentConfig] = None,
                 tools: Optional[Dict[str, Any]] = None,
                 components: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow manager with either a config path or config object
        
        Args:
            config_path: Path to the configuration file (YAML or JSON)
            config: Directly provided AgentConfig object
            tools: Dictionary of tool instances to use
            components: Dictionary of component instances to use
        """
        self.config = None
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.tools = tools or {}
        self.components = components or {}
        self._workflow_classes: Dict[WorkflowType, Type[BaseWorkflow]] = {
            WorkflowType.RAG: RAGWorkflow,
            # WorkflowType.GRAPH: GraphWorkflow,
            WorkflowType.HYBRID: HybridWorkflow,
        }
        
        # Load configuration
        if config:
            self.config = config
        elif config_path:
            self._load_config(config_path)
        else:
            raise ValueError("Either config_path or config must be provided")
        
        # Initialize workflows
        self._initialize_workflows()
    
    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from file
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            ValueError: If the file format is not supported or file doesn't exist
        """
        path = Path(config_path)
        if not path.exists():
            raise ValueError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() == '.json':
                    config_data = json.load(f)
                elif path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported configuration format: {path.suffix}")
            
            self.config = AgentConfig.model_validate(config_data)
            logger.info(f"Loaded agent configuration: {self.config.name}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise ValueError(f"Failed to load configuration: {str(e)}")
    
    def _initialize_workflows(self) -> None:
        """
        Initialize workflow instances based on configuration
        """
        if not self.config:
            logger.error("Cannot initialize workflows: no configuration loaded")
            return
        
        for workflow_config in self.config.workflows:
            try:
                # Get the model configuration for this workflow
                if workflow_config.model:
                    configuration = self.config.configuration.get_model_by_name(workflow_config.model)
                    if not configuration:
                        logger.warning(f"Model {workflow_config.model} not found, using default")
                        configuration = self.config.configuration.get_default_model()
                else:
                    configuration = self.config.configuration.get_default_model()
                
                # Create the model provider
                model_provider = ModelProviderFactory.create_provider(configuration)
                
                # Get workflow class based on type
                workflow_class = self._workflow_classes.get(workflow_config.type)
                if not workflow_class:
                    logger.warning(f"Workflow type {workflow_config.type} not supported")
                    continue
                
                # Prepare workflow tools
                workflow_tools = {}
                for tool_config in workflow_config.tools:
                    if tool_config.name in self.tools:
                        workflow_tools[tool_config.name] = self.tools[tool_config.name]
                    else:
                        logger.warning(f"Tool {tool_config.name} not available")
                
                # Prepare workflow components
                workflow_components = {}
                for component_name in workflow_config.components:
                    if component_name in self.components:
                        workflow_components[component_name] = self.components[component_name]
                    else:
                        logger.warning(f"Component {component_name} not available")
                
                # Initialize the workflow
                workflow = workflow_class(
                    name=workflow_config.name,
                    model_provider=model_provider,
                    tools=workflow_tools,
                    components=workflow_components
                )
                
                # Register the workflow
                self.workflows[workflow_config.name] = workflow
                logger.info(f"Initialized workflow: {workflow_config.name} ({workflow_config.type})")
                
            except Exception as e:
                logger.error(f"Error initializing workflow {workflow_config.name}: {e}", exc_info=True)
    
    async def select_workflow(self, query: str, context: Optional[Dict[str, Any]] = None) -> BaseWorkflow:
        """
        Select the appropriate workflow based on the query
        
        Args:
            query: User query text
            context: Optional context information
            
        Returns:
            The selected workflow
            
        Raises:
            ValueError: If no workflow is available
        """
        if not self.workflows:
            raise ValueError("No workflows available")
        
        # Get the workflows sorted by priority (highest first)
        sorted_workflows = sorted(
            self.config.workflows,
            key=lambda w: w.activation.priority,
            reverse=True
        )
        
        # Check for keyword matches
        query_lower = query.lower()
        for workflow_config in sorted_workflows:
            for keyword in workflow_config.activation.keywords:
                if keyword.lower() in query_lower:
                    workflow = self.workflows.get(workflow_config.name)
                    if workflow:
                        logger.info(f"Selected workflow '{workflow_config.name}' based on keyword match: {keyword}")
                        return workflow
        
        # If no keyword match, use default workflow
        default_config = self.config.get_default_workflow()
        if default_config and default_config.name in self.workflows:
            logger.info(f"Using default workflow: {default_config.name}")
            return self.workflows[default_config.name]
        
        # If no default is set, use the first available workflow
        logger.warning("No default workflow set, using first available")
        return next(iter(self.workflows.values()))
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Process a query using the appropriate workflow
        
        Args:
            query: User query text
            context: Optional context information
            
        Returns:
            Workflow execution result
        """
        try:
            # Select the appropriate workflow
            workflow = await self.select_workflow(query, context)
            
            # Execute the workflow
            logger.info(f"Executing workflow: {workflow.name}")
            result = await workflow.execute(query, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return WorkflowResult(
                answer=f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                confidence=0.0
            )
    
    def register_workflow_class(self, workflow_type: WorkflowType, workflow_class: Type[BaseWorkflow]) -> None:
        """
        Register a custom workflow class
        
        Args:
            workflow_type: The workflow type enumeration value
            workflow_class: The workflow class to register
        """
        self._workflow_classes[workflow_type] = workflow_class
        logger.info(f"Registered custom workflow class for type: {workflow_type}")
    
    def register_tool(self, name: str, tool_instance: Any) -> None:
        """
        Register a tool instance
        
        Args:
            name: Name of the tool
            tool_instance: The tool instance
        """
        self.tools[name] = tool_instance
        logger.info(f"Registered tool: {name}")
    
    def register_component(self, name: str, component_instance: Any) -> None:
        """
        Register a component instance
        
        Args:
            name: Name of the component
            component_instance: The component instance
        """
        self.components[name] = component_instance
        logger.info(f"Registered component: {name}")
