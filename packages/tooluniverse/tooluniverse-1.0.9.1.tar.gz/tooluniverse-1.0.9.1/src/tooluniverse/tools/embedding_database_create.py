"""
embedding_database_create

Create a new embedding database from a collection of documents. Generates embeddings using OpenAI...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def embedding_database_create(
    action: str,
    database_name: str,
    documents: list[Any],
    metadata: list[Any],
    model: str,
    description: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Create a new embedding database from a collection of documents. Generates embeddings using OpenAI...

    Parameters
    ----------
    action : str
        Action to create database from documents
    database_name : str
        Name for the new database (must be unique)
    documents : list[Any]
        List of document texts to embed and store
    metadata : list[Any]
        Optional metadata for each document (same length as documents)
    model : str
        OpenAI/Azure OpenAI embedding model to use
    description : str
        Optional description for the database
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
            "name": "embedding_database_create",
            "arguments": {
                "action": action,
                "database_name": database_name,
                "documents": documents,
                "metadata": metadata,
                "model": model,
                "description": description,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["embedding_database_create"]
