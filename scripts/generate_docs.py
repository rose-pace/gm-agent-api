"""
Documentation Generation Script (v2)

This script generates comprehensive documentation for Python projects using mkdocstrings.
It creates a mirrored directory structure with markdown files and mermaid diagrams.

Requirements:
    - mkdocstrings: For generating API documentation
    - mkdocs: For building the documentation site
        Additional plugins:
        - mkdocs-material: For a nice material theme
        - pymdown-extensions: For additional markdown extensions
    - click: For command-line interface
    - colorama: For colored terminal output
    - pydantic: For model validation

Usage:
    python generate_docs_v2.py --start-path ./app --output-dir ./docs
"""

import os
import sys
import logging
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import click
from colorama import Fore, init

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('doc_generator')

#################################################
# File Discovery Module
#################################################

def find_python_files(start_path: str) -> List[Path]:
    """
    Find all Python files in the given directory and subdirectories.
    
    Args:
        start_path: Path to start searching from
    
    Returns:
        List of Path objects to Python files
    """
    start_path = Path(start_path)
    
    if start_path.is_file():
        if start_path.suffix == '.py':
            return [start_path]
        else:
            logger.warning(f'{start_path} is not a Python file')
            return []
    
    python_files = []
    
    for path in start_path.rglob('*.py'):
        # Skip __pycache__, venv, and other common directories to ignore
        if any(part.startswith(('__pycache__', 'venv', '.venv', 'env', '.env', '.git')) 
               for part in path.parts):
            continue
        python_files.append(path)
    
    return python_files


def build_module_tree(files: List[Path], project_root: str) -> Dict[str, Any]:
    """
    Organize Python files into a module tree structure.
    
    Args:
        files: List of Python file paths
        project_root: Root directory of the project
        
    Returns:
        Dictionary representing the module tree structure
    """
    project_root_path = Path(project_root)
    tree = {}
    
    for file_path in files:
        try:
            # Get the relative path from project root
            rel_path = file_path.relative_to(project_root_path)
            
            # Convert file path to module path (e.g., app/models/user.py -> app.models.user)
            module_parts = list(rel_path.with_suffix('').parts)
            
            # Skip files starting with underscore as they're typically not public API
            if module_parts[-1].startswith('_') and module_parts[-1] != '__init__':
                continue
                
            # Navigate the tree and create branches as needed
            current = tree
            for i, part in enumerate(module_parts):
                # For the last part (file name)
                if i == len(module_parts) - 1:
                    # For __init__.py, add module info at the current level
                    if part == '__init__':
                        current['__file__'] = str(file_path)
                        current['__module__'] = '.'.join(module_parts[:-1])
                    else:
                        # Regular module file
                        if part not in current:
                            current[part] = {
                                '__file__': str(file_path),
                                '__module__': '.'.join(module_parts)
                            }
                else:
                    # For intermediate directories
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        except (ValueError, Exception) as e:
            logger.warning(f'Error processing file {file_path}: {str(e)}')
    
    return tree

#################################################
# Documentation Generation Module
#################################################

def create_output_structure(module_tree: Dict[str, Any], output_dir: str) -> Dict[str, Tuple[Path, str]]:
    """
    Create the output directory structure mapping but don't write files yet.
    
    Args:
        module_tree: Dictionary representing the module structure
        output_dir: Base output directory
        
    Returns:
        Dictionary mapping module paths to tuples of (output_file_path, source_file_path)
    """
    output_dir_path = Path(output_dir)
    output_mapping = {}
    
    def process_tree(tree: Dict[str, Any], current_path: Path, module_prefix: str = ''):
        """Process the module tree recursively to create the directory structure mapping."""
        for key, value in sorted(tree.items()):
            # Skip metadata keys
            if key.startswith('__'):
                continue
                
            # New module path
            new_module_path = f'{module_prefix}.{key}' if module_prefix else key
            
            # If this is a leaf node (module file)
            if not value.get('__file__', '').endswith('__init__.py'):
                # Define markdown file path for this module
                md_file_path = current_path / f'{key}.md'
                
                # Store mapping from module path to output file and source file
                module_path = value.get('__module__', new_module_path)
                source_file_path = value.get('__file__', '')
                output_mapping[module_path] = (md_file_path, source_file_path)
            
            # For package directories
            else:
                # Define directory path
                new_dir = current_path / key
                
                # Create index.md mapping for the package
                index_path = new_dir / 'index.md'
                
                # Find source file for package (__init__.py)
                source_file_path = ''
                if '__file__' in value:
                    source_file_path = value['__file__']
                
                output_mapping[new_module_path] = (index_path, source_file_path)
                
                # Process children
                process_tree(value, new_dir, new_module_path)
    
    # Start processing from the root
    process_tree(module_tree, output_dir_path)
    
    return output_mapping

def generate_module_docs(module_path: str, source_file: Path) -> str:
    """
    Generate documentation for a single module using mkdocstrings.
    
    Args:
        module_path: Importable Python module path
        source_file: Path to the source file
        
    Returns:
        Generated markdown content as a string
    """
    try:
        # Extract module name for the title
        module_name = module_path.split('.')[-1]
        
        # For packages, use the full module path
        if module_path.endswith('.__init__'):
            module_name = module_path[:-9]  # Remove .__init__
        
        # Generate markdown content using mkdocstrings reference format
        content = [
            f'# {module_name}',
            '',
            '## Module Documentation',
            '',
            f'::: {module_path}',
            '    options:',
            '        show_source: true',
            '        heading_level: 3',
            '        members_order: source',
            '',
            '## Source File',
            '',
            f'`{source_file}`',
            ''
        ]
        
        return '\n'.join(content)
        
    except Exception as e:
        logger.error(f'Failed to generate documentation for {module_path}: {str(e)}', exc_info=True)
        return ''

#################################################
# Diagram Generation Module
#################################################

def generate_module_diagram(module_path: str, source_file: Path) -> str:
    """
    Generate a mermaid diagram for a module.
    
    Args:
        module_path: Importable Python module path
        source_file: Path to the source file
        
    Returns:
        Generated mermaid diagram as string
    """
    try:
        # Try to import the module to get its attributes
        spec = importlib.util.spec_from_file_location(module_path, source_file)
        if not spec or not spec.loader:
            return ''
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get all classes in the module
        classes = {name: cls for name, cls in vars(module).items() 
                  if isinstance(cls, type) and cls.__module__ == module_path}
        
        if not classes:
            return ''
        
        # Start building the mermaid class diagram
        diagram_lines = [
            '## Class Diagram',
            '',
            '```mermaid',
            'classDiagram'
        ]
        
        # Add each class
        for class_name, cls in classes.items():
            diagram_lines.append(f'    class {class_name}')
            
            # Add methods
            methods = []
            for name, member in vars(cls).items():
                if callable(member) and not name.startswith('_'):
                    methods.append(f'    {class_name} : +{name}()')
            
            # Add properties and attributes
            for name, member in vars(cls).items():
                if not callable(member) and not name.startswith('_'):
                    methods.append(f'    {class_name} : +{name}')
                    
            diagram_lines.extend(methods)
                
        # Add inheritance relationships
        for class_name, cls in classes.items():
            for base in cls.__bases__:
                if base.__module__ == module_path and base.__name__ in classes:
                    diagram_lines.append(f'    {base.__name__} <|-- {class_name}')
        
        diagram_lines.append('```')
        diagram_lines.append('')
        
        return '\n'.join(diagram_lines)
    except Exception as e:
        logger.debug(f'Error generating diagram for {module_path}: {str(e)}')
        return ''

def generate_project_diagram(app_root: str, output_dir: str) -> str:
    """
    Generate an overall project dependency diagram.
    
    Args:
        app_root: starting directory of the application
        output_dir: output directory for the diagrams
        
    Returns:
        Generated mermaid diagram as string
    """
    try:
        diagrams_dir = os.path.join(output_dir, 'diagrams')
        os.makedirs(diagrams_dir, exist_ok=True)

        # Generate MermaidJS diagram directly with pyreverse
        cmd = [
            'pyreverse',
            '-o', 'mmd',
            '-p', 'project',
            '--no-standalone',
            '--colorized',
            '-d', diagrams_dir,
            app_root
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f'pyreverse failed: {result.stderr}', exc_info=True)
            return None
        
        # Get the manually made api diagram to add to the documentation as well
        api_mermaid_file = os.path.join(diagrams_dir, 'api_diagram.mmd')
        with open(api_mermaid_file, 'r') as f:
            api_content = f.read()

        doc_ingestion_mermaid_file = os.path.join(diagrams_dir, 'doc_ingestion_diagram.mmd')
        with open(doc_ingestion_mermaid_file, 'r') as f:
            ingest_content = f.read()
        
        # Start building the mermaid diagram
        diagram = f'''
# Project Overview

## API Agent Process

```mermaid
{api_content}
```

## Document Ingestion Process
```mermaid
{ingest_content}
```
'''
        return diagram
    except Exception as e:
        logger.error(f'Error generating project diagram: {str(e)}', exc_info=True)
        return ''

#################################################
# Navigation Module
#################################################

def process_module_tree(tree: Dict[str, Any], processor_fn, path: str = '', level: int = 0) -> Any:
    """
    Process a module tree using a provided processor function.
    
    Args:
        tree: Module tree dictionary
        processor_fn: Function to process each node (signature: fn(key, value, is_package, path, level))
        path: Current path in the tree
        level: Current level in the tree
        
    Returns:
        Result from the processor function
    """
    # First gather packages and modules separately
    packages = []
    modules = []
    
    for key, value in tree.items():
        if key.startswith('__'):
            continue
            
        if not value.get('__file__', '').endswith('__init__.py'):
            modules.append((key, value))
        else:
            packages.append((key, value))
    
    # Sort each group
    packages.sort(key=lambda x: x[0])
    modules.sort(key=lambda x: x[0])
    
    # Process packages first, then modules
    results = []
    
    for key, value in packages:
        new_path = f'{path}/{key}' if path else key
        result = processor_fn(key, value, True, new_path, level)
        if result:
            results.append(result)
    
    for key, value in modules:
        new_path = f'{path}/{key}' if path else key
        result = processor_fn(key, value, False, new_path, level)
        if result:
            results.append(result)
    
    return results

def generate_table_of_contents(module_tree: Dict[str, Any]) -> str:
    """
    Generate a table of contents for the documentation.
    
    Args:
        module_tree: Dictionary representing the module structure
        
    Returns:
        Generated table of contents as string
    """
    try:
        toc_lines = [
            '# Project Documentation',
            '',
            '## Table of Contents',
            ''
        ]
        
        def toc_processor(key, value, is_package, path, level):
            indent = '    ' * level
            
            if is_package:
                toc_lines.append(f'{indent}- {key}')
                process_module_tree(value, toc_processor, path, level + 1)
            else:
                toc_lines.append(f'{indent}- [{key}]({path}.md)')
            return None
        
        process_module_tree(module_tree, toc_processor)
        # for result in results:
        #     if result:
        #         toc_lines.append(result)
        
        return '\n'.join(toc_lines)
    except Exception as e:
        logger.error(f'Error generating table of contents: {str(e)}', exc_info=True)
        return ''

#################################################
# Configuration Module
#################################################

def generate_mkdocs_config(output_dir: str, module_tree: Dict[str, Any]) -> str:
    """
    Generate MkDocs configuration file.
    
    Args:
        output_dir: Output directory
        module_tree: Dictionary representing the module structure
        
    Returns:
        Path to the generated config file
    """
    logger.info('Generating MkDocs configuration file')
    config_file = Path(output_dir) / 'mkdocs.yml'
    
    try:
        # Build navigation structure
        nav = []
        
        # Home page
        nav.append({'Home': 'index.md'})
        
        # Project diagram
        nav.append({'Project Overview': 'project_diagram.md'})
        
        # Module documentation - organized by packages
        module_nav = build_navigation_structure(module_tree)
        if module_nav:
            nav.append({'API Documentation': module_nav})
        
        # Generate YAML content
        config_content = [
            'site_name: Project Documentation',
            'site_description: Auto-generated API Documentation',
            '',
            'theme:',
            '  name: material',
            '  features:',
            '    - navigation.instant',
            '    - navigation.tracking',
            '    - navigation.expand',
            '    - navigation.indexes',
            '    - toc.integrate',
            '  palette:',
            '    - scheme: default',
            '      primary: indigo',
            '      accent: indigo',
            '      toggle:',
            '        icon: material/brightness-7',
            '        name: Switch to dark mode',
            '    - scheme: slate',
            '      primary: indigo',
            '      accent: indigo',
            '      toggle:',
            '        icon: material/brightness-4',
            '        name: Switch to light mode',
            '',
            'plugins:',
            '  - search',
            '  - mkdocstrings:',
            '      handlers:',
            '        python:',
            '          rendering:',
            '            show_source: true',
            '            heading_level: 3',
            '            members_order: source',
            '            docstring_style: google',
            '',
            'markdown_extensions:',
            '  - pymdownx.highlight:',
            '      anchor_linenums: true',
            '  - pymdownx.superfences:',
            '      custom_fences:',
            '        - name: mermaid',
            '          class: mermaid',
            '          format: !!python/name:pymdownx.superfences.fence_code_format',
            '  - admonition',
            '  - pymdownx.details',
            '  - pymdownx.inlinehilite',
            '  - pymdownx.snippets',
            '  - pymdownx.tabbed',
            '  - attr_list',
            '',
            'nav:'
        ]
        
        # Add navigation entries
        add_nav_to_config(config_content, nav, indent_level=1)
        
        # Write the configuration file
        with open(config_file, 'w') as f:
            f.write('\n'.join(config_content))
            
        logger.info(f'MkDocs configuration written to {config_file}')
        return str(config_file)
        
    except Exception as e:
        logger.error(f'Failed to generate MkDocs config: {e}', exc_info=True)
        return ''

def build_navigation_structure(module_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build a nested navigation structure from the module tree.
    
    Args:
        module_tree: The module tree dictionary
        
    Returns:
        A list of navigation items for MkDocs configuration
    """
    def nav_processor(key, value, is_package, path, level):
        if is_package:
            # This is a package directory
            children = process_module_tree(value, nav_processor, path, level + 1)
            if children:
                # If the package has an index file, use that as the section entry
                if '__file__' in value:
                    package_path = path + '/index'
                    package_nav = {'index': f'{package_path}.md'}
                    children.insert(0, package_nav)
                return {key: children}
            return None
        else:
            # This is a module file
            return {key: f'{path}.md'}
    
    # Process the tree
    nav = process_module_tree(module_tree, nav_processor)
    return nav

def add_nav_to_config(config_content: List[str], nav_items: List[Dict[str, Any]], indent_level: int = 0):
    """
    Add navigation items to the config content with proper indentation.
    
    Args:
        config_content: List of configuration lines
        nav_items: List of navigation items
        indent_level: Current indentation level
    """
    indent = '  ' * indent_level
    
    for item in nav_items:
        for title, content in item.items():
            if isinstance(content, list):
                config_content.append(f'{indent}- {title}:')
                add_nav_to_config(config_content, content, indent_level + 1)
            else:
                config_content.append(f'{indent}- {title}: {content}')

#################################################
# Core Module
#################################################

def check_dependencies() -> List[str]:
    """
    Check if all required dependencies are installed.
    
    Returns:
        List of missing dependencies
    """
    dependencies = {
        'mkdocstrings': 'mkdocstrings',
        'mkdocs': 'mkdocs',
        'click': 'click',
        'colorama': 'colorama',
        'pydantic': 'pydantic'
    }
    
    missing = []
    
    for package, module in dependencies.items():
        try:
            # For packages we can import
            if module in ['mkdocstrings', 'click', 'colorama', 'pydantic']:
                importlib.util.find_spec(module)
            else:
                # For command-line tools, check if they're available in PATH
                result = subprocess.run(
                    ['which', module] if sys.platform != 'win32' else ['where', module],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    missing.append(package)
        except ImportError:
            missing.append(package)
    
    return missing

@click.command()
@click.option('--start-path', default='./app', help='Directory to start scanning Python files')
@click.option('--output-dir', default='./docs', help='Directory to store documentation')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--project-root', default=None, help='Project root directory (detected automatically if not specified)')
def main(start_path: str, output_dir: str, verbose: bool, project_root: str) -> None:
    """
    Generate project documentation using mkdocstrings with mermaid diagrams.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f'{Fore.GREEN}Starting documentation generation process')
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        logger.error(f'{Fore.RED}Missing dependencies: {", ".join(missing_deps)}', exc_info=True)
        logger.info('Install them using: pip install ' + ' '.join(missing_deps))
        return
    
    # Prepare output directory
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Find Python files
    logger.info(f'Scanning for Python files in {start_path}')
    python_files = find_python_files(start_path)
    logger.info(f'Found {len(python_files)} Python files')
    
    if not python_files:
        logger.error(f'{Fore.RED}No Python files found. Exiting.', exc_info=True)
        return
    
    # If project_root not specified, detect it
    if not project_root:
        project_root = str(Path(os.path.commonpath([str(f) for f in python_files])).parent)
        logger.info(f'Using detected project root: {project_root}')
    
    # Build module tree
    logger.info('Building module tree structure')
    module_tree = build_module_tree(python_files, project_root)
    logger.debug(f'Module tree built with {sum(1 for _ in Path(start_path).rglob("*.py"))} modules')
    
    # Log the module structure to help debug
    if verbose:
        def print_tree(tree, prefix=''):
            for key, value in sorted(tree.items()):
                if key.startswith('__'):
                    continue
                if isinstance(value, dict) and not key.startswith('__'):
                    logger.debug(f'{prefix}+ {key}')
                    print_tree(value, prefix + '  ')
                else:
                    logger.debug(f'{prefix}> {key}')
        logger.debug('Module tree structure:')
        print_tree(module_tree)
    
    # Create output directory structure mapping
    logger.info('Creating output directory structure mapping')
    output_mapping = create_output_structure(module_tree, output_dir)
    logger.info(f'Mapped {len(output_mapping)} documentation files')
    
    if verbose:
        logger.debug("Output mapping details:")
        for module_path, (output_file, source_path) in output_mapping.items():
            logger.debug(f"  {module_path}: {output_file} <- {source_path}")
    
    # Add project root to Python path so imports work correctly when viewing docs
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.debug(f'Added {project_root} to Python path')
    
    # Generate documentation for each module and keep in memory
    logger.info('Generating module documentation with mkdocstrings')
    documentation_content = {}
    success_count = 0
    failed_modules = []
    
    for module_path, (output_file, source_file_path) in output_mapping.items():
        logger.debug(f'Processing module {module_path}')
        
        if source_file_path:
            source_file = Path(source_file_path)
            logger.debug(f'Found source file for {module_path}: {source_file}')
            
            # Generate documentation content
            doc_content = generate_module_docs(module_path, source_file)
            if doc_content:
                logger.debug(f'Successfully generated documentation for {module_path}')
                
                # Generate diagram content
                diagram_content = generate_module_diagram(module_path, source_file)
                if diagram_content:
                    doc_content += '\n' + diagram_content
                    logger.debug(f'Added class diagram for {module_path}')
                
                # Store content in memory
                documentation_content[output_file] = doc_content
                success_count += 1
            else:
                failed_modules.append(module_path)
                logger.warning(f'Failed to generate documentation for {module_path}')
        else:
            # Packages without __init__.py files
            logger.debug(f'No source file for {module_path}, treating as package directory')
            # Create a simple package index
            package_content = [
                f'# Package {module_path}',
                '',
                'This is a package that contains the following modules:',
                ''
            ]
            
            # Find child modules for this package
            children = [m for m in output_mapping.keys() if m.startswith(module_path + '.')]
            if children:
                package_content.append('## Modules')
                package_content.append('')
                for child in sorted(children):
                    child_name = child.split('.')[-1]
                    relative_path = child.replace(module_path + '.', '')
                    package_content.append(f'- [{child_name}]({relative_path}.md)')
                
                documentation_content[output_file] = '\n'.join(package_content)
                success_count += 1
    
    logger.info(f'Successfully generated documentation for {success_count} out of {len(output_mapping)} modules')
    if failed_modules:
        logger.warning(f'Failed to generate documentation for {len(failed_modules)} modules')
        if verbose:
            for module in failed_modules:
                logger.debug(f'  - {module}')
    
    # Generate project-level diagram and table of contents
    logger.info('Generating project-level documentation')
    
    # Project diagram
    project_diagram = generate_project_diagram(os.path.abspath(start_path), output_dir)
    if project_diagram:
        project_diagram_file = Path(output_dir) / 'project_diagram.md'
        documentation_content[project_diagram_file] = project_diagram
    
    # Table of contents
    toc = generate_table_of_contents(module_tree)
    if toc:
        toc_file = Path(output_dir) / 'index.md'
        documentation_content[toc_file] = toc
    
    # Write all documentation to disk at once
    logger.info('Writing documentation files to disk')
    files_written = 0
    
    for output_file, content in documentation_content.items():
        # Ensure directory exists before writing file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(output_file, 'w') as f:
            f.write(content)
        files_written += 1
    
    logger.info(f'Successfully wrote {files_written} documentation files to disk')
    
    # Generate MkDocs configuration
    logger.info('Generating MkDocs configuration')
    config_file = generate_mkdocs_config(project_root, module_tree)
    
    if config_file:
        logger.info(f'MkDocs configuration file created: {config_file}')
        logger.info(f'To preview the documentation, run: mkdocs serve')
        logger.info(f'To build the documentation site, run: mkdocs build')
    else:
        logger.warning('Failed to create MkDocs configuration file')
    
    logger.info(f'{Fore.GREEN}Documentation generation completed!')
    logger.info(f'Documentation available at: {output_dir}')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f'{Fore.RED}An unexpected error occurred: {str(e)}', exc_info=True)
        sys.exit(1)
