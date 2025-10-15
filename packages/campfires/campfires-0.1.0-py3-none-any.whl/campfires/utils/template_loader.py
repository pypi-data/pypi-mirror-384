"""
Template loading utilities for RAG prompts and configurations.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Loads and renders templates for RAG prompts and configurations.
    
    Supports Jinja2 templating with YAML and JSON data loading.
    """
    
    def __init__(self, template_dirs: List[str] = None, config_dirs: List[str] = None):
        """
        Initialize the template loader.
        
        Args:
            template_dirs: Directories to search for templates
            config_dirs: Directories to search for configuration files
        """
        self.template_dirs = template_dirs or ["./templates", "./prompts"]
        self.config_dirs = config_dirs or ["./config", "./data"]
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dirs),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['json'] = json.dumps
        self.env.filters['yaml'] = yaml.dump
        
        # Cache for loaded configurations
        self._config_cache: Dict[str, Any] = {}
        self._template_cache: Dict[str, Template] = {}
    
    def load_template(self, template_name: str) -> Template:
        """
        Load a Jinja2 template.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Jinja2 Template object
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        try:
            template = self.env.get_template(template_name)
            self._template_cache[template_name] = template
            return template
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """
        Render a template with the given variables.
        
        Args:
            template_name: Name of the template file
            **kwargs: Variables to pass to the template
            
        Returns:
            Rendered template string
        """
        template = self.load_template(template_name)
        return template.render(**kwargs)
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file (YAML or JSON).
        
        Args:
            config_name: Name of the config file (with or without extension)
            
        Returns:
            Configuration dictionary
        """
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # Try different extensions
        extensions = ['.yaml', '.yml', '.json']
        if '.' in config_name:
            # Already has extension
            extensions = ['']
        
        for config_dir in self.config_dirs:
            for ext in extensions:
                config_path = Path(config_dir) / f"{config_name}{ext}"
                
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            if config_path.suffix.lower() in ['.yaml', '.yml']:
                                config = yaml.safe_load(f)
                            else:
                                config = json.load(f)
                        
                        self._config_cache[config_name] = config
                        logger.debug(f"Loaded config: {config_path}")
                        return config
                        
                    except Exception as e:
                        logger.error(f"Error loading config {config_path}: {e}")
                        continue
        
        raise FileNotFoundError(f"Configuration file not found: {config_name}")
    
    def render_with_config(self, template_name: str, config_name: str, **extra_vars) -> str:
        """
        Render a template using a configuration file.
        
        Args:
            template_name: Name of the template file
            config_name: Name of the configuration file
            **extra_vars: Additional variables to pass to the template
            
        Returns:
            Rendered template string
        """
        config = self.load_config(config_name)
        
        # Merge config with extra variables (extra_vars take precedence)
        template_vars = {**config, **extra_vars}
        
        return self.render_template(template_name, **template_vars)
    
    def list_templates(self) -> List[str]:
        """
        List all available templates.
        
        Returns:
            List of template names
        """
        templates = []
        for template_dir in self.template_dirs:
            template_path = Path(template_dir)
            if template_path.exists():
                for file_path in template_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.j2', '.jinja2']:
                        # Get relative path from template directory
                        rel_path = file_path.relative_to(template_path)
                        templates.append(str(rel_path))
        
        return sorted(templates)
    
    def list_configs(self) -> List[str]:
        """
        List all available configuration files.
        
        Returns:
            List of configuration file names
        """
        configs = []
        for config_dir in self.config_dirs:
            config_path = Path(config_dir)
            if config_path.exists():
                for file_path in config_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix in ['.yaml', '.yml', '.json']:
                        # Get relative path without extension
                        rel_path = file_path.relative_to(config_path)
                        config_name = str(rel_path.with_suffix(''))
                        configs.append(config_name)
        
        return sorted(configs)
    
    def clear_cache(self) -> None:
        """Clear template and config caches."""
        self._template_cache.clear()
        self._config_cache.clear()
        logger.debug("Template and config caches cleared")
    
    def add_template_dir(self, directory: str) -> None:
        """
        Add a new template directory.
        
        Args:
            directory: Path to template directory
        """
        if directory not in self.template_dirs:
            self.template_dirs.append(directory)
            # Recreate Jinja2 environment with new directories
            self.env = Environment(
                loader=FileSystemLoader(self.template_dirs),
                trim_blocks=True,
                lstrip_blocks=True
            )
            self.env.filters['json'] = json.dumps
            self.env.filters['yaml'] = yaml.dump
            self.clear_cache()
    
    def add_config_dir(self, directory: str) -> None:
        """
        Add a new configuration directory.
        
        Args:
            directory: Path to configuration directory
        """
        if directory not in self.config_dirs:
            self.config_dirs.append(directory)
            self.clear_cache()


class RAGTemplateManager:
    """
    Specialized template manager for RAG prompts.
    """
    
    def __init__(self, template_loader: TemplateLoader = None):
        """
        Initialize RAG template manager.
        
        Args:
            template_loader: TemplateLoader instance to use
        """
        self.loader = template_loader or TemplateLoader()
        
        # Common RAG template variables
        self.default_vars = {
            'max_tokens': 2000,
            'temperature': 0.7,
            'system_role': 'You are a helpful AI assistant.',
        }
    
    def load_rag_prompt(
        self, 
        template_name: str, 
        context: str = "", 
        query: str = "", 
        **kwargs
    ) -> str:
        """
        Load and render a RAG prompt template.
        
        Args:
            template_name: Name of the RAG template
            context: Context information for the prompt
            query: User query
            **kwargs: Additional template variables
            
        Returns:
            Rendered RAG prompt
        """
        template_vars = {
            **self.default_vars,
            'context': context,
            'query': query,
            **kwargs
        }
        
        return self.loader.render_template(template_name, **template_vars)
    
    def create_system_prompt(self, role: str, instructions: List[str] = None) -> str:
        """
        Create a system prompt for LLM.
        
        Args:
            role: Role description for the AI
            instructions: List of specific instructions
            
        Returns:
            System prompt string
        """
        prompt_parts = [f"You are {role}."]
        
        if instructions:
            prompt_parts.append("\nInstructions:")
            for i, instruction in enumerate(instructions, 1):
                prompt_parts.append(f"{i}. {instruction}")
        
        return "\n".join(prompt_parts)
    
    def create_few_shot_prompt(
        self, 
        task_description: str, 
        examples: List[Dict[str, str]], 
        query: str
    ) -> str:
        """
        Create a few-shot learning prompt.
        
        Args:
            task_description: Description of the task
            examples: List of example input/output pairs
            query: Current query to process
            
        Returns:
            Few-shot prompt string
        """
        prompt_parts = [task_description, "\nExamples:"]
        
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Input: {example.get('input', '')}")
            prompt_parts.append(f"Output: {example.get('output', '')}")
        
        prompt_parts.append(f"\nNow process this input:")
        prompt_parts.append(f"Input: {query}")
        prompt_parts.append("Output:")
        
        return "\n".join(prompt_parts)


# Global template loader instance
_global_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """
    Get the global template loader instance.
    
    Returns:
        Global TemplateLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = TemplateLoader()
    return _global_loader


def set_template_loader(loader: TemplateLoader) -> None:
    """
    Set the global template loader instance.
    
    Args:
        loader: TemplateLoader instance to use globally
    """
    global _global_loader
    _global_loader = loader


def render_template(template_name: str, **kwargs) -> str:
    """
    Convenience function to render a template using the global loader.
    
    Args:
        template_name: Name of the template file
        **kwargs: Variables to pass to the template
        
    Returns:
        Rendered template string
    """
    return get_template_loader().render_template(template_name, **kwargs)


def load_config(config_name: str) -> Dict[str, Any]:
    """
    Convenience function to load a config using the global loader.
    
    Args:
        config_name: Name of the configuration file
        
    Returns:
        Configuration dictionary
    """
    return get_template_loader().load_config(config_name)