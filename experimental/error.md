(venv) harsh108@HKLAPTOP-B8Q4PPKJ:~/projects/sdk2mcp$ python3 universal_mcp_server.py base64 base64 20
INFO:plugin_system:Loaded plugin: github
INFO:plugin_system:Loaded plugin: boto3
INFO:plugin_system:Loaded plugin: urllib_request
INFO:plugin_system:Loaded plugin: json
INFO:plugin_system:Loaded plugin: pathlib
INFO:plugin_system:Loaded plugin: kubernetes
INFO:plugin_system:Loaded plugin: base64
🚀 Initializing Universal MCP Server for base64
📦 Module: base64
🔍 Discovering SDK methods...
INFO:introspector_v2:Introspecting module: base64
INFO:introspector_v2:Discovered 22 methods
   Found 22 methods → 22 high-value
   Limiting to top 20 methods
🔧 Generating MCP tools...
Traceback (most recent call last):
  File "/home/harsh108/projects/sdk2mcp/universal_mcp_server.py", line 221, in <module>
    asyncio.run(main())
  File "/usr/lib/python3.10/asyncio/runners.py", line 44, in run
    return loop.run_until_complete(main)
  File "/usr/lib/python3.10/asyncio/base_events.py", line 649, in run_until_complete
    return future.result()
  File "/home/harsh108/projects/sdk2mcp/universal_mcp_server.py", line 215, in main
    await server.initialize(max_tools)
  File "/home/harsh108/projects/sdk2mcp/universal_mcp_server.py", line 155, in initialize
    self.tool_groups = generator.generate_tools(filtered_methods)
  File "/home/harsh108/projects/sdk2mcp/mcp_tool_generator.py", line 62, in generate_tools
    tool_group = self._generate_tool_group(owner, owner_methods)
  File "/home/harsh108/projects/sdk2mcp/mcp_tool_generator.py", line 136, in _generate_tool_group
    tool = self._generate_mcp_tool(method, owner)
  File "/home/harsh108/projects/sdk2mcp/mcp_tool_generator.py", line 160, in _generate_mcp_tool
    input_schema = self._generate_input_schema(method)
  File "/home/harsh108/projects/sdk2mcp/mcp_tool_generator.py", line 230, in _generate_input_schema
    param_schema = self._generate_parameter_schema(param)
  File "/home/harsh108/projects/sdk2mcp/mcp_tool_generator.py", line 307, in _generate_parameter_schema
    elif param.default_value.isdigit():
AttributeError: 'bool' object has no attribute 'isdigit'