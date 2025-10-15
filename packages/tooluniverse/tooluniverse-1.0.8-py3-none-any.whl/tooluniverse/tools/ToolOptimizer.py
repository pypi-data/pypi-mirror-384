"""
ToolOptimizer

Optimizes tool configurations based on quality feedback. Improves tool specifications and impleme...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ToolOptimizer(
    tool_config: str,
    quality_feedback: str,
    optimization_target: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Optimizes tool configurations based on quality feedback. Improves tool specifications and impleme...

    Parameters
    ----------
    tool_config : str
        JSON string of the original tool configuration
    quality_feedback : str
        JSON string of quality evaluation feedback
    optimization_target : str
        What to optimize for (improve_quality, enhance_performance, etc.)
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
            "name": "ToolOptimizer",
            "arguments": {
                "tool_config": tool_config,
                "quality_feedback": quality_feedback,
                "optimization_target": optimization_target,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ToolOptimizer"]
