<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# gemseo-matlab

[![PyPI - License](https://img.shields.io/pypi/l/gemseo-matlab)](https://www.gnu.org/licenses/lgpl-3.0.en.html)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gemseo-matlab)](https://pypi.org/project/gemseo-matlab/)
[![PyPI](https://img.shields.io/pypi/v/gemseo-matlab)](https://pypi.org/project/gemseo-matlab/)
[![Codecov branch](https://img.shields.io/codecov/c/gitlab/gemseo:dev/gemseo-matlab/develop)](https://app.codecov.io/gl/gemseo:dev/gemseo-matlab)

## Overview

MATLAB wrapper for GEMSEO

## Installation

!!! warning

    This plugin requires that a MATLAB engine as well as
    its Python API are installed. The MATLAB Python API is not defined as a
    dependency of this package, because until MATLAB release R2020b there
    was no package available in PyPI. It shall be installed in the same
    environment as the one in which this plugin is installed, please refer
    to the MATLAB documentation for further information.

    Here are the current versions of the MATLAB Python packages per MATLAB
    versions:

    | Python | Matlab | matlabengine |
    |:------:|:------:|:------------:|
    | 3.10 | r2022b | 9.13 |
    | 3.10 | r2023a | 9.14 |
    | 3.10, 3.11 | r2023b | 23.2 |
    | 3.10, 3.11 | r2024a | 24.1 |

    To make sure that MATLAB works fine through the Python API, start a
    Python interpreter and check that there is no error when executing
    `import matlab`.

Install the latest stable version with `pip install gemseo-matlab`.

See [pip](https://pip.pypa.io/en/stable/getting-started/) for more information.

## Development

For testing with `tox`, set the environment variable
`MATLAB_PIP_REQ_SPEC` to point to the URL or path of a `pip` installable
version of the MATLAB Python API, with eventually a conditional
dependency on the Python version:

``` console
export MATLAB_PIP_REQ_SPEC="matlabengine~=X.Y.0"
```

where `X.Y` is the version number in above table.

## Docker

To create or update the podman/docker images for testing the plugin,
adapt with the proper version of matlab:

``` console
podman build Dockerfile -t gemseo-matlab:r2020b --build-arg=MATLAB_VERSION=r2020b
```

## Bugs and questions

Please use the [gitlab issue tracker](https://gitlab.com/gemseo/dev/gemseo-matlab/-/issues)
to submit bugs or questions.

## Contributing

See the [contributing section of GEMSEO](https://gemseo.readthedocs.io/en/stable/software/developing.html#dev).

## Contributors

- GEMSEO developers
