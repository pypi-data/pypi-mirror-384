"""
embedding_database_add

Add new documents to an existing embedding database. Generates embeddings for new documents using...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def embedding_database_add(
    action: str,
    database_name: str,
    documents: list[Any],
    metadata: list[Any],
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Add new documents to an existing embedding database. Generates embeddings for new documents using...

    Parameters
    ----------
    action : str
        Action to add documents to existing database
    database_name : str
        Name of the existing database to add documents to
    documents : list[Any]
        List of new document texts to embed and add
    metadata : list[Any]
        Optional metadata for each new document (same length as documents)
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
            "name": "embedding_database_add",
            "arguments": {
                "action": action,
                "database_name": database_name,
                "documents": documents,
                "metadata": metadata,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["embedding_database_add"]
