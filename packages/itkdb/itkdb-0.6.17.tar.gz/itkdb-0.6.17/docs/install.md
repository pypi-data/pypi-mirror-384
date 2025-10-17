# Installation

There are two separate set of features shipped with this package:

- `contrib` (better handling of errors that return HTML instead of JSON)
- `eos` (support for uploading files to EOS)

These can be installed using your favorite installation method below. For
example,

```bash
# install eos support
python -m pip install itkdb[eos]

# install contrib
python -m pip install itkdb[contrib]

# install multiple features
python -m pip install itkdb[contrib,eos]
```

---

## pip

itkdb is available on PyPI and can be installed with [pip](https://pip.pypa.io).

```bash
pip install itkdb
```

<!-- prettier-ignore -->
!!! warning
    This method modifies the Python environment in which you choose to install. Consider instead using [pipx](#pipx) or virtual environments to avoid dependency conflicts.

## pipx

[pipx](https://github.com/pypa/pipx) allows for the global installation of
Python applications in isolated environments.

```bash
pipx install itkdb
```

## virtual environment

```bash
python -m venv venv
source venv/bin/activate
python -m pip install itkdb
```

## Conda

See the [feedstock](https://github.com/conda-forge/itkdb-feedstock) for more
details.

```bash
conda install -c conda-forge itkdb
```

or with [mamba](https://github.com/mamba-org/mamba):

```bash
mamba install itkdb
```

<!-- prettier-ignore -->
!!! warning
    This method modifies the Conda environment in which you choose to install. Consider instead using [pipx](#pipx) or [condax](https://github.com/mariusvniekerk/condax) to avoid dependency conflicts.
