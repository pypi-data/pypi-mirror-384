import typing

from ..._auxlib._modpow2 import modpow2
from ._circular_has_ingest_capacity import circular_has_ingest_capacity


def circular_assign_storage_site(S: int, T: int) -> typing.Optional[int]:
    """Site selection algorithm for circular curation.

    Parameters
    ----------
    S : int
        Buffer size. Must be a power of two.
    T : int
        Current logical time.

    Returns
    -------
    typing.Optional[int]
        Selected site, if any.

    Raises
    ------
    ValueError
        If insufficient ingest capacity is available.

        See `circular_algo.has_ingest_capacity` for details.
    """
    if not circular_has_ingest_capacity(S, T):
        raise ValueError(f"Insufficient ingest capacity for {S=}, {T=}")

    return modpow2(T, S)


assign_storage_site = circular_assign_storage_site  # lazy loader workaround
