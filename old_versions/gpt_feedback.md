You’re very close. The error you’re seeing is coming from the shape of the value you return to MCP Inspector from call_tool — not from your tool logic.

Symptom (from the screenshot):
“validation errors for CallToolResult → content.0.TextContent … input_value = ('meta', None)”

Inspector is trying to parse an item in content and finds a tuple like ('meta', None) instead of a content object ({"type":"text","text":"..."}).

That happens when the server serializes a content model into a list of key/value tuples (or mixes incompatible versions of mcp.types). The fastest, version-proof fix is to return plain dicts for content, not Pydantic model instances.

1) Fix your MCP return shape (exactly where & what)

File: universal_mcp_server.py
Where: inside UniversalMCPServer._setup_handlers → call_tool
What to change: stop constructing TextContent / CallToolResult objects; return a plain dict with content (and optional isError) in the MCP wire format.

Before (current):

from mcp.types import TextContent, Tool, CallToolResult
...
return CallToolResult(
    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
)


After (replace in all three return sites: not-found / success / except):

from mcp.types import Tool  # <- keep Tool for list_tools, drop TextContent/CallToolResult

# not found
return {
    "content": [
        {"type": "text", "text": json.dumps({"error": f"Tool '{name}' not found"})}
    ],
    "isError": True
}

# success
return {
    "content": [
        {"type": "text", "text": json.dumps(result, indent=2)}
    ]
}

# exception
return {
    "content": [
        {"type": "text", "text": json.dumps({"error": str(e), "tool": name})}
    ],
    "isError": True
}


Why: MCP Inspector validates the JSON envelope. Returning plain dicts avoids any mismatch between your mcp package version and the inspector’s Pydantic models (the tuple ('meta', None) is a tell that a model got serialized as .items() somewhere in that stack).

2) Make base64 tools Just Work (coerce text → bytes & serialize bytes)

Base64 methods require bytes-like inputs and produce bytes. Right now you’re passing a plain string ("Hello World"), which the SDK will reject even if the envelope were correct. Add small, generic coercions:

2a) Coerce inputs in the bridge

File: mcp_execution_bridge.py
Where: _prepare_arguments
Add right after you set prepared[param_name] = arguments[param_name]:

val = arguments[param_name]
ann = param.annotation

# bytes-like coercion (generic)
if (ann is bytes or str(ann) in {"<class 'bytes'>", "bytes"} or param_name in {"s","data","content","altchars"}):
    if isinstance(val, str):
        val = val.encode("utf-8")
    prepared[param_name] = val
    continue

# simple bool/int/float coercions from strings (handy for Inspector inputs)
if ann is bool and isinstance(val, str):
    prepared[param_name] = val.lower() in {"1","true","t","yes","y"}
    continue
if ann is int and isinstance(val, str) and val.isdigit():
    prepared[param_name] = int(val); continue
if ann is float and isinstance(val, str):
    try: prepared[param_name] = float(val); continue
    except: pass

prepared[param_name] = val

2b) Serialize bytes results to text

File: mcp_execution_bridge.py
Where: _serialize_result (top of the function)
Add:

from base64 import b64encode

# bytes → emit ascii (or b64 if not decodable)
if isinstance(result, (bytes, bytearray, memoryview)):
    try:
        return bytes(result).decode("utf-8")
    except UnicodeDecodeError:
        return {"base64": b64encode(bytes(result)).decode("ascii")}


Why: lets you type “Hello World” in Inspector and get a readable result (either the decoded text or a base64 string), instead of failing on bytes.

3) Be strict about JSON-serializable results (already mostly there)

You already convert unknown objects to strings. Keep that; it prevents inspector crashes when a tool returns SDK objects.

If you want cleaner output for common containers, add just under your dict/iterable handling:

# tuples/sets → lists
if isinstance(result, (tuple, set)):
    return [self._serialize_result(x) for x in result]

4) Quick sanity checklist after the patch

Restart Inspector and your server.

In Tools, run base64_b64encode with:

s: Hello World

leave altchars blank

Expected response (no validation error):

{
  "status": "success",
  "tool": "base64_b64encode",
  "result": "SGVsbG8gV29ybGQ="
}


(or wrapped inside your outer object depending on your bridge — either is fine as long as content[0].text contains JSON)

Try a failure path (e.g., wrong arg name) and confirm you get:

{"error": "...", "tool": "base64_b64encode"}


with isError: true.

5) (Optional) Guardrail for destructive tools in the envelope

When you later enable Azure/K8s deletes/creates, include a confirmation guard in the bridge before invoking:

if tool_metadata.flags.get("destructive") and not arguments.get("confirm", False):
    return {
        "content": [{"type": "text", "text": json.dumps({"error":"Destructive call requires confirm=true"})}],
        "isError": True
    }

Why these fixes solve your specific error

The tuple ('meta', None) inside content indicates the inspector is receiving a malformed content item. Returning plain JSON dicts ({"type":"text", "text":"..."}) removes any ambiguity about class versions/serialization.

Base64 methods need bytes. Coercing input strings → bytes and serializing bytes → UTF-8 or base64 prevents runtime type crashes once the envelope is valid.