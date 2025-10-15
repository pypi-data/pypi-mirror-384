import functools
import itertools as it
from random import randrange as rand
import typing

import pytest

from downstream.dstream import sticky_algo as algo


def validate_sticky_site_selection(
    fn: typing.Callable,
) -> typing.Callable:
    """Decorator to validate pre- and post-conditions on site selection."""

    @functools.wraps(fn)
    def wrapper(S: int, T: int) -> typing.Optional[int]:
        assert S.bit_count() == 1  # Assert S is a power of two
        assert 0 <= T  # Assert T is non-negative
        res = fn(S, T)
        assert res is None or 0 <= res < S  # Assert valid output
        return res

    return wrapper


site_selection = validate_sticky_site_selection(algo.assign_storage_site)


def test_sticky_site_selection8():
    # fmt: off
    actual = (site_selection(8, T) for T in it.count())
    expected = [
        0, 1, 2, 3, 4, 5, 6, 7,  # T 0-7
        None, None, None, None, None, None, None, None,  # T 8-15
        None, None, None, None, None, None, None, None,  # T 16-23
        None, None, None, None, None, None, None, None,  # T 24-31
        None, None, None, None, None, None, None, None, # T 32-39
        None, None, None, None, None, None, None, None, # T 40-47
    ]
    assert all(x == y for x, y in zip(actual, expected))


def test_sticky_site_selection16():
    # fmt: off
    actual = (site_selection(16, T) for T in it.count())
    expected = [
        0, 1, 2, 3, 4, 5, 6, 7,  # T 0-7
        8, 9, 10, 11, 12, 13, 14, 15,  # T 8-15
        None, None, None, None, None, None, None, None,  # T 16-23
        None, None, None, None, None, None, None, None,  # T 24-31
    ]
    assert all(x == y for x, y in zip(actual, expected))


def test_sticky_site_selection_fuzz():
    testS = (1 << s for s in range(1, 33))
    testT = it.chain(range(10**5), (rand(2**128) for _ in range(10**5)))
    for S, T in it.product(testS, testT):
        site_selection(S, T)  # Validated via wrapper


@pytest.mark.parametrize("S", [1 << s for s in range(1, 21)])
def test_sticky_site_selection_epoch0(S: int):
    actual = {site_selection(S, T) for T in range(S)}
    expected = set(range(S))
    assert actual == expected


def test_sticky_site_selection_exceeds_capacity():
    with pytest.raises(ValueError):
        algo.assign_storage_site(0, 7)
