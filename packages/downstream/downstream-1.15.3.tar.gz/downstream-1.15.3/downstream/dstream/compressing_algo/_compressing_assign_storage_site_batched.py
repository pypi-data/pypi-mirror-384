import typing

import numpy as np

from ..._auxlib._bitlen32 import bitlen32
from ..._auxlib._ctz32 import ctz32


def compressing_assign_storage_site_batched(
    S: typing.Union[np.ndarray, int], T: typing.Union[np.ndarray, int]
) -> np.ndarray:
    """Site selection algorithm for steady curation.

    Vectorized implementation for bulk calculations.

    Parameters
    ----------
    S : Union[np.ndarray, int]
        Buffer size. Must be a power of two, <= 2**52.
    T : Union[np.ndarray, int]
        Current logical time. Must be <= 2**52.

    Returns
    -------
    np.array
        Selected site, if any. Otherwise, S.
    """
    S, T = np.atleast_1d(S).astype(np.int64), np.atleast_1d(T).astype(np.int64)
    assert np.logical_and(S > 1, np.bitwise_count(S) == 1).all()
    # restriction <= 2 ** 52 might be overly conservative
    assert (np.maximum(S, T) <= 2**52).all()

    T_ = T - (T > 0)
    si = bitlen32(T_ // (S - 1))  # Current sampling interval
    h = ctz32(np.maximum(T_, 1))  # Current hanoi value

    res = (T_) % (S - 1) + 1
    res[h < si] = np.broadcast_to(S, res.shape)[h < si]
    res[T == 0] = 0  # special-case site 0 for T = 0, to fill entire buffer
    return res


# lazy loader workaround
assign_storage_site_batched = compressing_assign_storage_site_batched
