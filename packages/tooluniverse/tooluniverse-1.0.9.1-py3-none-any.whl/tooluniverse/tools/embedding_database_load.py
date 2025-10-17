"""
embedding_database_load

Load an existing embedding database from a local path or external source. Allows importing databa...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def embedding_database_load(
    action: str,
    database_path: str,
    database_name: str,
    overwrite: bool,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Load an existing embedding database from a local path or external source. Allows importing databa...

    Parameters
    ----------
    action : str
        Action to load database from external source
    database_path : str
        Path to the existing database directory or file
    database_name : str
        Local name to assign to the loaded database
    overwrite : bool
        Whether to overwrite existing database with same name
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
            "name": "embedding_database_load",
            "arguments": {
                "action": action,
                "database_path": database_path,
                "database_name": database_name,
                "overwrite": overwrite,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["embedding_database_load"]
