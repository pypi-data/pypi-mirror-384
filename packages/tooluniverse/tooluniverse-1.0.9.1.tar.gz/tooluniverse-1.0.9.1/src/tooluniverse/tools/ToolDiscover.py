"""
ToolDiscover

Generates new ToolUniverse-compliant tools based on short descriptions through an intelligent dis...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ToolDiscover(
    tool_description: str,
    max_iterations: int,
    save_to_file: bool,
    output_file: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Generates new ToolUniverse-compliant tools based on short descriptions through an intelligent dis...

    Parameters
    ----------
    tool_description : str
        Short description of the desired tool functionality and purpose. Tool Discove...
    max_iterations : int
        Maximum number of refinement iterations to perform.
    save_to_file : bool
        Whether to save the generated tool configuration and report to a file.
    output_file : str
        Optional file path to save the generated tool. If not provided, uses auto-gen...
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
            "name": "ToolDiscover",
            "arguments": {
                "tool_description": tool_description,
                "max_iterations": max_iterations,
                "save_to_file": save_to_file,
                "output_file": output_file,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ToolDiscover"]
