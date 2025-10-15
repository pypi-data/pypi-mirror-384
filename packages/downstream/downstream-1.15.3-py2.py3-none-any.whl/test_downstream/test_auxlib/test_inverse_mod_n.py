import pytest

from downstream._auxlib._inverse_mod_n import inverse_mod_n


def test_inverse_mod_n_valid():
    # Test valid cases: e is a power of 2 and n+1 is a power of 2.

    # For e=2 and n=3 (since 2 is 2**1 and 3+1=4 is 2**2),
    # the inverse is 2 because 2*2 % 3 == 1.
    assert inverse_mod_n(2, 3) == 2

    # For e=4 and n=7 (4 is 2**2 and 7+1=8 is 2**3),
    # the inverse is 2 because 4*2 % 7 == 1.
    assert inverse_mod_n(4, 7) == 2

    # For e=8 and n=15 (8 is 2**3 and 15+1=16 is 2**4),
    # the inverse is 2 because 8*2 % 15 == 1.
    assert inverse_mod_n(8, 15) == 2

    # For e=1 and n=3 (1 is 2**0 and 3+1=4 is 2**2),
    # the inverse is 1.
    assert inverse_mod_n(1, 3) == 1


def test_invalid_e():
    # Test that if e is not a power of 2, a ValueError is raised.
    with pytest.raises(ValueError):
        inverse_mod_n(3, 7)


def test_invalid_n():
    # Test that if n+1 is not a power of 2, a ValueError is raised.
    with pytest.raises(ValueError):
        inverse_mod_n(2, 6)
