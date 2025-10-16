"""
FAERS_count_seriousness_by_drug_event

Count the number of adverse event reports classified as serious or non-serious, filtered by drug ...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_seriousness_by_drug_event(
    medicinalproduct: str,
    patientsex: str,
    patientagegroup: str,
    occurcountry: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Count the number of adverse event reports classified as serious or non-serious, filtered by drug ...

    Parameters
    ----------
    medicinalproduct : str
        Drug name.
    patientsex : str
        Patient sex, leave it blank if you don't want to apply a filter.
    patientagegroup : str
        Patient age group.
    occurcountry : str
        Country where event occurred.
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
            "name": "FAERS_count_seriousness_by_drug_event",
            "arguments": {
                "medicinalproduct": medicinalproduct,
                "patientsex": patientsex,
                "patientagegroup": patientagegroup,
                "occurcountry": occurcountry,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["FAERS_count_seriousness_by_drug_event"]
