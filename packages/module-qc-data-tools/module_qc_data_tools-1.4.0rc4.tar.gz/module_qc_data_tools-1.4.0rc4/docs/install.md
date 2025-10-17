# Installation

This tool **requires** users to have a python version that is still supported
(not end-of-life). You can check the status of different python versions
[here](https://devguide.python.org/versions/#status-of-python-versions). Check
your local python version with `python -V`. If the local python version is lower
than what is currently supported, set up a virtual python environment following
the instructions [here](https://itk.docs.cern.ch/general/Virtual_Environments/).

This package may be accessed by cloning from gitlab or by installing it via pip.

## git

Use this method if you want to use the latest version of the package from
GitLab.

=== "HTTPS"

    ``` bash
    git clone https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools.git
    ```

=== "SSH"

    ``` bash
    ssh://git@gitlab.cern.ch:7999/atlas-itk/pixel/module/module-qc-data-tools.git
    ```

=== "KRB5"

    ``` bash
    https://:@gitlab.cern.ch:8443/atlas-itk/pixel/module/module-qc-data-tools.git
    ```

=== "branch/commit"

    ``` bash
    git+ssh://git@gitlab.cern.ch:7999/atlas-itk/pixel/module/module-qc-data-tools.git@main
    ```

Upon a successful checkout, `cd` to the new `module-qc-data-tools` directory and
run the following to install the necessary software in a virtual environment:

=== "With pip"

    ```bash
    $ python -m venv venv
    $ source venv/bin/activate
    $ python -m pip install -U pip
    $ python -m pip install -e .
    ```

=== "With uv"

    ```bash
    $ python -m venv venv
    $ source venv/bin/activate
    $ python -m pip install uv
    $ uv pip install -e .
    ```

This installs in `editable` mode which allows for development work as well.

## pip

module-qc-data-tools is available on PyPI and can be installed with
[pip](https://pip.pypa.io).

```bash
pip install module-qc-data-tools
```

<!-- prettier-ignore -->
!!! warning
    This method modifies the Python environment in which you choose to install. Consider instead using [pipx](#pipx) or virtual environments to avoid dependency conflicts.

## pipx

[pipx](https://github.com/pypa/pipx) allows for the global installation of
Python applications in isolated environments.

```bash
pipx install module-qc-data-tools
```

## virtual environment

```bash
python -m venv venv
source venv/bin/activate
python -m pip install module-qc-data-tools
```

### via pip

Use this method if you want to use the latest stable (versioned) release of the
package.

```
$ python -m venv venv
$ source venv/bin/activate
$ python -m pip install -U pip
$ python -m pip install module-qc-data-tools==1.4.0rc4
```

### via uv

```
$ python -m venv venv
$ source venv/bin/activate
$ python -m pip install uv
$ uv pip install module-qc-data-tools==1.4.0rc4
```

# Usage

After installation, one just needs to enter the virtual environment in each new
session to use the scripts:

```bash
source venv/bin/activate
```
