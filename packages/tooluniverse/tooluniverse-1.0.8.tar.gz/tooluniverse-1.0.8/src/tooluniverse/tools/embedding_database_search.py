"""
embedding_database_search

Search for semantically similar documents in an embedding database. Uses OpenAI embeddings to con...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def embedding_database_search(
    action: str,
    database_name: str,
    query: str,
    top_k: int,
    filters: dict[str, Any],
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Search for semantically similar documents in an embedding database. Uses OpenAI embeddings to con...

    Parameters
    ----------
    action : str
        Action to search the database
    database_name : str
        Name of the database to search in
    query : str
        Query text to find similar documents for
    top_k : int
        Number of most similar documents to return
    filters : dict[str, Any]
        Optional metadata filters to apply to search results
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
            "name": "embedding_database_search",
            "arguments": {
                "action": action,
                "database_name": database_name,
                "query": query,
                "top_k": top_k,
                "filters": filters,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["embedding_database_search"]
