"""
FAERS_count_reactions_by_drug_event

Count the number of adverse reactions reported for a given drug, filtered by patient details, eve...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def FAERS_count_reactions_by_drug_event(
    medicinalproduct: str,
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
    Count the number of adverse reactions reported for a given drug, filtered by patient details, eve...

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
    serious : str
        Whether the event was serious.
    seriousnessdeath : str
        Was death reported?
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
            "name": "FAERS_count_reactions_by_drug_event",
            "arguments": {
                "medicinalproduct": medicinalproduct,
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


__all__ = ["FAERS_count_reactions_by_drug_event"]
