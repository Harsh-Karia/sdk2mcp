# SDK2MCP Project Context

## Assignment Overview
**Goal**: Build a Python SDK-to-MCP converter that automatically exposes Python SDK methods as MCP (Model Context Protocol) tools.

**Key Requirements**:
- Must be **truly generalized** - work with ANY Python SDK, not just the test cases
- Test with GitHub, Kubernetes, and Azure SDKs
- Use deterministic introspection first, LLM as fallback only
- Cover as many SDK methods as possible (potentially thousands)
- Test with MCP Inspector
- 3-5 hour timeframe (24 hours total from API key receipt)

**Clarifications from Tahsin**:
1. Not completely LLM-driven - use deterministic approaches where possible
2. Aim to cover as many methods as possible
3. MCP Inspector for testing
4. Capture as much Azure functionality as realistically possible

## Critical Architecture Decision
The system must be **SDK-agnostic**:
- Core knows nothing about specific SDKs
- Uses pattern recognition and introspection
- New SDKs work without code changes
- Configuration over code

**Success Test**: Should be able to `pip install any-random-sdk` and the converter should automatically work with it.

## Development Phases

### PHASE 1: Basic MCP Server Setup ✅ CURRENT
- [ ] Set up project structure and dependencies
- [ ] Create minimal MCP server with one hardcoded tool
- [ ] Test with MCP Inspector
- [ ] Document setup and testing process

### PHASE 2: Universal SDK Introspection Engine
- Build generic Python introspection system
- Auto-detect SDK patterns (client classes, service modules)
- Extract methods from ANY Python SDK

### PHASE 3: SDK Pattern Recognition System
- Identify common patterns (Client, Resource, Service)
- Create SDK fingerprinting system

### PHASE 4: Universal MCP Tool Generator
- Convert any Python method to MCP tool
- Handle all Python type hints → MCP schemas

### PHASE 5: Plugin-Based SDK Configuration
- Create plugin system for SDK-specific hints
- Test with GitHub, Kubernetes, Azure as config-only plugins

### PHASE 6: Smart Auto-Configuration with LLM
- Auto-detect authentication patterns
- LLM-based method categorization

### PHASE 7: Production-Ready System
- Performance optimization
- Test with 10+ different SDKs

## Current Status
**Phase 1 COMPLETE ✅** - Basic MCP server with test tool is working and tested with MCP Inspector!

## Phase 1 Achievements
- ✅ Virtual environment set up in WSL
- ✅ MCP package installed (v1.13.1)
- ✅ Created `server.py` with stdio transport
- ✅ Implemented `list_sdk_methods` test tool with parameters
- ✅ Successfully tested with MCP Inspector
- ✅ Comprehensive documentation in README

## Next Immediate Steps (Phase 2)
1. Build generic Python introspection system
2. Auto-detect SDK patterns (client classes, service modules)
3. Extract methods, parameters, types from ANY Python SDK
4. Test with multiple SDK structures

## Project Structure (Phase 1)
```
sdk2mcp/
├── server.py           # Main MCP server
├── requirements.txt    # Dependencies
├── README.md          # Setup instructions
└── test_connection.py  # Quick test script
```

## Testing Approach
- Each phase produces working deliverable
- Test with MCP Inspector at each phase
- Document everything for reproducibility

## OpenAI API Key
Use the key provided in email for LLM functionality (Phase 6)

## Environment
- Using WSL (Windows Subsystem for Linux) for development
- Python 3.9+ required
- MCP Inspector for testing
