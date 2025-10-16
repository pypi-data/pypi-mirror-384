"""
alphafold_get_annotations

Retrieve AlphaFold variant annotations (e.g., missense mutations) for a given UniProt accession (...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def alphafold_get_annotations(
    qualifier: str,
    type: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Retrieve AlphaFold variant annotations (e.g., missense mutations) for a given UniProt accession (...

    Parameters
    ----------
    qualifier : str
        Protein identifier: UniProt accession, entry name, or CRC64 checksum.
    type : str
        Annotation type (currently only 'MUTAGEN' is supported).
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
            "name": "alphafold_get_annotations",
            "arguments": {"qualifier": qualifier, "type": type},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["alphafold_get_annotations"]
