import typing

from ..._auxlib._ctz import ctz
from ._compressing_has_ingest_capacity import compressing_has_ingest_capacity


def compressing_assign_storage_site(S: int, T: int) -> typing.Optional[int]:
    """Site selection algorithm for compressing curation.

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

        See `compressing_algo.has_ingest_capacity` for details.

    References
    ----------
    John C. Gunther. 2014. Algorithm 938: Compressing circular buffers. ACM
    Trans. Math. Softw. 40, 2, Article 17 (February 2014), 12 pages.
    https://doi.org/10.1145/2559995
    """
    if not compressing_has_ingest_capacity(S, T):
        raise ValueError(f"Insufficient ingest capacity for {S=}, {T=}")

    # special-case site 0 for T = 0, to fill entire buffer
    if T == 0:
        return 0
    else:
        T -= 1

    si = (T // (S - 1)).bit_length()  # Current sampling interval
    h = ctz(T or 1)  # Current hanoi value
    return None if h < si else T % (S - 1) + 1


assign_storage_site = compressing_assign_storage_site  # lazy loader workaround
