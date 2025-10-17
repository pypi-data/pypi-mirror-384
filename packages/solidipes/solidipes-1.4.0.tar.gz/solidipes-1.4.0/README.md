# Solidipes

_Python package that aids the processes of curating, publishing, and sharing research data_

[![PyPI version](https://badge.fury.io/py/solidipes.svg)](https://badge.fury.io/py/solidipes)
[![Read the Docs](https://readthedocs.org/projects/solidipes/badge/?version=latest)](http://solidipes.readthedocs.io/)

See the package's documentation on [Read the Docs](http://solidipes.readthedocs.io/).

<div style="text-align: center;">
    <img src="https://gitlab.com/solidipes/solidipes/-/raw/main/logos/solidipes.png" width="180px" height="180px">
</div>


# Installation

## As regular user

```bash
pip install solidipes
```


## As developer

If you intend to implement new features into the code (like implementing a new reader for a specific file format or a new type of report), you need to get the source code of Solidipes.


### Dependencies

- Python (3.10 minimum)
- make
- [uv](https://docs.astral.sh/uv/) to manage dependencies


### Installation

```bash
git clone https://gitlab.com/solidipes/solidipes.git
cd solidipes
make install
```

This will install Solidipes as well as all the Python development dependencies. It will also fetch Solidipes plugins in the `plugins` directory.


## Build the documentation

### Dependencies

- [Graphviz](https://graphviz.org/download/)


### Build

Run the following command to build the documentation locally:

```bash
cd docs
make html
```

The documentation will be available in the `docs/build/html` directory.


# Usage from the command line

To see a list of all available commands, run
```bash
solidipes --help
```

Consult the documentation in the [Getting started](https://solidipes.readthedocs.io/en/latest/src/getting_started.html#usage-from-the-command-line) section for next steps.
