# Downstream --- Python Implementation

![downstream wordmark](https://raw.githubusercontent.com/mmore500/downstream/master/docs/assets/downstream-wordmark.png)

[![CI](https://github.com/mmore500/downstream/actions/workflows/python-ci.yaml/badge.svg?branch=python)](https://github.com/mmore500/downstream/actions/workflows/python-ci.yaml?query=branch:python)
[![GitHub stars](https://img.shields.io/github/stars/mmore500/downstream.svg?style=flat-square&logo=github&label=Stars&logoColor=white)](https://github.com/mmore500/downstream)
[
![PyPi](https://img.shields.io/pypi/v/downstream.svg)
](https://pypi.python.org/pypi/downstream)
[![DOI](https://zenodo.org/badge/776865597.svg)](https://zenodo.org/doi/10.5281/zenodo.10866541)

downstream provides efficient, constant-space implementations of stream curation algorithms.

-   Free software: MIT license

<!---
-   Documentation: <https://downstream.readthedocs.io>.
-->

## Installation

To install from PyPi with pip, run

`python3 -m pip install "downstream[jit]"`

A containerized release of `downstream` is available via <https://ghcr.io>

```bash
singularity exec docker://ghcr.io/mmore500/downstream:v1.15.3 python3 -m downstream --help
```

## Citing

If downstream contributes to a scientific publication, please cite it as

> Yang C., Wagner J., Dolson E., Zaman L., & Moreno M. A. (2025). Downstream: efficient cross-platform algorithms for fixed-capacity stream downsampling. arXiv preprint arXiv:2506.12975. https://doi.org/10.48550/arXiv.2506.12975

```bibtex
@misc{yang2025downstream,
      doi={10.48550/arXiv.2506.12975},
      url={https://arxiv.org/abs/2506.12975},
      title={Downstream: efficient cross-platform algorithms for fixed-capacity stream downsampling},
      author={Connor Yang and Joey Wagner and Emily Dolson and Luis Zaman and Matthew Andres Moreno},
      year={2025},
      eprint={2506.12975},
      archivePrefix={arXiv},
      primaryClass={cs.DS},
}
```

And don't forget to leave a [star on GitHub](https://github.com/mmore500/downstream/stargazers)!
