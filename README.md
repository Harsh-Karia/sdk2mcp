# SDK2MCP - Universal Python SDK to MCP Converter

A generalized system that automatically converts any Python SDK into MCP (Model Context Protocol) tools, enabling LLMs to interact with any service that has a Python SDK.

## 🎯 Project Goal

Build a truly generalized Python SDK-to-MCP converter that can automatically expose methods from ANY Python SDK as MCP tools - not just specific SDKs, but any SDK without writing custom code.

## 📋 Current Status: Phase 1 Complete ✅

The foundation MCP server is working and tested with MCP Inspector!

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- MCP Inspector (for testing)

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd sdk2mcp
```

2. Set up virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

1. Start the MCP server:
```bash
python3 server.py
# Or use the helper script:
./run_server.sh
```

2. In another terminal, start MCP Inspector:
```bash
mcp-inspector
```

3. In MCP Inspector:
   - Click "Connect"
   - The server uses stdio transport by default
   - You should see the connection established

### Testing the Server

Once connected in MCP Inspector:

1. Click "List Tools" - you should see `list_sdk_methods`
2. Click on the tool to test it
3. Try these example inputs:
   - Without parameters: Returns "SDK 'unknown' not found"
   - `sdk_name: "github"`: Lists all GitHub categories and methods
   - `sdk_name: "github", category: "issues"`: Lists only issue-related methods

## 🏗️ Project Structure

```
sdk2mcp/
├── server.py           # Main MCP server with stdio transport
├── test_connection.py  # Quick test script for server components
├── run_server.sh       # Helper script to start the server
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## 📊 Development Phases

### ✅ Phase 1: Basic MCP Server Setup (COMPLETE)
- [x] Set up project structure and dependencies
- [x] Create minimal MCP server with one hardcoded tool
- [x] Test with MCP Inspector
- [x] Document setup and testing process

### ⏳ Phase 2: Universal SDK Introspection Engine (NEXT)
- [ ] Build generic Python introspection system
- [ ] Auto-detect SDK patterns (client classes, service modules)
- [ ] Extract methods, parameters, types from ANY Python SDK
- [ ] Test with multiple SDK structures

### 📅 Phase 3: SDK Pattern Recognition System
- [ ] Identify common SDK patterns (Client, Resource, Service)
- [ ] Build pattern matchers for different SDK styles
- [ ] Create SDK fingerprinting system
- [ ] Test pattern detection on 5+ different SDKs

### 📅 Phase 4: Universal MCP Tool Generator
- [ ] Convert any Python method to MCP tool
- [ ] Handle all Python type hints → MCP schemas
- [ ] Generate tools without SDK-specific code
- [ ] Validate with unknown SDK (e.g., Stripe, Twilio)

### 📅 Phase 5: Plugin-Based SDK Configuration
- [ ] Create plugin system for SDK-specific hints
- [ ] Build config schema for SDK registration
- [ ] Implement GitHub, Kubernetes, Azure as plugins
- [ ] Test adding new SDK with just config

### 📅 Phase 6: Smart Auto-Configuration with LLM
- [ ] Auto-detect authentication patterns
- [ ] LLM-based method categorization
- [ ] Intelligent method filtering
- [ ] Test with completely unknown SDK

### 📅 Phase 7: Production-Ready System
- [ ] Performance optimization for large SDKs
- [ ] Comprehensive error handling
- [ ] CLI for easy SDK registration
- [ ] Test with 10+ different SDKs

## 🎯 Key Architecture Principles

### SDK-Agnostic Core
The core system will never have SDK-specific code. Instead of:
```python
if sdk_name == "github":  # ❌ Bad
```

It discovers patterns:
```python
if hasattr(obj, '__call__') and not name.startswith('_'):  # ✅ Good
```

### Pattern-Based Discovery
Recognizes common SDK patterns automatically:
- **Client pattern**: `SDKClient().service.method()`
- **Resource pattern**: `Resource.list(), Resource.get(id)`
- **Builder pattern**: `SDK().with_auth().build().execute()`
- **Module pattern**: `sdk.module.function()`

### Zero-Code SDK Addition
When complete, adding new SDKs will require only configuration:
```yaml
sdks:
  - name: firebase
    package: firebase_admin
    entry_point: firebase_admin.initialize_app
    auth_pattern: "credentials"
    discover_from: ["firestore", "auth", "storage"]
```

## 🧪 Testing

### Component Testing
Run the test script to verify server components:
```bash
python test_connection.py
```

### MCP Inspector Testing
1. Start the server: `python3 server.py`
2. Start MCP Inspector: `mcp-inspector`
3. Connect and test the `list_sdk_methods` tool

### Expected Results
- Tool accepts `sdk_name` parameter (required)
- Tool accepts `category` parameter (optional)
- Returns mock data for github, kubernetes, azure SDKs
- Proper error handling for unknown SDKs

## 📈 Phase 1 Success Criteria ✅

- [x] Server starts without errors
- [x] MCP Inspector connects successfully
- [x] Tool appears in Inspector's tool list
- [x] Tool can be called with parameters
- [x] Tool returns expected response
- [x] README has clear reproduction steps

## 🔄 Next Steps

Phase 2 will implement the Universal SDK Introspection Engine to replace mock data with real SDK discovery.

## 📝 Technical Notes

- **Transport**: stdio (compatible with MCP Inspector)
- **Python Version**: 3.9+
- **MCP Package**: 1.13.1
- **Architecture**: Async/await pattern for all tool handlers

## 🤝 Contributing

This is a take-home assessment project. The goal is to create a truly generalized system that works with ANY Python SDK without modification.