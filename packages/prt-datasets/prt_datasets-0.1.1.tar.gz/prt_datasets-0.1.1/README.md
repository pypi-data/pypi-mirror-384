# prt-datasets

prt-datasets is a small collection of synthetic and common example datasets packaged as PyTorch Datasets
and Lightning DataModules. It provides utilities and ready-to-use DataModules for common examples used in
experiments and tutorials such as MNIST (classification) and synthetic regression datasets (circle, cubic,
thermistor). The goal of this project is to make it easy to prototype training and uncertainty estimation
workflows with minimal setup.

## Features

- Lightweight PyTorch Dataset implementations for common toy problems
- Lightning DataModule wrappers for easy integration with PyTorch Lightning
- Built-in examples: MNIST (wrapper), Circle, Cubic, Thermistor

## Installation

Requires Python 3.11 or later. The project declares the following runtime dependencies in `pyproject.toml`:

- lightning
- numpy
- requests
- torch

To install from source (editable) with pip and the dev/test extras, run:

```bash
python -m pip install -e .[dev]
```

Or install the package normally:

```bash
python -m pip install .
```

If you only want runtime dependencies, install them directly:

```bash
python -m pip install lightning numpy requests torch
```

## Quick examples

Below are short examples showing how to use DataModules and Datasets in this repository.

Note: the package exposes modules under `prt_datasets`. Import paths shown assume the package is
installed or the repository root is on `PYTHONPATH`.

### Circle (regression)

The `CircleDataModule` creates a synthetic 2D circle dataset and exposes train/val/test dataloaders.

```python
from prt_datasets.regression.circle import CircleDataModule

dm = CircleDataModule(batch_size=128, num_workers=4, seed=0)
dm.prepare_data()
dm.setup()

train_loader = dm.train_dataloader()
for x, y in train_loader:
	# x: angle values, y: 2D coordinates on noisy circle
	break
```

### Cubic (regression)

The `CubicDataModule` provides samples of the function y = x^3 + noise with separate train/test ranges
so you can experiment with interpolation/epistemic uncertainty.

```python
from prt_datasets.regression.cubic import CubicDataModule

dm = CubicDataModule(batch_size=64, num_workers=4, seed=42)
dm.setup()
loader = dm.train_dataloader()
for x, y in loader:
	# x, y are tensors shaped (B, 1)
	break
```

### MNIST (classification)

`MNISTDataModule` is a thin wrapper around `torchvision.datasets.MNIST`. It normalizes data to the
standard MNIST mean/std and provides Lightning DataModule loaders.

```python
from prt_datasets.classification.mnist import MNISTDataModule

dm = MNISTDataModule(root='data', batch_size=64)
dm.prepare_data()
dm.setup()
train_loader = dm.train_dataloader()
for imgs, labels in train_loader:
	break
```

## API overview

- prt_datasets.classification.MNISTDataset, MNISTDataModule
- prt_datasets.regression.CircleDataset, CircleDataModule
- prt_datasets.regression.CubicDataset, CubicDataModule
- prt_datasets.regression.ThermistorDataset, ThermistorModel

Refer to the docstrings in the source files for parameter details and behaviors.

## Tests

This repository uses `pytest` for tests. To run the test suite:

```bash
python -m pip install -e .[dev]
pytest -q
```

There are tests under `tests/` that exercise basic dataset behaviors.

## Contributing

Contributions are welcome. A few guidelines:

- Open an issue to discuss larger changes before implementing them.
- Keep changes small and focused. Add tests for new functionality.
- Follow the repository style and type annotations where present.

## License

This project is provided under the terms of the license in `LICENSE.md`.

## Maintainer

Gavin Strunk

If you spot mistakes or want more example datasets, file an issue or send a PR.
