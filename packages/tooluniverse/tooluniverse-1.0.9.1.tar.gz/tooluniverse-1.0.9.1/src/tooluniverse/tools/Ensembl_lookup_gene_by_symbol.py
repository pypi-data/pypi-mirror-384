"""
Ensembl_lookup_gene_by_symbol

Lookup Ensembl gene by species and gene symbol, returning core metadata and coordinates (uses /xr...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def Ensembl_lookup_gene_by_symbol(
    symbol: str,
    species: Optional[str] = "homo_sapiens",
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Lookup Ensembl gene by species and gene symbol, returning core metadata and coordinates (uses /xr...

    Parameters
    ----------
    species : str
        Species name (e.g., 'homo_sapiens').
    symbol : str
        Gene symbol (e.g., BRCA1).
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
            "name": "Ensembl_lookup_gene_by_symbol",
            "arguments": {"species": species, "symbol": symbol},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["Ensembl_lookup_gene_by_symbol"]
