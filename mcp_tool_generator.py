#!/usr/bin/env python3
"""
Universal MCP Tool Generator

Converts discovered SDK methods into MCP tools with proper JSON schemas.
Works with ANY Python SDK without SDK-specific code.
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from introspector_v2 import MethodInfo, ParameterInfo
import inspect

@dataclass
class MCPTool:
    """Represents an MCP tool generated from SDK methods."""
    name: str  # MCP tool name (e.g., "github_repository_create_issue")
    description: str
    input_schema: Dict[str, Any]  # JSON Schema
    sdk_method: str  # Full method path for execution
    flags: Dict[str, bool]  # destructive, paginated, lro, etc.
    
@dataclass 
class MCPToolGroup:
    """Groups related MCP tools together."""
    name: str  # e.g., "github_repository_operations"
    description: str
    tools: List[MCPTool]
    sdk_module: str

class UniversalMCPToolGenerator:
    """
    Generates MCP tools from discovered SDK methods.
    Completely universal - works with any Python SDK.
    """
    
    def __init__(self, sdk_name: str):
        self.sdk_name = sdk_name
        self.generated_tools = []
        self.tool_groups = {}
        
    def generate_tools(self, methods: List[MethodInfo], 
                       patterns: Optional[Dict] = None) -> List[MCPToolGroup]:
        """
        Generate MCP tools from discovered methods.
        
        Args:
            methods: List of discovered methods from introspector
            patterns: Optional pattern analysis results
            
        Returns:
            List of MCP tool groups
        """
        # Group methods by owner/class for better organization
        method_groups = self._group_methods_by_owner(methods)
        
        # Generate tool groups
        tool_groups = []
        for owner, owner_methods in method_groups.items():
            tool_group = self._generate_tool_group(owner, owner_methods)
            if tool_group and tool_group.tools:
                tool_groups.append(tool_group)
        
        return tool_groups
    
    def _group_methods_by_owner(self, methods: List[MethodInfo]) -> Dict[str, List[MethodInfo]]:
        """Group methods by their owner class for logical organization."""
        groups = {}
        
        for method in methods:
            owner = str(method.parent_class) if method.parent_class else 'module'
            
            # Simplify owner name for grouping
            owner_key = self._simplify_owner_name(owner)
            
            if owner_key not in groups:
                groups[owner_key] = []
            groups[owner_key].append(method)
        
        return groups
    
    def _simplify_owner_name(self, owner: str) -> str:
        """
        Simplify owner name for cleaner tool naming.
        E.g., 'github.MainClass.Github' -> 'github'
        """
        if not owner or owner == 'module':
            return self.sdk_name
        
        # Remove module prefixes and get class name
        parts = owner.split('.')
        
        # For Azure, keep the service identifier
        if 'azure' in owner.lower():
            if 'blob' in owner.lower():
                if 'BlobClient' in owner:
                    return 'blob'
                elif 'ContainerClient' in owner:
                    return 'container'
                elif 'BlobServiceClient' in owner:
                    return 'blob_service'
            elif 'resource' in owner.lower():
                if 'ResourceGroups' in owner:
                    return 'resource_groups'
                elif 'Deployments' in owner:
                    return 'deployments'
        
        # For Kubernetes, extract API version
        if 'kubernetes' in owner.lower():
            for part in parts:
                if 'Api' in part:
                    # CoreV1Api -> core_v1
                    api_name = re.sub(r'([A-Z])', r'_\1', part).lower()
                    return api_name.strip('_').replace('_api', '')
        
        # For GitHub, use the class name
        if 'github' in owner.lower():
            for part in parts:
                if part in ['Github', 'Repository', 'Issue', 'PullRequest', 'User']:
                    return part.lower()
        
        # Default: use last meaningful part
        meaningful = [p for p in parts if not p.startswith('_') and p not in ['client', 'api']]
        if meaningful:
            return meaningful[-1].lower()
        
        return self.sdk_name
    
    def _generate_tool_group(self, owner: str, methods: List[MethodInfo]) -> MCPToolGroup:
        """Generate an MCP tool group for methods from the same owner."""
        tools = []
        
        for method in methods:
            tool = self._generate_mcp_tool(method, owner)
            if tool:
                tools.append(tool)
        
        if not tools:
            return None
        
        # Create tool group
        return MCPToolGroup(
            name=f"{self.sdk_name}_{owner}_operations",
            description=f"{owner.replace('_', ' ').title()} operations for {self.sdk_name}",
            tools=tools,
            sdk_module=self.sdk_name
        )
    
    def _generate_mcp_tool(self, method: MethodInfo, owner_simplified: str) -> Optional[MCPTool]:
        """Generate a single MCP tool from a method."""
        # Generate tool name
        tool_name = self._generate_tool_name(method, owner_simplified)
        
        # Generate description
        description = self._generate_description(method)
        
        # Generate JSON schema for inputs
        input_schema = self._generate_input_schema(method)
        
        # Generate flags
        flags = self._generate_flags(method)
        
        return MCPTool(
            name=tool_name,
            description=description,
            input_schema=input_schema,
            sdk_method=method.full_name,
            flags=flags
        )
    
    def _generate_tool_name(self, method: MethodInfo, owner: str) -> str:
        """
        Generate MCP tool name from method.
        E.g., 'create_issue' -> 'github_repository_create_issue'
        """
        # Clean method name
        method_name = method.name.lower()
        
        # Remove common prefixes for cleaner names
        for prefix in ['get_', 'list_', 'create_', 'update_', 'delete_']:
            if method_name.startswith(prefix):
                method_name = prefix.rstrip('_') + '_' + method_name[len(prefix):]
                break
        
        # Build tool name
        parts = [self.sdk_name]
        
        if owner and owner != self.sdk_name:
            parts.append(owner)
        
        parts.append(method_name)
        
        # Clean up the name
        tool_name = '_'.join(parts)
        tool_name = re.sub(r'_+', '_', tool_name)  # Remove double underscores
        tool_name = tool_name.strip('_')
        
        return tool_name
    
    def _generate_description(self, method: MethodInfo) -> str:
        """Generate tool description from method info."""
        if method.docstring:
            # Use first line of docstring
            first_line = method.docstring.split('\n')[0].strip()
            if first_line and len(first_line) < 200:
                return first_line
        
        # Generate from method name
        words = re.findall(r'[A-Za-z][a-z]*', method.name)
        action = ' '.join(words).lower()
        
        return f"{action} operation"
    
    def _generate_input_schema(self, method: MethodInfo) -> Dict[str, Any]:
        """Generate JSON Schema for method parameters."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param in method.parameters:
            # Skip self/cls
            if param.name in ['self', 'cls']:
                continue
            
            # Generate parameter schema
            param_schema = self._generate_parameter_schema(param)
            
            if param_schema:
                schema["properties"][param.name] = param_schema
                
                # Add to required if no default
                if param.is_required and param.name not in ['kwargs', 'args']:
                    schema["required"].append(param.name)
        
        # If no properties, allow additional properties for kwargs
        if not schema["properties"]:
            schema["additionalProperties"] = True
        
        return schema
    
    def _generate_parameter_schema(self, param: ParameterInfo) -> Dict[str, Any]:
        """Generate JSON Schema for a single parameter."""
        schema = {}
        
        # Handle kwargs specially
        if param.name == 'kwargs':
            return {
                "type": "object",
                "additionalProperties": True,
                "description": "Additional keyword arguments"
            }
        
        # Handle args specially
        if param.name == 'args':
            return {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional positional arguments"
            }
        
        # Map Python types to JSON Schema types
        type_mapping = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'list': 'array',
            'dict': 'object',
            'Any': 'string',  # Default to string for Any
            'None': 'null',
            'NoneType': 'null'
        }
        
        # Determine type from type hint
        if param.type_hint:
            type_str = str(param.type_hint).lower()
            
            # Check for Optional types
            if 'optional' in type_str or 'union' in type_str:
                # This is Optional, extract the actual type
                match = re.search(r'\[([^\[\]]+)\]', str(param.type_hint))
                if match:
                    inner_type = match.group(1).split(',')[0].strip()
                    for py_type, json_type in type_mapping.items():
                        if py_type.lower() in inner_type.lower():
                            schema["type"] = json_type
                            break
                else:
                    schema["type"] = "string"
            else:
                # Direct type mapping
                for py_type, json_type in type_mapping.items():
                    if py_type.lower() in type_str:
                        schema["type"] = json_type
                        break
        
        # Default to string if no type determined
        if "type" not in schema:
            # Try to infer type from default value
            if param.default_value is not None:
                # Handle actual boolean values
                if isinstance(param.default_value, bool):
                    schema["type"] = "boolean"
                # Handle string representations
                elif isinstance(param.default_value, str):
                    if param.default_value in ['True', 'False', 'true', 'false']:
                        schema["type"] = "boolean"
                    elif param.default_value.isdigit():
                        schema["type"] = "integer"
                    elif param.default_value.replace('.', '').isdigit():
                        schema["type"] = "number"
                    else:
                        schema["type"] = "string"
                # Handle actual numeric values
                elif isinstance(param.default_value, int):
                    schema["type"] = "integer"
                elif isinstance(param.default_value, float):
                    schema["type"] = "number"
                else:
                    schema["type"] = "string"
            else:
                schema["type"] = "string"
        
        # Add description if available
        if param.description:
            schema["description"] = param.description
        elif param.name in ['url', 'uri', 'endpoint']:
            schema["description"] = f"The {param.name} to use"
            schema["format"] = "uri"
        elif param.name in ['headers', 'params', 'data', 'json']:
            schema["type"] = "object"
            schema["additionalProperties"] = {"type": "string"}
            schema["description"] = f"The {param.name} to send"
        
        # Add default value if not None
        if param.default_value is not None and param.default_value != 'None':
            # Parse the default value to the correct type
            schema["default"] = self._parse_default_value(param.default_value, schema.get("type", "string"))
        
        return schema
    
    def _parse_default_value(self, default_value: Any, json_type: str) -> Any:
        """Parse a default value to the correct JSON type."""
        # If it's already the right type, return as-is
        if isinstance(default_value, (bool, int, float)) or default_value is None:
            return default_value
        
        # Only process strings
        if not isinstance(default_value, str):
            return str(default_value)
        
        default_str = default_value
        
        # Handle boolean defaults
        if json_type == "boolean":
            if default_str.lower() in ['true', '1']:
                return True
            elif default_str.lower() in ['false', '0']:
                return False
        
        # Handle integer defaults
        elif json_type == "integer":
            try:
                return int(default_str)
            except ValueError:
                pass
        
        # Handle number defaults
        elif json_type == "number":
            try:
                return float(default_str)
            except ValueError:
                pass
        
        # Handle None/null
        if default_str in ['None', 'null']:
            return None
        
        # Handle quoted strings
        if default_str.startswith(("'", '"')) and default_str.endswith(("'", '"')):
            return default_str[1:-1]
        
        # Return as-is for strings or if parsing fails
        return default_str
    
    def _generate_flags(self, method: MethodInfo) -> Dict[str, bool]:
        """Generate flags for the method (destructive, paginated, lro, etc.)."""
        flags = {}
        
        method_lower = method.name.lower()
        
        # Check for destructive operations
        if any(verb in method_lower for verb in ['create', 'update', 'delete', 'patch', 'remove', 'destroy', 'drop']):
            flags['destructive'] = True
            flags['confirm'] = True
        
        # Check for pagination
        if method.return_type:
            return_lower = str(method.return_type).lower()
            if any(term in return_lower for term in ['paged', 'iterator', 'iterable', 'generator']):
                flags['paginated'] = True
        
        # Check for long-running operations
        if method.return_type:
            return_lower = str(method.return_type).lower()
            if any(term in return_lower for term in ['poller', 'operation', 'future']):
                flags['lro'] = True
        
        # Check docstring for additional hints
        if method.docstring:
            doc_lower = method.docstring[:500].lower()
            if 'long-running' in doc_lower or 'polling' in doc_lower:
                flags['lro'] = True
            if 'paginated' in doc_lower or 'iterator' in doc_lower:
                flags['paginated'] = True
            if 'dangerous' in doc_lower or 'caution' in doc_lower:
                flags['dangerous'] = True
        
        # Check for async
        if method.is_async:
            flags['async'] = True
        
        return flags
    
    def export_to_json(self, tool_groups: List[MCPToolGroup], output_file: str):
        """Export tool groups to JSON for debugging/review."""
        output = {
            "sdk": self.sdk_name,
            "tool_groups": []
        }
        
        for group in tool_groups:
            group_data = {
                "name": group.name,
                "description": group.description,
                "tool_count": len(group.tools),
                "tools": []
            }
            
            for tool in group.tools[:10]:  # Sample first 10 tools
                tool_data = {
                    "name": tool.name,
                    "description": tool.description,
                    "sdk_method": tool.sdk_method,
                    "flags": tool.flags,
                    "input_schema": tool.input_schema
                }
                group_data["tools"].append(tool_data)
            
            output["tool_groups"].append(group_data)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output