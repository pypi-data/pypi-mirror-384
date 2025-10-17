# Cocycle Hunter

Python package for hunting for cocycles in single-cell RNA-seq data.

## Installation

Cocycle hunter can currently be installed as a python package "chunter" from the PyPi test repository "https://test.pypi.org". To following steps might be used to setup a python environment that contains cocycle hunter:

### Using UV package manager

1. Install UV as described on the UV web page.
2. Create an empty folder "testing-cocycle-hunter"
3. In the terminal run
```
uv init
uv add --dev ipykernel
uv add chunter --index testpypi=https://test.pypi.org/simple --index-strategy unsafe-best-match
```

### Using conda + pip

```
conda create -n cocycle-hunter-env python=3.10 pip matplotlib pandas ipykernel
conda activate cocycle-hunter-env
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ chunter==0.1.1
```
