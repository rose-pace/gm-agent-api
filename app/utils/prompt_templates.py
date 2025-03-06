import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import jinja2

class PromptTemplate(BaseModel):
    """
    A class for loading and rendering Jinja2 templates for LLM prompts.
    """
    name: str
    template: str
    template_path: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def render(self, **kwargs: Any) -> str:
        """
        Render the template with the given variables.
        
        Args:
            **kwargs: Variables to use in the template
            
        Returns:
            The rendered template as a string
        """
        template = jinja2.Template(self.template)
        return template.render(**kwargs)


class PromptLibrary:
    """
    A library of prompt templates for various tasks.
    """
    def __init__(self, template_dir: str = None):
        """
        Initialize the prompt library.
        
        Args:
            template_dir: Directory containing template files (optional)
        """
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_dir = template_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'templates'
        )
        
        # Create template directory if it doesn't exist
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
    
    def add_template(self, name: str, template: str, description: str = None) -> PromptTemplate:
        """
        Add a new template to the library.
        
        Args:
            name: Name of the template
            template: The template string
            description: Optional description of the template
            
        Returns:
            The created PromptTemplate
        """
        prompt_template = PromptTemplate(
            name=name,
            template=template,
            description=description
        )
        self.templates[name] = prompt_template
        return prompt_template
    
    def load_template_from_file(self, name: str, filename: str) -> PromptTemplate:
        """
        Load a template from a file and add it to the library.
        
        Args:
            name: Name to give the template
            filename: Filename of the template (without directory)
            
        Returns:
            The loaded PromptTemplate
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
        """
        template_path = os.path.join(self.template_dir, filename)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Template file not found: {template_path}')
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        prompt_template = PromptTemplate(
            name=name,
            template=template_content,
            template_path=template_path
        )
        self.templates[name] = prompt_template
        return prompt_template
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.
        
        Args:
            name: The name of the template
            
        Returns:
            The PromptTemplate if found, None otherwise
        """
        return self.templates.get(name)
    
    def render_template(self, name: str, **kwargs: Any) -> str:
        """
        Render a template by name with the given variables.
        
        Args:
            name: Name of the template to render
            **kwargs: Variables to use in the template
            
        Returns:
            The rendered template as a string
            
        Raises:
            KeyError: If the template name doesn't exist
        """
        if name not in self.templates:
            raise KeyError(f'Template not found: {name}')
        
        return self.templates[name].render(**kwargs)
    
    def load_all_templates(self) -> None:
        """
        Load all template files from the template directory.
        
        Templates should have .jinja2 or .j2 extensions.
        """
        for filename in os.listdir(self.template_dir):
            if filename.endswith(('.jinja2', '.j2')):
                name = os.path.splitext(filename)[0]
                self.load_template_from_file(name, filename)


# Initialize a global prompt library instance
prompt_library = PromptLibrary()

def render_prompt(template_name: str, **kwargs: Any) -> str:
    """
    Utility function to render a prompt by template name.
    
    Args:
        template_name: Name of the template to render
        **kwargs: Variables to use in the template
        
    Returns:
        The rendered template as a string
    """
    return prompt_library.render_template(template_name, **kwargs)

def load_prompt_templates() -> None:
    """
    Load all available prompt templates.
    """
    prompt_library.load_all_templates()
