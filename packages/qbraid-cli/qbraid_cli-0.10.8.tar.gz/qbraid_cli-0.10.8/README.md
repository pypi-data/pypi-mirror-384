<img width="full" alt="qbraid_cli" src="https://qbraid-static.s3.amazonaws.com/logos/qbraid-cli-banner.png">

[![Documentation](https://img.shields.io/badge/Documentation-DF0982)](https://docs.qbraid.com/cli/user-guide/overview)
[![PyPI version](https://img.shields.io/pypi/v/qbraid-cli.svg?color=blue)](https://pypi.org/project/qbraid-cli/)
[![Python verions](https://img.shields.io/pypi/pyversions/qbraid-cli.svg?color=blue)](https://pypi.org/project/qbraid-cli/)
[![Downloads](https://static.pepy.tech/badge/qbraid-cli)](https://pepy.tech/project/qbraid-cli)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/qBraid/community/issues)
[![Stack Overflow](https://img.shields.io/badge/StackOverflow-qbraid-orange?logo=stackoverflow)](https://stackoverflow.com/questions/tagged/qbraid)

Command Line Interface for interacting with all parts of the qBraid platform.

The **qBraid CLI** is a versatile command-line interface tool designed for seamless interaction with qBraid cloud services and quantum software management tools. Initially exclusive to the [qBraid Lab](https://docs.qbraid.com/lab/user-guide/overview) platform, the CLI now supports local installations as well. This enhancement broadens access to features like [qBraid Quantum Jobs](https://docs.qbraid.com/cli/user-guide/quantum-jobs), enabling direct, pre-configured access to QPUs from IonQ, Oxford Quantum Circuits, QuEra, Rigetti, and IQM, as well as on-demand simulators from qBraid, AWS, IonQ, QuEra, and NEC. See [pricing](https://docs.qbraid.com/home/pricing) for more.

*Resources*:
- [User Guide](https://docs.qbraid.com/cli/user-guide/overview)
- [API Reference](https://docs.qbraid.com/cli/api-reference/qbraid)

## Getting Started

The qBraid-CLI comes pre-installed and pre-configured in qBraid Lab:

- [Launch qBraid Lab &rarr;](https://lab.qbraid.com/)
- [Make an account &rarr;](https://account.qbraid.com/)

For help, see qBraid Lab User Guide: [Getting Started](https://docs.qbraid.com/lab/user-guide/getting-started).

You can also install the qBraid-CLI from PyPI with:

```bash
pip install qbraid-cli
```

To manage qBraid [environments](https://docs.qbraid.com/lab/user-guide/environments) using the CLI, you must also install the `envs` extra:

```bash
pip install 'qbraid-cli[envs]'
```

## Local configuration

After installation, you must configure your account credentials to use the CLI locally:

1. Create a qBraid account or log in to your existing account by visiting
   [account.qbraid.com](https://account.qbraid.com/)
2. Copy your API Key token from the left side of
    your [account page](https://account.qbraid.com/):
3. Save your API key from step 2 in local [configuration file](https://docs.qbraid.com/cli/user-guide/config-files) `~/.qbraid/qbraidrc` using:

```bash
$ qbraid configure
```

For more on API keys, see [documentation](https://docs.qbraid.com/home/account#api-keys).

## Basic Commands

```bash
$ qbraid
----------------------------------
  * Welcome to the qBraid CLI! * 
----------------------------------

        ____            _     _  
   __ _| __ ) _ __ __ _(_) __| | 
  / _` |  _ \| '__/ _` | |/ _` | 
 | (_| | |_) | | | (_| | | (_| | 
  \__,_|____/|_|  \__,_|_|\__,_| 
     |_|                         


- Use 'qbraid --help' to see available commands.

- Use 'qbraid --version' to see the current version.

Reference Docs: https://docs.qbraid.com/cli/api-reference/qbraid
```

A qBraid CLI command has the following structure:

```bash
$ qbraid <command> <subcommand> [options and parameters]
```

For example, to list installed environments, the command would be:

```bash
$ qbraid envs list
```

To view help documentation, use one of the following:

```bash
$ qbraid --help
$ qbraid <command> --help
$ qbraid <command> <subcommand> --help
```

For example:

```bash
$ qbraid --help

Usage: qbraid [OPTIONS] COMMAND [ARGS]...

The qBraid CLI.

Options
  --version                     Show the version and exit.
  --install-completion          Install completion for the current shell.
  --show-completion             Show completion for the current shell, to copy it or customize the installation.
  --help                        Show this message and exit.

Commands
  account                       Manage qBraid account
  admin                         CI/CD commands for qBraid maintainers.
  configure                     Configure qBraid CLI options.
  account                       Manage qBraid account.
  chat                          Interact with qBraid AI chat service.
  devices                       Manage qBraid quantum devices.
  envs                          Manage qBraid environments.
  files                         Manage qBraid cloud storage files.
  jobs                          Manage qBraid quantum jobs.
  kernels                       Manage qBraid kernels.
  pip                           Run pip command in active qBraid environment.
```

To get the version of the qBraid CLI:

```bash
$ qbraid --version
```

## Magic Commands

You can also access the CLI directly from within [Notebooks](https://docs.qbraid.com/lab/user-guide/notebooks) using IPython [magic commands](https://ipython.readthedocs.io/en/stable/interactive/magics.html). First, configure the qBraid magic commands extension using:

```bash
$ qbraid configure magic
```

The above command can also be executed from within a Jupyter notebook using the ``!`` operator. Then, from within a notebook cell, load the qBraid magic IPython extension using:

```python
In [1]: %load_ext qbraid_magic
```

Now you can continue to use the qBraid-CLI as normal from within your Jupyter notebook using the magic ``%`` operator, e.g.

```python
In [2]: %qbraid chat -f code -p "Write a Qiskit bell circuit"
```
