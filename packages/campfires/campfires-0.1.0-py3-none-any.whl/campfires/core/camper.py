"""
Base Camper class for individual models or tools within a campfire.
"""

import json
import yaml
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from jinja2 import Template, Environment, FileSystemLoader

from .torch import Torch

if TYPE_CHECKING:
    from ..party_box.box_driver import BoxDriver


class Camper(ABC):
    """
    Base class for individual models or tools within a campfire.
    
    Campers collaborate to produce a single, refined output (torch).
    Each camper can load RAG templates, process prompts, and interact
    with the Party Box for asset management.
    """
    
    def __init__(self, party_box: "BoxDriver", config: Dict[str, Any]):
        """
        Initialize a camper.
        
        Args:
            party_box: Reference to the Party Box for asset storage
            config: Configuration dictionary for this camper
        """
        self.party_box = party_box
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.jinja_env = Environment(
            loader=FileSystemLoader(config.get("template_dir", "templates"))
        )
        
    def load_rag(self, template_path: str, **kwargs) -> str:
        """
        Load a JSON/YAML template and embed dynamic values.
        
        Args:
            template_path: Path to the template file
            **kwargs: Dynamic values to embed in the template
            
        Returns:
            Formatted prompt string
        """
        template_file = Path(template_path)
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Load template content
        with open(template_file, 'r', encoding='utf-8') as f:
            if template_file.suffix.lower() in ['.yaml', '.yml']:
                template_data = yaml.safe_load(f)
            elif template_file.suffix.lower() == '.json':
                template_data = json.load(f)
            else:
                # Treat as plain text template
                template_content = f.read()
                template = Template(template_content)
                return template.render(**kwargs)
        
        # Add default dynamic values
        default_values = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(time.time()),
            'camper_name': self.name,
            **kwargs
        }
        
        # If template_data is a dict, look for a 'prompt' or 'template' field
        if isinstance(template_data, dict):
            prompt_template = template_data.get('prompt', template_data.get('template', ''))
            if isinstance(prompt_template, str):
                template = Template(prompt_template)
                return template.render(**default_values)
            else:
                # Return the entire template data as JSON string
                template = Template(json.dumps(template_data, indent=2))
                return template.render(**default_values)
        else:
            # Template data is a string
            template = Template(str(template_data))
            return template.render(**default_values)
    
    @abstractmethod
    async def override_prompt(self, raw_prompt: str) -> Dict[str, Any]:
        """
        Custom API calls for this camper.
        
        Developers implement this method to integrate their existing
        model wrappers (e.g., OpenRouter, local models, APIs).
        
        Args:
            raw_prompt: The formatted prompt to process
            
        Returns:
            Dictionary containing the response and any metadata
        """
        pass
    
    async def process(self, input_torch: Optional[Torch] = None) -> Torch:
        """
        Main processing logic for the camper.
        
        Args:
            input_torch: Optional input torch from previous campfire
            
        Returns:
            Output torch with this camper's results
        """
        try:
            # Prepare context from input torch
            context = {}
            if input_torch:
                context.update({
                    'input_claim': input_torch.claim,
                    'input_path': input_torch.path,
                    'input_metadata': input_torch.metadata,
                    'input_confidence': input_torch.confidence
                })
            
            # Load and format prompt if template is specified
            prompt = ""
            if 'template_path' in self.config:
                prompt = self.load_rag(self.config['template_path'], **context)
            elif 'prompt' in self.config:
                template = Template(self.config['prompt'])
                prompt = template.render(**context)
            else:
                # Use a default prompt
                prompt = f"Process the following input: {context}"
            
            # Call the custom override_prompt method
            response = await self.override_prompt(prompt)
            
            # Extract claim and other data from response
            claim = response.get('claim', response.get('content', str(response)))
            confidence = response.get('confidence', 1.0)
            metadata = response.get('metadata', {})
            asset_path = response.get('path')
            
            # Store any assets in Party Box if provided
            if 'asset_data' in response:
                asset_hash = await self.party_box.put(
                    f"{self.name}_{int(time.time())}", 
                    response['asset_data']
                )
                asset_path = f"./party_box/{asset_hash}"
            
            # Create output torch
            output_torch = Torch(
                claim=claim,
                path=asset_path,
                confidence=confidence,
                metadata={
                    'camper_name': self.name,
                    'processing_time': time.time(),
                    **metadata
                },
                source_campfire=self.config.get('campfire_name', 'unknown'),
                channel=self.config.get('output_channel', 'default')
            )
            
            return output_torch
            
        except Exception as e:
            # Return error torch
            error_torch = Torch(
                claim=f"Error in {self.name}: {str(e)}",
                confidence=0.0,
                metadata={
                    'error': True,
                    'error_type': type(e).__name__,
                    'camper_name': self.name
                },
                source_campfire=self.config.get('campfire_name', 'unknown'),
                channel=self.config.get('output_channel', 'default')
            )
            return error_torch
    
    async def store_asset(self, data: bytes, filename: str) -> str:
        """
        Store an asset in the Party Box.
        
        Args:
            data: Asset data as bytes
            filename: Suggested filename
            
        Returns:
            Asset hash/key for retrieval
        """
        return await self.party_box.put(filename, data)
    
    async def get_asset(self, asset_key: str):
        """
        Retrieve an asset from the Party Box.
        
        Args:
            asset_key: Asset hash/key
            
        Returns:
            Asset data or path
        """
        return await self.party_box.get(asset_key)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def set_party_box(self, party_box: "BoxDriver") -> None:
        """
        Set the party box reference for this camper.
        
        Args:
            party_box: The party box driver instance
        """
        self.party_box = party_box
    
    def set_campfire_name(self, campfire_name: str) -> None:
        """
        Set the campfire name for this camper.
        
        Args:
            campfire_name: Name of the campfire this camper belongs to
        """
        self.campfire_name = campfire_name
    
    def __str__(self) -> str:
        """String representation of the camper."""
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(name={self.name}, config={self.config})"


class SimpleCamper(Camper):
    """
    A simple camper implementation for testing and basic use cases.
    """
    
    async def override_prompt(self, raw_prompt: str) -> Dict[str, Any]:
        """
        Simple implementation that echoes the prompt.
        
        Args:
            raw_prompt: The prompt to process
            
        Returns:
            Dictionary with echoed content
        """
        return {
            'claim': f"Processed: {raw_prompt}",
            'confidence': 0.8,
            'metadata': {
                'prompt_length': len(raw_prompt),
                'processing_method': 'echo'
            }
        }