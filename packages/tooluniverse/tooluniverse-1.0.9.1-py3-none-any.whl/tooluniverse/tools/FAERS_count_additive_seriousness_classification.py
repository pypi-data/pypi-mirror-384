"""
FAERS_count_additive_seriousness_classification

Additive multi-drug data: Quantify serious vs non-serious classifications across medicinal produc...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_additive_seriousness_classification(
    medicinalproducts: list[Any],
    patientsex: str,
    patientagegroup: str,
    occurcountry: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Additive multi-drug data: Quantify serious vs non-serious classifications across medicinal produc...

    Parameters
    ----------
    medicinalproducts : list[Any]
        Array of medicinal product names.
    patientsex : str
        Filter by sex.
    patientagegroup : str
        Filter by age group.
    occurcountry : str
        ISO2 country code filter.
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
            "name": "FAERS_count_additive_seriousness_classification",
            "arguments": {
                "medicinalproducts": medicinalproducts,
                "patientsex": patientsex,
                "patientagegroup": patientagegroup,
                "occurcountry": occurcountry,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["FAERS_count_additive_seriousness_classification"]
