"""Configuration loader for YAML and JSON files."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ..types.core import ConfigurationError


class ConfigLoader:
    """Loads configuration from YAML and JSON files."""
    
    def __init__(self, config_path: str = "config"):
        """Initialize the config loader.
        
        Args:
            config_path: Path to the configuration directory
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise ConfigurationError(f"Config path does not exist: {config_path}")
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file.
        
        Args:
            filename: Name of the YAML file
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        file_path = self.config_path / filename
        if not file_path.exists():
            raise ConfigurationError(f"YAML file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading {file_path}: {e}")
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON configuration file.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        file_path = self.config_path / filename
        if not file_path.exists():
            raise ConfigurationError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading {file_path}: {e}")
    
    def load_instructions(self) -> Dict[str, Any]:
        """Load agent instructions from YAML file.
        
        Returns:
            Dictionary containing agent instructions
        """
        return self.load_yaml("instructions.yaml")
    
    def load_actions(self) -> Dict[str, Any]:
        """Load agent actions from YAML file.
        
        Returns:
            Dictionary containing agent actions
        """
        return self.load_yaml("actions.yaml")
    
    def load_intent_synonyms(self) -> Dict[str, List[str]]:
        """Load intent synonyms from JSON file.
        
        Returns:
            Dictionary mapping intents to their synonyms
        """
        return self.load_json("intent-synonyms.json")
    
    def load_discover_products(self) -> Dict[str, Any]:
        """Load discover products configuration from JSON file.
        
        Returns:
            Dictionary containing discover products configuration
        """
        return self.load_json("DiscoverProducts.json")
    
    def load_tool_playbook(self) -> str:
        """Load tool playbook from markdown file.
        
        Returns:
            String containing the tool playbook content
        """
        file_path = self.config_path / "tool-playbook.md"
        if not file_path.exists():
            raise ConfigurationError(f"Tool playbook not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise ConfigurationError(f"Error loading tool playbook: {e}")
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Load all configuration files.
        
        Returns:
            Dictionary containing all configurations
        """
        configs = {}
        
        try:
            configs['instructions'] = self.load_instructions()
        except ConfigurationError:
            configs['instructions'] = {}
        
        try:
            configs['actions'] = self.load_actions()
        except ConfigurationError:
            configs['actions'] = {}
        
        try:
            configs['intent_synonyms'] = self.load_intent_synonyms()
        except ConfigurationError:
            configs['intent_synonyms'] = {}
        
        try:
            configs['discover_products'] = self.load_discover_products()
        except ConfigurationError:
            configs['discover_products'] = {}
        
        try:
            configs['tool_playbook'] = self.load_tool_playbook()
        except ConfigurationError:
            configs['tool_playbook'] = ""
        
        return configs
