"""
FAERS_count_additive_administration_routes

Additive multi-drug data: Enumerate and count administration routes for adverse events across spe...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_additive_administration_routes(
    medicinalproducts: list[Any],
    serious: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Additive multi-drug data: Enumerate and count administration routes for adverse events across spe...

    Parameters
    ----------
    medicinalproducts : list[Any]
        Array of medicinal product names.
    serious : str
        Filter by seriousness.
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
            "name": "FAERS_count_additive_administration_routes",
            "arguments": {"medicinalproducts": medicinalproducts, "serious": serious},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["FAERS_count_additive_administration_routes"]
