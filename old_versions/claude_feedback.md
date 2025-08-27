Looking at your error message, the issue is a validation error for the CallToolResult. The error states:
"9 validation errors for CallToolResult"
content.0.TextContent
  Input should be a valid dictionary or instance of TextContent

The problem is in your mcp_execution_bridge.py file. When returning results from tool execution, you're trying to create a CallToolResult with a TextContent object, but the MCP library expects a specific format.
Here's the fix for your universal_mcp_server.py file in the call_tool handler:
 # Format the result - return list of content items directly
                formatted_result = [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
                
                logger.info(f"🔍 CallToolResult created successfully")
                return formatted_result

Also update the error return case:
  # Format the result - return list of content items directly
                formatted_result = [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
                
                logger.info(f"🔍 CallToolResult created successfully")
                return formatted_result


And the exception case:
  # Format the result - return list of content items directly
                formatted_result = [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
                
                logger.info(f"🔍 CallToolResult created successfully")
                return formatted_result


Also remove the import for CallToolResult and TextContent since we're no longer using them:
# Format the result - return list of content items directly
                formatted_result = [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
                
                logger.info(f"🔍 CallToolResult created successfully")
                return formatted_result

The key issue is that the MCP library expects the call_tool handler to return a list of content items (as plain dictionaries) rather than a CallToolResult object. The library handles wrapping this into the proper response format internally.
Summary
The validation error occurs because:

The MCP library's internal handling expects the tool handler to return a list of content dictionaries
Your code was trying to return a CallToolResult object with TextContent inside
The library couldn't validate this structure

The fix changes the return format to:

Return a list containing a dictionary with type and text fields
Remove the CallToolResult and TextContent wrapper objects
Let the MCP library handle the final response formatting

After making these changes, restart your server and the tool execution should work properly in MCP Inspector.