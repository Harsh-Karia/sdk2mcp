#!/usr/bin/env python3
"""
Plugin-Based SDK Configuration System

Provides optional configuration for better SDK support while keeping
the core system completely universal.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class AuthConfig:
    """Authentication configuration for an SDK."""
    type: str  # "token", "oauth", "credentials", "key_pair", etc.
    env_vars: List[str] = field(default_factory=list)  # Environment variables to check
    fallback: str = "anonymous"  # Fallback mode if no auth found
    required: bool = False  # Whether auth is required
    config_files: List[str] = field(default_factory=list)  # Config files to check

@dataclass
class ClientConfig:
    """Client initialization configuration."""
    class_path: str  # e.g., "github.Github" 
    init_params: Dict[str, Any] = field(default_factory=dict)  # Parameters for __init__
    setup_methods: List[str] = field(default_factory=list)  # Methods to call after init

@dataclass
class SDKPlugin:
    """Configuration plugin for a specific SDK."""
    name: str
    sdk_module: str
    auth: Optional[AuthConfig] = None
    client: Optional[ClientConfig] = None
    hints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PluginManager:
    """
    Manages SDK configuration plugins.
    
    Plugins are optional - the system works without them but they provide
    better authentication, client initialization, and optimization hints.
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, SDKPlugin] = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all plugin configurations from the plugins directory."""
        if not self.plugins_dir.exists():
            logger.info("No plugins directory found, creating one")
            self.plugins_dir.mkdir(exist_ok=True)
            self._create_default_plugins()
            return
        
        for plugin_file in self.plugins_dir.glob("*.yaml"):
            try:
                with open(plugin_file) as f:
                    config = yaml.safe_load(f)
                
                plugin = self._parse_plugin_config(config)
                self.plugins[plugin.name] = plugin
                logger.info(f"Loaded plugin: {plugin.name}")
                
            except Exception as e:
                logger.warning(f"Failed to load plugin {plugin_file}: {e}")
    
    def _parse_plugin_config(self, config: Dict) -> SDKPlugin:
        """Parse a plugin configuration dictionary into an SDKPlugin object."""
        plugin = SDKPlugin(
            name=config['name'],
            sdk_module=config['sdk_module'],
            metadata=config.get('metadata', {})
        )
        
        # Parse auth config
        if 'auth' in config:
            auth_config = config['auth']
            plugin.auth = AuthConfig(
                type=auth_config['type'],
                env_vars=auth_config.get('env_vars', []),
                fallback=auth_config.get('fallback', 'anonymous'),
                required=auth_config.get('required', False),
                config_files=auth_config.get('config_files', [])
            )
        
        # Parse client config
        if 'client' in config:
            client_config = config['client']
            plugin.client = ClientConfig(
                class_path=client_config['class_path'],
                init_params=client_config.get('init_params', {}),
                setup_methods=client_config.get('setup_methods', [])
            )
        
        # Parse hints
        plugin.hints = config.get('hints', {})
        
        return plugin
    
    def get_plugin(self, sdk_name: str) -> Optional[SDKPlugin]:
        """Get plugin configuration for a specific SDK."""
        # Try exact match first
        if sdk_name in self.plugins:
            return self.plugins[sdk_name]
        
        # Try normalized names
        normalized = sdk_name.lower().replace('-', '_').replace('.', '_')
        for plugin_name, plugin in self.plugins.items():
            if plugin_name.lower().replace('-', '_') == normalized:
                return plugin
            
            # Also check module name match
            if plugin.sdk_module.lower().replace('.', '_') == normalized:
                return plugin
        
        return None
    
    def get_auth_info(self, sdk_name: str) -> Optional[Dict[str, Any]]:
        """Get authentication information for an SDK."""
        plugin = self.get_plugin(sdk_name)
        if not plugin or not plugin.auth:
            return None
        
        auth_config = plugin.auth
        auth_info = {
            'type': auth_config.type,
            'fallback': auth_config.fallback,
            'required': auth_config.required
        }
        
        # Check environment variables
        for env_var in auth_config.env_vars:
            value = os.getenv(env_var)
            if value:
                auth_info['value'] = value
                auth_info['source'] = f"env:{env_var}"
                break
        
        # Check config files
        if 'value' not in auth_info:
            for config_file in auth_config.config_files:
                config_path = Path(config_file).expanduser()
                if config_path.exists():
                    auth_info['config_file'] = str(config_path)
                    auth_info['source'] = f"file:{config_file}"
                    break
        
        return auth_info
    
    def get_client_config(self, sdk_name: str) -> Optional[ClientConfig]:
        """Get client initialization configuration for an SDK."""
        plugin = self.get_plugin(sdk_name)
        return plugin.client if plugin else None
    
    def get_hints(self, sdk_name: str) -> Dict[str, Any]:
        """Get optimization hints for an SDK."""
        plugin = self.get_plugin(sdk_name)
        return plugin.hints if plugin else {}
    
    def create_configured_client(self, sdk_name: str):
        """
        Create a properly configured client for an SDK.
        Returns None if no plugin configuration exists.
        """
        plugin = self.get_plugin(sdk_name)
        if not plugin or not plugin.client:
            return None
        
        try:
            # Import the class
            module_path, class_name = plugin.client.class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            client_class = getattr(module, class_name)
            
            # Prepare initialization parameters
            init_params = {}
            
            # Add configured parameters
            for param, value in plugin.client.init_params.items():
                if isinstance(value, str) and value.startswith('${'):
                    # Variable substitution
                    if value.startswith('${auth.'):
                        auth_info = self.get_auth_info(sdk_name)
                        if auth_info and 'value' in auth_info:
                            init_params[param] = auth_info['value']
                    elif value.startswith('${env.'):
                        env_var = value[6:-1]  # Extract env var name
                        env_value = os.getenv(env_var)
                        if env_value:
                            init_params[param] = env_value
                else:
                    init_params[param] = value
            
            # Create the client
            client = client_class(**init_params)
            
            # Run setup methods if any
            for method_name in plugin.client.setup_methods:
                method = getattr(client, method_name, None)
                if method and callable(method):
                    method()
            
            return client
            
        except Exception as e:
            logger.warning(f"Failed to create configured client for {sdk_name}: {e}")
            return None
    
    def _create_default_plugins(self):
        """Create default plugin configurations for common SDKs."""
        default_plugins = {
            'github.yaml': {
                'name': 'github',
                'sdk_module': 'github',
                'metadata': {
                    'description': 'GitHub API v3/v4 SDK',
                    'homepage': 'https://github.com/PyGithub/PyGithub'
                },
                'auth': {
                    'type': 'token',
                    'env_vars': ['GITHUB_TOKEN', 'GITHUB_ACCESS_TOKEN'],
                    'fallback': 'anonymous',
                    'required': False
                },
                'client': {
                    'class_path': 'github.Github',
                    'init_params': {
                        'auth': '${auth.value}'
                    }
                },
                'hints': {
                    'prioritize_methods': ['get_user', 'get_repo', 'create_issue', 'get_organization'],
                    'important_classes': ['Repository', 'Issue', 'PullRequest', 'User', 'Organization'],
                    'exclude_patterns': ['_with_http_info$'],
                    'boost_patterns': ['^(get|create|list)_']
                }
            },
            
            'kubernetes.yaml': {
                'name': 'kubernetes',
                'sdk_module': 'kubernetes',
                'metadata': {
                    'description': 'Kubernetes Python client',
                    'homepage': 'https://github.com/kubernetes-client/python'
                },
                'auth': {
                    'type': 'kubeconfig',
                    'config_files': ['~/.kube/config'],
                    'fallback': 'incluster'
                },
                'client': {
                    'class_path': 'kubernetes.client.ApiClient',
                    'setup_methods': ['kubernetes.config.load_kube_config']
                },
                'hints': {
                    'important_classes': ['CoreV1Api', 'AppsV1Api', 'BatchV1Api'],
                    'exclude_patterns': ['_with_http_info$', '^connect_'],
                    'boost_patterns': ['^(create|list|get|delete|patch)_namespaced_']
                }
            },
            
            'boto3.yaml': {
                'name': 'boto3', 
                'sdk_module': 'boto3',
                'metadata': {
                    'description': 'AWS SDK for Python',
                    'homepage': 'https://boto3.amazonaws.com/'
                },
                'auth': {
                    'type': 'aws_credentials',
                    'env_vars': ['AWS_ACCESS_KEY_ID', 'AWS_PROFILE'],
                    'config_files': ['~/.aws/credentials', '~/.aws/config'],
                    'fallback': 'default_session'
                },
                'hints': {
                    'prioritize_methods': ['client', 'resource', 'Session'],
                    'boost_patterns': ['^(list|get|create|delete)_']
                }
            }
        }
        
        for filename, config in default_plugins.items():
            plugin_file = self.plugins_dir / filename
            with open(plugin_file, 'w') as f:
                yaml.dump(config, f, indent=2, default_flow_style=False)
        
        logger.info(f"Created {len(default_plugins)} default plugin configurations")

# Global plugin manager instance
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager