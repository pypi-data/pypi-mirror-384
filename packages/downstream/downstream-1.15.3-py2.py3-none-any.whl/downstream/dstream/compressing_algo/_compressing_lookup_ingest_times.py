import typing

from ..._auxlib._inverse_mod_n import inverse_mod_n


def compressing_lookup_ingest_times(
    S: int, T: int
) -> typing.Iterable[typing.Optional[int]]:
    """Ingest time lookup algorithm for compressing curation.

    Lazy implementation.

    Parameters
    ----------
    S : int
        Buffer size. Must be a power of two.
    T : int
        Current logical time.

    Yields
    ------
    typing.Optional[int]
        Ingest time of stored item at buffer sites in index order.
    """
    assert T >= 0
    if T < S:  # Patch for before buffer is filled...
        return (v if v < T else None for v in compressing_lookup_impl(S, S))
    else:  # ... assume buffer has been filled
        return compressing_lookup_impl(S, T)


def compressing_lookup_impl(S: int, T: int) -> typing.Iterable[int]:
    """Implementation detail for `compressing_lookup_ingest_times`."""
    S, T = int(S), int(T)  # play nice with numpy types
    assert S > 1 and S.bit_count() == 1
    assert T >= S  # T < S handled by T = S via compressing_lookup_ingest_times

    yield 0  # Ingest time of site 0 is always 0
    yield 1  # Ingest time of site 1 is always 1

    si = ((T - 2) // (S - 1)).bit_length()  # Current sampling interval
    for k in range(1, S - 1):
        for delta_si in 0, 1:
            si_ = (1 << si) >> delta_si
            assert si_

            inverse = inverse_mod_n(si_, S - 1)
            ansatz_idx = (k * inverse) % (S - 1)
            ansatz_Tbar = si_ * ansatz_idx
            if ansatz_Tbar < T - 1:
                yield ansatz_Tbar + 1
                break
        else:
            assert False


lookup_ingest_times = compressing_lookup_ingest_times  # lazy loader workaround
