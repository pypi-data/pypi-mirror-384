"""
gnomAD_query_variant

Query gnomAD GraphQL for a variant in a dataset (returns ID and genome allele counts/frequency).
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def gnomAD_query_variant(
    variant_id: str,
    dataset: Optional[str] = "gnomad_r4",
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Query gnomAD GraphQL for a variant in a dataset (returns ID and genome allele counts/frequency).

    Parameters
    ----------
    variant_id : str
        Variant ID like '1-230710048-A-G'.
    dataset : str
        Dataset ID (e.g., gnomad_r4).
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
        {
            "name": "gnomAD_query_variant",
            "arguments": {"variant_id": variant_id, "dataset": dataset},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["gnomAD_query_variant"]
