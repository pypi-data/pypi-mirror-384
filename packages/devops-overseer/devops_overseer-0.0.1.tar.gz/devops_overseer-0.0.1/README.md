# devops.overseer

A DevOps helper python module to monitor and automate all kinds of tasks related to either process, migrations, reporting, monitoring etc.

# Installation

Clone the repository and `cd ` into it.

## Virtual environment

Make sure you have `vevn` installed (example on Ubuntu: `sudo apt install python3-venv`).
From the root of the repository, if you don't have another preference onto where to get the venv, just create it here:

`python3 -v venv ./.venv`

> INFO: The `venv` directory is ignored at the root.

## Requirements

Just install both requirements file in your virtual environment to make sure you have access to all the processes:

```
pip install -r ./requirements.dev.txt
pip install -r ./requirements.txt
```

## Building

You can simply build the package after pip installing both requirements file using this command:

`python3 -m build`

## Installation

### Locally

just run the usual pip install:

`pip install .`

## Calling the CLI

You should now be able to just call `devops-overseer` from your current shell while having your virtual environment activated

# Contributing

## Commiting

This repository tries to follow as best as it cana the [conventional commits specification](https://www.conventionalcommits.org).
The accepted types for commit messages are:
- feat
- fix
- docs
- style
- refactor
- perf
- test
- build
- ci
- chore
- revert

## Commands

* `devops-overseer` - CLI call (parameters will come).

## Project layout

    mkdocs.yml    # The configuration file.
    docs/         # mkdocs documentation
    src/          # main source directory
    tests/        # unit tests directory

# Full documentation

You can find the full documentation [here](https://mot0ko.github.io/devops.overseer/)
