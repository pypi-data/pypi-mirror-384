import functools
import typing

import numpy as np
import pytest

from downstream import dstream
from downstream.dstream import hybrid_algo as algo_class


def validate_lookup(fn: typing.Callable) -> typing.Callable:
    """Decorator to validate pre- and post-conditions on site lookup."""

    @functools.wraps(fn)
    def wrapper(S: int, T: np.ndarray, *args, **kwargs) -> np.ndarray:
        assert np.asarray(S <= T).all()  # T is non-negative
        res = fn(S, T, *args, **kwargs)
        assert (np.clip(res, 0, T[:, None] - 1) == res).all()
        return res

    return wrapper


@pytest.mark.parametrize(
    "algo",
    [
        algo_class(0, dstream.steady_algo, 1),
        algo_class(0, dstream.steady_algo, 1, dstream.stretched_algo, 2),
        algo_class(0, dstream.tilted_algo, 1, dstream.tilted_algo, 2),
        algo_class(
            0,
            dstream.tilted_algo,
            1,
            dstream.tilted_algo,
            2,
            dstream.steady_algo,
            3,
        ),
        algo_class(
            0,
            dstream.steady_algo,
            2,
            dstream.stretched_algo,
            3,
            dstream.steady_algo,
            4,
        ),
        algo_class(
            0,
            dstream.steady_algo,
            1,
            dstream.stretched_algo,
            3,
            dstream.tilted_algo,
            4,
        ),
    ],
)
@pytest.mark.parametrize("s", range(1, 7))
def test_lookup_against_site_selection(algo: typing.Any, s: int):
    time_lookup = validate_lookup(algo.lookup_ingest_times_batched)
    S = (1 << s) * algo._get_num_chunks()
    T_max = min(1 << (20 - s), algo.get_ingest_capacity(S) or 2**S - 1)
    expected = [None] * S

    expecteds = []
    for T in range(T_max):
        if T >= S:
            expecteds.extend(expected)

        site = algo.assign_storage_site(S, T)
        if site is not None:
            expected[site] = T

    actual = time_lookup(S, np.arange(S, T_max)).ravel()
    np.testing.assert_array_equal(expecteds, actual)
