# elims

![PyPI](https://img.shields.io/pypi/v/elims.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/elims)
![License](https://img.shields.io/github/license/FabienMeyer/elims)
![CI](https://github.com/FabienMeyer/e-lims-d2xx/actions/workflows/ci.yml/badge.svg)
[![Codecov](https://codecov.io/gh/FabienMeyer/e-lims-d2xx/graph/badge.svg?token=xp3TKuNLKh)](https://codecov.io/gh/FabienMeyer/elims)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=FabienMeyer_elims&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=FabienMeyer_elims)
[![Documentation](https://img.shields.io/badge/GitHub-Pages-blue)](https://fabienmeyer.github.io/elims/)

# Testing tools

- uv run ruff check elims/ # Uses [tool.ruff]
- uv run mypy elims/ # Uses [tool.mypy]
- uv run mdformat docs/ # Uses [tool.mdformat]
- uv run vale

## Hooks

### Install hooks

- uv run pre-commit install

### Run on all files

- uv run pre-commit run --all-files
- uv run pre-commit run --files path/to/file.py
