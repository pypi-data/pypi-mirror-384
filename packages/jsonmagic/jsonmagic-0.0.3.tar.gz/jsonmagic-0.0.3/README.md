# Welcome to jsonmagic

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Release](https://img.shields.io/pypi/v/jsonmagic.svg)](https://pypi.org/project/jsonmagic)

## Installation

The Python package `jsonmagic` can be installed from PyPI:

```
python -m pip install jsonmagic
```

## Usage

Usage is only meaningful within JupyterLab.

You can do:

```python
from jsonmagic import view_json

view_json(obj)
```

or alternatively use this as a line magic:

```
%load_ext jsonmagic
```

Then, inspect any JSON-like data structure (nested dictionary/list etc) with:

```
%json data
```

Get a browsable output like this:

![Example Output](https://github.com/ssciwr/jsonmagic/blob/main/screenshot.png)

## Acknowledgments

This repository was set up using the [SSC Cookiecutter for Python Packages](https://github.com/ssciwr/cookiecutter-python-package).
