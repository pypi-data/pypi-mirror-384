"""
dbSNP_get_variant_by_rsid

Fetch dbSNP variant by rsID using NCBI Variation Services (refsnp endpoint).
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def dbSNP_get_variant_by_rsid(
    rsid: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Fetch dbSNP variant by rsID using NCBI Variation Services (refsnp endpoint).

    Parameters
    ----------
    rsid : str
        rsID without 'rs' prefix or with (e.g., rs699 or 699).
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    dict[str, Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {"name": "dbSNP_get_variant_by_rsid", "arguments": {"rsid": rsid}},
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["dbSNP_get_variant_by_rsid"]
