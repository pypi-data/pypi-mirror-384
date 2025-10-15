"""
MCP Tool Registration System for ToolUniverse

This module provides functionality to register local tools as MCP tools and enables
automatic loading of these tools on remote servers via ToolUniverse integration.

Usage:
======

Server Side (Tool Provider):
```python
from tooluniverse.mcp_tool_registry import register_mcp_tool, start_mcp_server

@register_mcp_tool(
    tool_type_name="my_analysis_tool",
    config={
        "description": "Performs custom data analysis"
    },
    mcp_config={
        "server_name": "Custom Analysis Server",
        "host": "0.0.0.0",
        "port": 8001
    }
)
class MyAnalysisTool:
    def run(self, arguments):
        return {"result": "analysis complete"}

# Start MCP server with registered tools
start_mcp_server()
```

Client Side (Tool Consumer):
```python
from tooluniverse import ToolUniverse

# Auto-discover and load MCP tools from remote servers
tu = ToolUniverse()
tu.load_mcp_tools(server_urls=["http://localhost:8001"])

# Use the remote tool
result = tu.run_tool("my_analysis_tool", {"data": "input"})
```
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import threading


# Import SMCP and ToolUniverse dynamically to avoid circular imports
def _get_smcp():
    """Get SMCP class with delayed import to avoid circular import"""
    from tooluniverse import SMCP

    return SMCP


def _get_tooluniverse():
    """Get ToolUniverse class with delayed import to avoid circular import"""
    from tooluniverse import ToolUniverse

    return ToolUniverse


# Global MCP tool registry
_mcp_tool_registry: Dict[str, Any] = {}
_mcp_server_configs: Dict[int, Dict[str, Any]] = {}
_mcp_server_instances: Dict[int, Any] = {}


def register_mcp_tool(tool_type_name=None, config=None, mcp_config=None):
    """
    Decorator to register a tool class exactly like register_tool, but also expose it as an MCP server.

    This decorator does everything that register_tool does, PLUS exposes the tool via SMCP protocol
    for remote access. The parameters and behavior are identical to register_tool, with an optional
    mcp_config parameter for server configuration.

    Parameters:
    ===========
    tool_type_name : str, optional
        Custom name for the tool type. Same as register_tool.

    config : dict, optional
        Tool configuration dictionary. Same as register_tool.

    mcp_config : dict, optional
        Additional MCP server configuration. Can include:
        - server_name: Name of the MCP server
        - host: Server host (default: "localhost")
        - port: Server port (default: 8000)
        - transport: "http" or "stdio" (default: "http")
        - auto_start: Whether to auto-start server when tool is registered

    Returns:
    ========
    function
        Decorator function that registers the tool class both locally and as MCP server.

    Examples:
    =========

    Same as register_tool, just with MCP exposure:
    ```python
    @register_mcp_tool('CustomToolName', config={...}, mcp_config={"port": 8001})
    class MyTool:
        pass

    @register_mcp_tool()  # Uses class name, default MCP config
    class AnotherTool:
        pass
    ```
    """

    def decorator(cls):
        # First, do exactly what register_tool does
        from .tool_registry import register_tool

        # Apply register_tool decorator to register locally
        registered_cls = register_tool(tool_type_name, config)(cls)

        # Now, additionally register for MCP exposure
        tool_name = tool_type_name or cls.__name__
        tool_config = config or {}
        tool_description = (
            tool_config.get("description")
            or (cls.__doc__ or f"Tool: {tool_name}").strip()
        )

        # Create default parameter schema if not provided
        tool_schema = tool_config.get("parameter_schema") or {
            "type": "object",
            "properties": {
                "arguments": {"type": "object", "description": "Tool arguments"}
            },
        }

        # Default MCP server configuration
        default_mcp_config = {
            "server_name": f"MCP Server for {tool_name}",
            "host": "localhost",
            "port": 8000,
            "transport": "http",
            "auto_start": False,
            "max_workers": 5,
        }

        # Merge with provided mcp_config
        server_config = {**default_mcp_config, **(mcp_config or {})}

        # Register for MCP exposure
        tool_info = {
            "name": tool_name,
            "class": cls,
            "description": tool_description,
            "parameter_schema": tool_schema,
            "server_config": server_config,
            "tool_config": tool_config,
        }

        _mcp_tool_registry[tool_name] = tool_info

        # Register server config by port to group tools on same server
        port = server_config["port"]
        if port not in _mcp_server_configs:
            _mcp_server_configs[port] = {"config": server_config, "tools": []}
        _mcp_server_configs[port]["tools"].append(tool_info)

        print(f"✅ Registered MCP tool: {tool_name} (server port: {port})")

        # Auto-start server if requested
        auto_start = server_config.get("auto_start", False)
        if auto_start:
            start_mcp_server_for_tool(tool_name)

        return registered_cls

    return decorator


def register_mcp_tool_from_config(tool_class: type, config: Dict[str, Any]):
    """
    Register an existing tool class as MCP tool using configuration.

    This function provides a programmatic way to register tools as MCP tools
    without using decorators, useful for dynamic tool registration.
    Just like register_mcp_tool decorator, this does everything register_tool would do
    PLUS exposes the tool via MCP.

    Parameters:
    ===========
    tool_class : type
        The tool class to register
    config : dict
        Configuration containing:
        - name: Tool name (required)
        - description: Tool description
        - parameter_schema: JSON schema for parameters
        - mcp_config: MCP server configuration

    Examples:
    =========
    ```python
    class ExistingTool:
        def run(self, arguments):
            return {"status": "processed"}

    register_mcp_tool_from_config(ExistingTool, {
        "name": "existing_tool",
        "description": "An existing tool exposed via MCP",
        "mcp_config": {"port": 8002}
    })
    ```
    """
    name = config.get("name") or tool_class.__name__
    tool_config = {k: v for k, v in config.items() if k != "mcp_config"}
    mcp_config = config.get("mcp_config", {})

    # Use the decorator to register both locally and for MCP
    register_mcp_tool(tool_type_name=name, config=tool_config, mcp_config=mcp_config)(
        tool_class
    )


def get_mcp_tool_registry() -> Dict[str, Any]:
    """Get the current MCP tool registry."""
    return _mcp_tool_registry.copy()


def get_registered_tools() -> List[Dict[str, Any]]:
    """
    Get a list of all registered MCP tools with their information.

    Returns:
        List of dictionaries containing tool information including name, description, and port.
    """
    tools = []
    for tool_name, tool_info in _mcp_tool_registry.items():
        tools.append(
            {
                "name": tool_name,
                "description": tool_info["description"],
                "port": tool_info["server_config"]["port"],
                "class": tool_info["class"].__name__,
            }
        )
    return tools


def get_mcp_server_configs() -> Dict[int, Dict[str, Any]]:
    """Get the current MCP server configurations grouped by port."""
    return _mcp_server_configs.copy()


def start_mcp_server(port: Optional[int] = None, **kwargs):
    """
    Start MCP server(s) for registered tools.

    Parameters:
    ===========
    port : int, optional
        Specific port to start server for. If None, starts servers for all registered tools.
    **kwargs
        Additional arguments passed to SMCP server

    Examples:
    =========
    ```python
    # Start server for specific port
    start_mcp_server(port=8001)

    # Start all servers
    start_mcp_server()

    # Start with custom configuration
    start_mcp_server(max_workers=20, debug=True)
    ```
    """
    import time

    try:
        pass
    except ImportError:
        print("❌ SMCP not available. Cannot start MCP server.")
        return

    if port is not None:
        # Start server for specific port
        if port in _mcp_server_configs:
            _start_server_for_port(port, **kwargs)
        else:
            print(f"❌ No tools registered for port {port}")
    else:
        # Start servers for all registered ports
        for port in _mcp_server_configs:
            _start_server_for_port(port, **kwargs)

    # Keep main thread alive
    print("🎯 MCP server(s) started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MCP server(s)...")
        # Cleanup server instances
        for port, _server in _mcp_server_instances.items():
            try:
                print(f"🧹 Stopping server on port {port}...")
                # Note: FastMCP cleanup is handled automatically
            except Exception as e:
                print(f"⚠️  Error stopping server on port {port}: {e}")
        _mcp_server_instances.clear()
        print("✅ All servers stopped.")


def _start_server_for_port(port: int, **kwargs):
    """Start SMCP server for tools on a specific port."""
    if port in _mcp_server_instances:
        print(f"🔄 MCP server already running on port {port}")
        return

    server_info = _mcp_server_configs[port]
    config = server_info["config"]
    tools = server_info["tools"]

    print(f"🚀 Starting MCP server on port {port} with {len(tools)} tools...")

    # Create SMCP server for compatibility
    server = _get_smcp()(
        name=config["server_name"],
        auto_expose_tools=False,  # We'll add tools manually
        search_enabled=True,
        max_workers=config.get("max_workers", 5),
        **kwargs,
    )

    # Add registered tools to the server
    for tool_info in tools:
        _add_tool_to_smcp_server(server, tool_info)

    # Store server instance
    _mcp_server_instances[port] = server

    # Start server in background thread
    def run_server():
        try:
            # Enable stateless mode for MCPAutoLoaderTool compatibility
            server.run_simple(
                transport=config["transport"],
                host=config["host"],
                port=port,
                stateless_http=True,
            )
        except Exception as e:
            print(f"❌ Error running MCP server on port {port}: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print(f"✅ MCP server started on {config['host']}:{port}")


def _add_tool_to_smcp_server(server, tool_info: Dict[str, Any]):
    """Add a registered tool to an SMCP server instance by reusing SMCP's proven method."""
    name = tool_info["name"]
    tool_class = tool_info["class"]
    description = tool_info["description"]
    schema = tool_info["parameter_schema"]

    print(
        f"🔧 Adding tool '{name}' using SMCP's _create_mcp_tool_from_tooluniverse approach..."
    )

    # Create tool instance for execution
    tool_instance = tool_class()

    # Convert our tool_info to the format expected by SMCP's method
    # SMCP expects tool_config with 'name', 'description', and 'parameter' fields
    tool_config = {
        "name": name,
        "description": description,
        "parameter": schema,  # SMCP expects 'parameter' not 'parameter_schema'
    }

    # Check if the server has the SMCP method available
    if hasattr(server, "_create_mcp_tool_from_tooluniverse"):
        print("✅ Using server's _create_mcp_tool_from_tooluniverse method")
        # Temporarily store our tool instance so SMCP's method can access it
        # We need to modify SMCP's approach to use our tool_instance instead of tooluniverse
        server._temp_tool_instance = tool_instance

        # Create a modified version of SMCP's approach
        _create_mcp_tool_from_tooluniverse_with_instance(
            server, tool_config, tool_instance
        )
    else:
        print(
            "⚠️ Server doesn't have _create_mcp_tool_from_tooluniverse, using fallback"
        )
        # Fallback to standard method
        server.add_custom_tool(
            name=name,
            function=lambda arguments="{}": tool_instance.run(json.loads(arguments)),
            description=description,
        )


def _create_mcp_tool_from_tooluniverse_with_instance(
    server, tool_config: Dict[str, Any], tool_instance
):
    """
    Create an MCP tool from a ToolUniverse tool configuration using a tool instance.

    This method reuses the proven approach from SMCP's _create_mcp_tool_from_tooluniverse
    method, but adapts it to work with tool instances instead of ToolUniverse.
    It creates functions with proper parameter signatures that match the ToolUniverse
    tool schema, enabling FastMCP's automatic parameter validation.
    """
    try:
        # Debug: Ensure tool_config is a dictionary
        if not isinstance(tool_config, dict):
            raise ValueError(
                f"tool_config must be a dictionary, got {type(tool_config)}: {tool_config}"
            )

        tool_name = tool_config["name"]
        description = tool_config.get("description", f"Tool: {tool_name}")
        parameters = tool_config.get("parameter", {})

        # Extract parameter information from the schema
        # Handle case where properties might be None (like in Finish tool)
        properties = parameters.get("properties")
        if properties is None:
            properties = {}
        required_params = parameters.get("required", [])

        # Handle non-standard schema format where 'required' is set on individual properties
        # instead of at the object level (common in ToolUniverse schemas)
        if not required_params and properties:
            required_params = [
                param_name
                for param_name, param_info in properties.items()
                if param_info.get("required", False)
            ]

        # Build function signature dynamically with Pydantic Field support
        import inspect
        from typing import Union

        try:
            from typing import Annotated
            from pydantic import Field

            PYDANTIC_AVAILABLE = True
        except ImportError:
            PYDANTIC_AVAILABLE = False

        # Create parameter signature for the function
        func_params = []
        param_annotations = {}

        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_description = param_info.get("description", f"{param_name} parameter")
            is_required = param_name in required_params

            # Map JSON schema types to Python types
            python_type: type
            if param_type == "string":
                python_type = str
            elif param_type == "integer":
                python_type = int
            elif param_type == "number":
                python_type = float
            elif param_type == "boolean":
                python_type = bool
            elif param_type == "array":
                python_type = list
            elif param_type == "object":
                python_type = dict
            else:
                python_type = str  # Default to string for unknown types

            # Create proper type annotation
            if PYDANTIC_AVAILABLE:
                # Use Pydantic Field for enhanced schema information
                field_kwargs = {"description": param_description}
                pydantic_field = Field(**field_kwargs)

                if is_required:
                    annotated_type: Any = Annotated[python_type, pydantic_field]
                    param_annotations[param_name] = annotated_type
                    func_params.append(
                        inspect.Parameter(
                            param_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=annotated_type,
                        )
                    )
                else:
                    optional_annotated_type: Any = Annotated[
                        Union[python_type, type(None)], pydantic_field
                    ]
                    param_annotations[param_name] = optional_annotated_type
                    func_params.append(
                        inspect.Parameter(
                            param_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            default=None,
                            annotation=optional_annotated_type,
                        )
                    )
            else:
                # Fallback without Pydantic
                if is_required:
                    param_annotations[param_name] = python_type
                    func_params.append(
                        inspect.Parameter(
                            param_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=python_type,
                        )
                    )
                else:
                    param_annotations[param_name] = Union[python_type, type(None)]
                    func_params.append(
                        inspect.Parameter(
                            param_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            default=None,
                            annotation=Union[python_type, type(None)],
                        )
                    )

        # Create the async function with dynamic signature
        if not properties:
            # Tool has no parameters - create simple function
            async def dynamic_tool_function() -> str:
                """Execute tool with no arguments."""
                try:
                    # Execute our custom tool instance
                    result = tool_instance.run({})

                    # Format the result
                    if isinstance(result, str):
                        return result
                    else:
                        return json.dumps(result, indent=2, default=str)

                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    print(f"❌ {error_msg}")
                    return json.dumps({"error": error_msg}, indent=2)

            # Set function metadata
            dynamic_tool_function.__name__ = tool_name
            dynamic_tool_function.__signature__ = inspect.Signature([])
            dynamic_tool_function.__annotations__ = {"return": str}

        else:
            # Tool has parameters - create function with dynamic signature
            async def dynamic_tool_function(**kwargs) -> str:
                """Execute tool with provided arguments."""
                try:
                    # Filter out None values for optional parameters
                    args_dict = {k: v for k, v in kwargs.items() if v is not None}

                    # Validate required parameters
                    missing_required = [
                        param for param in required_params if param not in args_dict
                    ]
                    if missing_required:
                        return json.dumps(
                            {
                                "error": f"Missing required parameters: {missing_required}",
                                "required": required_params,
                                "provided": list(args_dict.keys()),
                            },
                            indent=2,
                        )

                    # Execute our custom tool instance instead of tooluniverse
                    result = tool_instance.run(args_dict)

                    # Format the result
                    if isinstance(result, str):
                        return result
                    else:
                        return json.dumps(result, indent=2, default=str)

                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    print(f"❌ {error_msg}")
                    return json.dumps({"error": error_msg}, indent=2)

            # Set function metadata
            dynamic_tool_function.__name__ = tool_name

            # Set function signature dynamically for tools with parameters
            if func_params:
                dynamic_tool_function.__signature__ = inspect.Signature(func_params)

            # Set annotations for type hints
            dynamic_tool_function.__annotations__ = param_annotations.copy()
            dynamic_tool_function.__annotations__["return"] = str

        # Create detailed docstring
        param_docs = []
        for param_name, param_info in properties.items():
            param_desc = param_info.get("description", f"{param_name} parameter")
            param_type = param_info.get("type", "string")
            is_required = param_name in required_params
            required_text = "required" if is_required else "optional"
            param_docs.append(
                f"    {param_name} ({param_type}, {required_text}): {param_desc}"
            )

        # Set function docstring
        dynamic_tool_function.__doc__ = f"""{description}

Parameters:
{chr(10).join(param_docs) if param_docs else '    No parameters required'}

Returns:
    str: Tool execution result
"""

        print(f"✅ Created function with {len(func_params)} parameters")
        print("📋 Docstring includes parameter descriptions:")
        for i, doc in enumerate(param_docs[:3], 1):  # Show first 3 for brevity
            print(f"   {i}. {doc.strip()}")
        if len(param_docs) > 3:
            print(f"   ... and {len(param_docs) - 3} more")

        # Register with FastMCP using the tool decorator approach (following SMCP pattern)
        server.tool(description=description)(dynamic_tool_function)

        print(
            f"📦 Tool '{tool_name}' registered successfully with parameter descriptions"
        )

    except Exception as e:
        print(f"❌ Error creating tool from config: {e}")
        import traceback

        traceback.print_exc()
        # Don't raise - continue with other tools
        return


def _build_fastmcp_tool_function(
    name: str, description: str, schema: Dict[str, Any], tool_instance
):
    """
    Build a FastMCP-compatible function with proper docstring and type annotations.

    FastMCP generates parameter schema from the function signature and docstring,
    so we need to create a function that matches the expected format exactly.
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Build parameter definitions and documentation
    param_definitions = []
    param_names = []
    docstring_params = []

    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "string")
        param_description = param_info.get("description", f"{param_name} parameter")
        has_default = param_name not in required
        default_value = param_info.get("default", None)
        enum_values = param_info.get("enum", None)

        # Map JSON schema types to Python types
        if param_type == "string":
            py_type = "str"
            if has_default and default_value is None:
                default_value = '""'
            elif has_default:
                default_value = f'"{default_value}"'
        elif param_type == "integer":
            py_type = "int"
            if has_default and default_value is None:
                default_value = "0"
            elif has_default:
                default_value = str(default_value)
        elif param_type == "number":
            py_type = "float"
            if has_default and default_value is None:
                default_value = "0.0"
            elif has_default:
                default_value = str(default_value)
        elif param_type == "boolean":
            py_type = "bool"
            if has_default and default_value is None:
                default_value = "False"
            elif has_default:
                default_value = str(default_value)
        else:
            py_type = "str"  # Default to string
            if has_default and default_value is None:
                default_value = '""'
            elif has_default:
                default_value = f'"{default_value}"'

        # Build parameter definition for function signature
        if has_default:
            param_def = f"{param_name}: {py_type} = {default_value}"
        else:
            param_def = f"{param_name}: {py_type}"

        param_definitions.append(param_def)
        param_names.append(param_name)

        # Build docstring parameter documentation
        param_doc = f"        {param_name} ({py_type}): {param_description}"
        if enum_values:
            param_doc += f". Options: {enum_values}"
        if has_default and default_value is not None:
            param_doc += f". Default: {default_value}"

        docstring_params.append(param_doc)

    # Create function signature
    params_str = ", ".join(param_definitions)

    # Create comprehensive docstring following Google style
    # This is critical for FastMCP to extract parameter information
    docstring_parts = [
        f'    """{description}',
        "",
        "    This tool provides expert consultation functionality.",
        "",
    ]

    if docstring_params:
        docstring_parts.extend(["    Args:", *docstring_params, ""])

    docstring_parts.extend(
        [
            "    Returns:",
            "        dict: Tool execution result with status and response data",
            '    """',
        ]
    )

    docstring = "\n".join(docstring_parts)

    # Create the function code with comprehensive docstring
    func_code = f"""
def fastmcp_tool_function({params_str}) -> dict:
{docstring}
    # Collect all parameters into arguments dict for tool execution
    arguments = {{}}
{chr(10).join(f'    arguments["{pname}"] = {pname}' for pname in param_names)}

    # Execute the original tool
    try:
        result = tool_instance.run(arguments)
        return result
    except Exception as e:
        return {{
            "error": f"Tool execution failed: {{str(e)}}",
            "status": "error"
        }}
"""

    # Execute the function definition in a clean namespace
    namespace = {
        "tool_instance": tool_instance,
        "str": str,  # Ensure str is available for error handling
    }

    try:
        exec(func_code, namespace)
        fastmcp_function = namespace["fastmcp_tool_function"]

        # Verify the function was created correctly
        if not callable(fastmcp_function):
            raise ValueError("Generated function is not callable")

        # Verify docstring exists
        if not fastmcp_function.__doc__:
            raise ValueError("Generated function has no docstring")

        print(f"✅ FastMCP function created successfully for '{name}'")
        print(f"   Parameters: {len(param_names)} ({', '.join(param_names)})")
        print(f"   Docstring length: {len(fastmcp_function.__doc__)} chars")

        return fastmcp_function

    except Exception as e:
        print(f"❌ Error creating FastMCP function for '{name}': {e}")
        print(f"Generated code:\n{func_code}")
        raise


def start_mcp_server_for_tool(tool_name: str):
    """Start MCP server for a specific tool."""
    if tool_name not in _mcp_tool_registry:
        print(f"❌ Tool '{tool_name}' not found in MCP registry")
        return

    tool_info = _mcp_tool_registry[tool_name]
    port = tool_info["server_config"]["port"]
    start_mcp_server(port=port)


def stop_mcp_server(port: Optional[int] = None):
    """
    Stop MCP server(s).

    Parameters:
    ===========
    port : int, optional
        Specific port to stop server for. If None, stops all servers.
    """
    if port is not None:
        if port in _mcp_server_instances:
            server = _mcp_server_instances[port]
            asyncio.create_task(server.close())
            del _mcp_server_instances[port]
            print(f"🛑 Stopped MCP server on port {port}")
        else:
            print(f"❌ No server running on port {port}")
    else:
        # Stop all servers
        for port in list(_mcp_server_instances.keys()):
            stop_mcp_server(port)


def list_mcp_tools():
    """List all registered MCP tools with their configurations."""
    if not _mcp_tool_registry:
        print("📭 No MCP tools registered")
        return

    print("📋 Registered MCP Tools:")
    print("=" * 50)

    for name, tool_info in _mcp_tool_registry.items():
        config = tool_info["server_config"]
        print(f"🔧 {name}")
        print(f"   Description: {tool_info['description']}")
        print(f"   Class: {tool_info['class'].__name__}")
        print(f"   Server: {config['host']}:{config['port']}")
        print(f"   Transport: {config['transport']}")
        print()


def get_mcp_tool_urls() -> List[str]:
    """Get list of MCP server URLs for all registered tools."""
    urls = []
    for port, server_info in _mcp_server_configs.items():
        config = server_info["config"]
        if config["transport"] == "http":
            url = f"http://{config['host']}:{port}"
            urls.append(url)
    return urls


# Convenience functions for ToolUniverse integration
def load_mcp_tools_to_tooluniverse(tu, server_urls: Optional[List[str]] = None):
    """
    Load MCP tools from servers into a ToolUniverse instance.

    Parameters:
    ===========
    tu : ToolUniverse
        ToolUniverse instance to load tools into
    server_urls : list of str, optional
        List of MCP server URLs. If None, uses all registered local servers.

    Examples:
    =========
    ```python
    from tooluniverse import ToolUniverse
    from tooluniverse.mcp_tool_registry import load_mcp_tools_to_tooluniverse

    tu = ToolUniverse()

    # Load from specific servers
    load_mcp_tools_to_tooluniverse(tu, [
        "http://localhost:8001",
        "http://analysis-server:8002"
    ])

    # Load from all local registered servers
    load_mcp_tools_to_tooluniverse(tu)
    ```
    """
    if server_urls is None:
        server_urls = get_mcp_tool_urls()

    if not server_urls:
        print("📭 No MCP servers available to load tools from")
        return

    print(f"🔄 Loading MCP tools from {len(server_urls)} servers...")

    for url in server_urls:
        try:
            # Create auto-loader for this server
            loader_config = {
                "name": f"mcp_auto_loader_{url.replace(':', '_').replace('/', '_')}",
                "type": "MCPAutoLoaderTool",
                "server_url": url,
                "auto_register": True,
                "tool_prefix": "mcp_",
                "timeout": 30,
            }

            # Add auto-loader to ToolUniverse
            tu.register_custom_tool(
                tool_class=None,  # Will be loaded by MCPAutoLoaderTool
                tool_type="MCPAutoLoaderTool",
                config=loader_config,
            )

            print(f"✅ Added MCP auto-loader for {url}")

        except Exception as e:
            print(f"❌ Failed to load tools from {url}: {e}")

    print("🎉 MCP tools loading complete!")
