"""
UCSC_get_genes_by_region

Query UCSC Genome Browser track API for knownGene features in a genomic window.
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def UCSC_get_genes_by_region(
    chrom: str,
    start: int,
    end: int,
    genome: Optional[str] = "hg38",
    track: Optional[str] = "knownGene",
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Query UCSC Genome Browser track API for knownGene features in a genomic window.

    Parameters
    ----------
    genome : str
        Genome assembly (e.g., hg38).
    chrom : str
        Chromosome (e.g., chr17).
    start : int
        Start position (0-based).
    end : int
        End position.
    track : str
        Track name.
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
            "name": "UCSC_get_genes_by_region",
            "arguments": {
                "genome": genome,
                "chrom": chrom,
                "start": start,
                "end": end,
                "track": track,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["UCSC_get_genes_by_region"]
