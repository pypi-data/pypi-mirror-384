"""
FAERS_count_additive_adverse_reactions

Additive multi-drug data: Aggregate adverse reaction counts across specified medicinal products, ...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_additive_adverse_reactions(
    medicinalproducts: list[Any],
    patientsex: str,
    patientagegroup: str,
    occurcountry: str,
    serious: str,
    seriousnessdeath: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Additive multi-drug data: Aggregate adverse reaction counts across specified medicinal products, ...

    Parameters
    ----------
    medicinalproducts : list[Any]
        Array of medicinal product names.
    patientsex : str
        Filter by patient sex.
    patientagegroup : str
        Filter by patient age group.
    occurcountry : str
        Filter by ISO2 country code of occurrence.
    serious : str
        Filter by seriousness classification.
    seriousnessdeath : str
        Filter for fatal outcomes.
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
            "name": "FAERS_count_additive_adverse_reactions",
            "arguments": {
                "medicinalproducts": medicinalproducts,
                "patientsex": patientsex,
                "patientagegroup": patientagegroup,
                "occurcountry": occurcountry,
                "serious": serious,
                "seriousnessdeath": seriousnessdeath,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["FAERS_count_additive_adverse_reactions"]
