"""
ToolSpecificationGenerator

Generates complete ToolUniverse-compliant tool specifications based on a description and analysis...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ToolSpecificationGenerator(
    tool_description: str,
    tool_category: str,
    tool_type: str,
    similar_tools: str,
    existing_tools_summary: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Generates complete ToolUniverse-compliant tool specifications based on a description and analysis...

    Parameters
    ----------
    tool_description : str
        Brief description of the desired tool functionality and purpose.
    tool_category : str
        Target category for the tool (e.g., 'biomedical', 'data_analysis', 'text_proc...
    tool_type : str
        Specific ToolUniverse tool type (e.g., 'AgenticTool', 'RESTTool', 'PythonTool').
    similar_tools : str
        JSON string containing configurations of similar existing tools for analysis ...
    existing_tools_summary : str
        Summary of existing tools in the ecosystem to avoid duplication and identify ...
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    Any
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "ToolSpecificationGenerator",
            "arguments": {
                "tool_description": tool_description,
                "tool_category": tool_category,
                "tool_type": tool_type,
                "similar_tools": similar_tools,
                "existing_tools_summary": existing_tools_summary,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ToolSpecificationGenerator"]
