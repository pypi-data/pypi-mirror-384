"""
ClinVar_search_variants

Search ClinVar via NCBI E-utilities (esearch→esummary) and return concise variant records for a q...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ClinVar_search_variants(
    query: str,
    retmax: Optional[int] = 5,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> list[Any]:
    """
    Search ClinVar via NCBI E-utilities (esearch→esummary) and return concise variant records for a q...

    Parameters
    ----------
    query : str
        ClinVar search term (e.g., BRCA1).
    retmax : int
        Max records.
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    list[Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "ClinVar_search_variants",
            "arguments": {"query": query, "retmax": retmax},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ClinVar_search_variants"]
