# xpcs-correlator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Repository](https://img.shields.io/badge/Repo-GitLab-ff69b4.svg)](https://gitlab.esrf.fr/mj/xpcs_developments/xpcscorr)

## Table of contents
- About
- Documentation
- Features
- Requirements
- Installation
- Quickstart
- Configuration / Logging
- Tests
- Contributing
- License
- Contact

## About
This package consolidates ongoing development of correlators for XPCS data analysis at ESRF, with a focus on the ID02 and ID10-coh beamlines.

## Documentation
The documentation is hosted online: [https://mj.gitlab-pages.esrf.fr/xpcs_developments/xpcscorr/](https://mj.gitlab-pages.esrf.fr/xpcs_developments/xpcscorr/)

## Features
- Dense frames data reference and chunked correlator implementations.
- Calculates g2, g2 errors, and ttcf (2-time correlation function).
- The ttcf calculations support linear binning for t1,t2 format and hybrid linear log binning for age,lag format.
- Designed to handle large frame stacks via chunked (partitioned) processing.
- Supports Dask for both cluster (SLURM) and local parallel execution

## Requirements
- Python 3.10+ (recommended: 3.10, 3.11, 3.12)
- numpy
- dask
- dask_jobqueue
- h5py
- hdf5plugin
- threadpoolctl

## Installation
Install in editable/develop mode (recommended during development):

```bash
pip install -e .
```

Install with development extras (for running tests and linters):

```bash
pip install -e .[dev]
```

When published to PyPI the package can be installed with:

```bash
pip install xpcs-correlator
```

## Quickstart
For a step-by-step walkthrough with examples and runnable code, see the Tutorial in the online documentation: [Quickstart tutorial](https://mj.gitlab-pages.esrf.fr/xpcs_developments/xpcscorr/tutorials/quickstart/).

Basic usage example — adapt to your data shape and correlator options:

```python
import numpy as np
from xpcscorr import correlator_dense_reference, correlator_dense_chunked

# Replace with your frames array; shape here is (n_frames, nx_pixels, ny_pixels)
frames = np.random.random((100,512, 512))
roimask= np.ones((512,512), dtype=bool)

# Run reference  correlator
result_ref = correlator_dense_reference(frames, roimask)

# Run chunked correlator (handles large data in chunks)
extra_options = {'chunks_N': 3}
result_chunked = correlator_dense_chunked(frames, roimask, extra_options=extra_options)

print(type(result_ref), type(result_chunked))
```

Notes:
- Replace the synthetic `frames` with your real dataset (HDF5 dataset or numpy array).
- Check correlator function docstrings for exact argument names and options.

## Configuration / Logging
Control logging with environment variables used by the package (see `src/xpcscorr/__init__.py`):

- `XPCSCORR_LOG_TO_CLI` — set to `1` to enable logging to stdout (default in development)
- `XPCSCORR_LOG_TO_FILE` — set to `1` to enable logging to a file named `xpcscorr.log`

Example:

```bash
export XPCSCORR_LOG_TO_CLI=1
export XPCSCORR_LOG_TO_FILE=0
```

## Tests
Run tests with pytest:

```bash
pip install -e .[dev]
pytest -q
```

There are unit tests under `tests/` that exercise correlator behavior and core utilities.

## Contributing
- Open issues for bugs or feature requests.
- Fork the repo, create a feature branch, add tests, and submit a pull request.
- Keep changes small, document API changes, and add tests for new behavior.

## License
This project is licensed under the MIT License — see the `LICENSE` file for details.

## Contact
Maintainer: Maciej Jankowski — maciej.jankowski@esrf.fr


<!-- EOF -->

