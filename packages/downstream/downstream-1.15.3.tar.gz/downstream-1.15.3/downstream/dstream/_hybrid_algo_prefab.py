from . import (
    steady_algo,
    stretched_algo,
    stretchedxtc_algo,
    tilted_algo,
    tiltedxtc_algo,
)
from ._hybrid_algo import hybrid_algo

hybrid_0_steady_1_stretched_2_algo = hybrid_algo(
    0, steady_algo, 1, stretched_algo, 2
)
hybrid_0_steady_1_stretchedxtc_2_algo = hybrid_algo(
    0, steady_algo, 1, stretchedxtc_algo, 2
)
hybrid_0_steady_1_tilted_2_algo = hybrid_algo(
    0, steady_algo, 1, tilted_algo, 2
)
hybrid_0_steady_1_tiltedxtc_2_algo = hybrid_algo(
    0, steady_algo, 1, tiltedxtc_algo, 2
)
