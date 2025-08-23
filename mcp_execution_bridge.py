#!/usr/bin/env python3
"""
MCP Execution Bridge

Dynamically executes SDK methods based on MCP tool calls.
Handles client initialization, parameter conversion, and result serialization.
"""

import importlib
import json
import inspect
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)

class MCPExecutionBridge:
    """
    Universal execution bridge for MCP tools.
    Dynamically calls SDK methods without SDK-specific code.
    """
    
    def __init__(self, sdk_name: str, sdk_module: str):
        self.sdk_name = sdk_name
        self.sdk_module = sdk_module
        self.client_cache = {}  # Cache initialized clients
        self.module_cache = {}  # Cache imported modules
        
    async def execute_tool(self, tool_name: str, sdk_method: str, 
                          arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool by calling the underlying SDK method.
        
        Args:
            tool_name: Name of the MCP tool
            sdk_method: Full path to SDK method (e.g., 'github.Github.get_user')
            arguments: Tool arguments from MCP
            
        Returns:
            Execution result with status and data
        """
        try:
            # Parse method path
            parts = sdk_method.split('.')
            if len(parts) < 2:
                raise ValueError(f"Invalid method path: {sdk_method}")
            
            # Get the method object
            method_obj = self._get_method_object(sdk_method)
            
            # Prepare arguments
            prepared_args = self._prepare_arguments(method_obj, arguments)
            
            # Execute the method
            result = await self._execute_method(method_obj, prepared_args)
            
            # Serialize the result
            serialized = self._serialize_result(result)
            
            return {
                "status": "success",
                "tool": tool_name,
                "result": serialized
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(e)
            }
    
    def _get_method_object(self, sdk_method: str) -> Any:
        """Get the actual method object from its path."""
        parts = sdk_method.split('.')
        
        # Determine if this is a class method or module function
        if len(parts) == 2:
            # Module-level function (e.g., 'requests.get')
            module_name = parts[0]
            function_name = parts[1]
            
            module = self._get_or_import_module(module_name)
            return getattr(module, function_name)
        
        else:
            # Class method - need to get or create instance
            module_path = '.'.join(parts[:-2])
            class_name = parts[-2]
            method_name = parts[-1]
            
            # Get or create class instance
            instance = self._get_or_create_instance(module_path, class_name)
            
            # Get the method
            return getattr(instance, method_name)
    
    def _get_or_import_module(self, module_name: str) -> Any:
        """Import and cache a module."""
        if module_name not in self.module_cache:
            self.module_cache[module_name] = importlib.import_module(module_name)
        return self.module_cache[module_name]
    
    def _get_or_create_instance(self, module_path: str, class_name: str) -> Any:
        """Get or create an instance of a class."""
        cache_key = f"{module_path}.{class_name}"
        
        if cache_key not in self.client_cache:
            # Import the module
            module = self._get_or_import_module(module_path)
            
            # Get the class
            cls = getattr(module, class_name)
            
            # Create instance based on SDK type
            instance = self._create_sdk_instance(cls, class_name)
            
            self.client_cache[cache_key] = instance
        
        return self.client_cache[cache_key]
    
    def _create_sdk_instance(self, cls: type, class_name: str) -> Any:
        """
        Create an SDK client instance.
        This is where SDK-specific initialization can be configured.
        """
        # Try to create with no arguments first (many SDKs support this)
        try:
            return cls()
        except TypeError:
            pass
        
        # GitHub-style initialization
        if 'github' in self.sdk_name.lower():
            # Check for token in environment or config
            import os
            token = os.getenv('GITHUB_TOKEN')
            if token:
                return cls(token)
            else:
                return cls()  # Anonymous access
        
        # Kubernetes-style initialization
        elif 'kubernetes' in self.sdk_name.lower():
            if 'Api' in class_name:
                # Kubernetes API clients need configuration
                from kubernetes import config, client
                try:
                    config.load_incluster_config()
                except:
                    try:
                        config.load_kube_config()
                    except:
                        pass
                
                # Create API client
                api_client = client.ApiClient()
                return cls(api_client)
        
        # Azure-style initialization
        elif 'azure' in self.sdk_name.lower():
            if 'Client' in class_name:
                # Azure clients need credentials
                try:
                    from azure.identity import DefaultAzureCredential
                    credential = DefaultAzureCredential()
                    
                    # Check if subscription ID is needed
                    import os
                    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
                    
                    if subscription_id:
                        return cls(credential, subscription_id)
                    else:
                        return cls(credential)
                except ImportError:
                    # Fall back to no credentials
                    return cls()
        
        # Default: try with empty initialization
        return cls()
    
    def _prepare_arguments(self, method: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare arguments for method execution."""
        # Get method signature
        sig = inspect.signature(method)
        
        prepared = {}
        for param_name, param in sig.parameters.items():
            # Skip self/cls
            if param_name in ['self', 'cls']:
                continue
            
            # Check if argument was provided
            if param_name in arguments:
                prepared[param_name] = arguments[param_name]
            elif param.default != inspect.Parameter.empty:
                # Use default value (don't pass it)
                pass
            elif param_name == 'kwargs' and param.kind == inspect.Parameter.VAR_KEYWORD:
                # Pass remaining arguments as kwargs
                for key, value in arguments.items():
                    if key not in prepared:
                        prepared[key] = value
        
        return prepared
    
    async def _execute_method(self, method: Any, arguments: Dict[str, Any]) -> Any:
        """Execute the method with proper async handling."""
        # Check if method is async
        if inspect.iscoroutinefunction(method):
            # Async method
            return await method(**arguments)
        else:
            # Sync method - run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: method(**arguments))
    
    def _serialize_result(self, result: Any) -> Any:
        """Serialize the result to JSON-compatible format."""
        if result is None:
            return None
        
        # Try common serialization methods
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        elif hasattr(result, 'as_dict'):
            return result.as_dict()
        elif hasattr(result, 'model_dump'):
            return result.model_dump()
        elif hasattr(result, '__dict__'):
            # Try to serialize object attributes
            try:
                return {k: v for k, v in result.__dict__.items() 
                       if not k.startswith('_') and self._is_serializable(v)}
            except:
                pass
        
        # Check if it's already JSON-serializable
        try:
            json.dumps(result)
            return result
        except:
            pass
        
        # Handle iterables
        if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
            try:
                items = []
                for item in result:
                    serialized_item = self._serialize_result(item)
                    items.append(serialized_item)
                    # Limit to prevent huge responses
                    if len(items) >= 100:
                        items.append({"note": "Results truncated to 100 items"})
                        break
                return items
            except:
                pass
        
        # Fall back to string representation
        return str(result)
    
    def _is_serializable(self, obj: Any) -> bool:
        """Check if an object is JSON serializable."""
        try:
            json.dumps(obj)
            return True
        except:
            return False