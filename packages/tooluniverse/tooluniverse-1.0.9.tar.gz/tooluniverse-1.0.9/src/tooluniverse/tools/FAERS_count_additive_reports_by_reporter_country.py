"""
FAERS_count_additive_reports_by_reporter_country

Additive multi-drug data: Aggregate adverse event reports by primary reporter country across medi...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_additive_reports_by_reporter_country(
    medicinalproducts: list[Any],
    patientsex: str,
    patientagegroup: str,
    serious: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Additive multi-drug data: Aggregate adverse event reports by primary reporter country across medi...

    Parameters
    ----------
    medicinalproducts : list[Any]
        Array of medicinal product names.
    patientsex : str
        Filter by sex.
    patientagegroup : str
        Filter by age group.
    serious : str
        Filter by seriousness.
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
            "name": "FAERS_count_additive_reports_by_reporter_country",
            "arguments": {
                "medicinalproducts": medicinalproducts,
                "patientsex": patientsex,
                "patientagegroup": patientagegroup,
                "serious": serious,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["FAERS_count_additive_reports_by_reporter_country"]
