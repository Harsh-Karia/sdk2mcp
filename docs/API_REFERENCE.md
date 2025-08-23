# 📚 API Reference

## Core Components

### UniversalIntrospector

The main introspection engine that discovers methods from any Python SDK.

```python
from introspector_v2 import UniversalIntrospector

# Initialize with optional SDK name for plugin support
introspector = UniversalIntrospector('github')

# Discover methods from any module
methods = introspector.discover_from_module('github')

# Filter to high-value methods
filtered = introspector.filter_high_value_methods(methods)
```

**Key Methods:**
- `discover_from_module(module_name: str)` - Discovers all methods from a module
- `filter_high_value_methods(methods: List[MethodInfo])` - Filters to important methods

### UniversalPatternRecognizer

Analyzes SDK patterns to identify resources, CRUD operations, and authentication flows.

```python
from pattern_recognizer import UniversalPatternRecognizer

recognizer = UniversalPatternRecognizer()
patterns = recognizer.analyze_patterns(methods)

# Access discovered patterns
resources = patterns.resources
crud_ops = patterns.crud_operations
auth_flows = patterns.auth_flows
```

### UniversalMCPToolGenerator

Generates MCP tools from discovered methods.

```python
from mcp_tool_generator import UniversalMCPToolGenerator

generator = UniversalMCPToolGenerator('sdk_name')
tool_groups = generator.generate_tools(methods)

# Each tool group contains related MCP tools
for group in tool_groups:
    print(f"Group: {group.owner}")
    for tool in group.tools:
        print(f"  - {tool.name}: {tool.description}")
```

### MCPExecutionBridge

Dynamically executes SDK methods through the MCP protocol.

```python
from mcp_execution_bridge import MCPExecutionBridge

bridge = MCPExecutionBridge('sdk_name', 'module_name')

# Execute any SDK method
result = await bridge.execute_tool(
    tool_name='sdk_method_name',
    sdk_method='module.class.method',
    arguments={'param1': 'value1'}
)
```

### Plugin System

Optional configuration system for SDK-specific optimizations.

```python
from plugin_system import get_plugin_manager

pm = get_plugin_manager()

# Check if plugin exists
plugin = pm.get_plugin('github')

# Get authentication info
auth_info = pm.get_auth_info('github')

# Get optimization hints
hints = pm.get_hints('github')
```

## Data Models

### MethodInfo

Represents a discovered method with metadata.

```python
@dataclass
class MethodInfo:
    name: str
    full_name: str
    module_path: str
    parameters: List[ParameterInfo]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    parent_class: Optional[str] = None
    priority_score: float = 0.0
```

### MCPTool

Represents a generated MCP tool.

```python
@dataclass
class MCPTool:
    name: str
    description: str
    sdk_method: str
    input_schema: Dict[str, Any]
    flags: Dict[str, bool]
```

## Configuration

### SDK Hints (sdk_hints.yaml)

Optional configuration for SDK-specific optimizations:

```yaml
sdks:
  github:
    root_prefixes: ["github."]
    important_class_patterns: ["Client$", "Api$"]
    boost_method_patterns: ["^(get|list|create)_"]
    penalize_method_patterns: ["^_"]
```

### Plugin Configuration (plugins/*.yaml)

Advanced plugin-based configuration:

```yaml
name: github
sdk_module: github
auth:
  type: token
  env_vars: [GITHUB_TOKEN]
client:
  class_path: github.Github
  init_params:
    auth: ${auth.value}
hints:
  prioritize_methods: [get_user, get_repo]
```

## Environment Variables

- `OPENAI_API_KEY` - Required for LLM auto-configuration (Phase 6)
- `GITHUB_TOKEN` - Optional, for GitHub SDK authentication
- `AWS_ACCESS_KEY_ID` - Optional, for AWS SDK authentication

## Error Handling

All components include comprehensive error handling:

```python
try:
    methods = introspector.discover_from_module('nonexistent')
except ImportError:
    print("Module not found")

try:
    result = await bridge.execute_tool(...)
except Exception as e:
    print(f"Execution failed: {e}")
```