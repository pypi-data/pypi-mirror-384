# PdmV HTTP Client

This project provides an HTTP client based on [requests](https://github.com/psf/requests) to handle authenticated requests to CERN
internal applications. Furthermore, it includes some clients to ease the interaction with the APIs of
PdmV applications. This version is a refactor of the old [McM Scripts](https://github.com/cms-PdmV/mcm_scripts) project, and it is published at
PyPI to be public available.

### How to use this package

#### Prerequisite

Create an isolated virtual environment using a Python version >= 3.9 like, for instance:

`python3.9 -m venv venv && source ./venv/bin/activate`

#### Development version

If you want to set up a development environment to contribute to this project:

Install `uv` and the required dependencies.

`pip install uv`

Set the current `venv` to use with `uv`:

`export UV_PROJECT_ENVIRONMENT="${VIRTUAL_ENV}"`

Install the packages via: `uv sync`

Run the test suite via:
`uv run pytest -s -vv`

> [!IMPORTANT]
> Make sure your execution environment has a valid Kerberos ticket to consume CERN services!

#### Build package

If you just want to use this package in your own project, install it via:

`pip install pdmv-http-client`

Make sure to remove the `sys.path.append(...)` statement, if you have them in your script, to avoid overloading old versions from CERN AFS.

### Examples

At the `examples/` folder, you will find some scripts explaining how to use the clients and the HTTP client.

### Priority change
* If you want to use priority-changing scripts or do anything else related to cmsweb, you'll have to use voms-proxy:
    * `voms-proxy-init -voms cms`
    * `export X509_USER_PROXY=$(voms-proxy-info --path)`
