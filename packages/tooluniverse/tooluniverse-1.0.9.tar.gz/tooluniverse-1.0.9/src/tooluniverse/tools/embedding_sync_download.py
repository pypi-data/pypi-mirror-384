"""
embedding_sync_download

Download an embedding database from HuggingFace Hub to local storage. Allows accessing databases ...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def embedding_sync_download(
    action: str,
    repository: str,
    local_name: str,
    overwrite: bool,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Download an embedding database from HuggingFace Hub to local storage. Allows accessing databases ...

    Parameters
    ----------
    action : str
        Action to download database from HuggingFace
    repository : str
        HuggingFace repository to download from (format: username/repo-name)
    local_name : str
        Local name for the downloaded database (optional, defaults to repo name)
    overwrite : bool
        Whether to overwrite existing local database with same name
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
            "name": "embedding_sync_download",
            "arguments": {
                "action": action,
                "repository": repository,
                "local_name": local_name,
                "overwrite": overwrite,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["embedding_sync_download"]
