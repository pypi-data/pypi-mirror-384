# pvenv: Easy python virtual environment management

[![build][build_badge]][build_url]
[![lint][lint_badge]][lint_url]
[![tests][tests_badge]][tests_url]
[![license][licence_badge]][licence_url]
[![codecov][codecov_badge]][codecov_url]
[![readthedocs][readthedocs_badge]][readthedocs_url]
[![pypi][pypi_badge]][pypi_url]
[![downloads][pepy_badge]][pepy_url]
[![build automation: yam][yam_badge]][yam_url]
[![Lint: ruff][ruff_badge]][ruff_url]

`pvenv` provides an easy way to use virtual environments in python.

Behind the scenes, it uses [uv] to create virtual environments extremely fast. Also, it is inspired from
[virtualenvwrapper] to move virtual environments outside the directory, and cd to the project directory
upon activation.

## Links

- [Documentation]
- [Changelog]

[build_badge]: https://github.com/spapanik/pvenv/actions/workflows/build.yml/badge.svg
[build_url]: https://github.com/spapanik/pvenv/actions/workflows/build.yml
[lint_badge]: https://github.com/spapanik/pvenv/actions/workflows/lint.yml/badge.svg
[lint_url]: https://github.com/spapanik/pvenv/actions/workflows/lint.yml
[tests_badge]: https://github.com/spapanik/pvenv/actions/workflows/tests.yml/badge.svg
[tests_url]: https://github.com/spapanik/pvenv/actions/workflows/tests.yml
[licence_badge]: https://img.shields.io/pypi/l/pvenv
[licence_url]: https://p-venv.readthedocs.io/en/stable/LICENSE/
[codecov_badge]: https://codecov.io/github/spapanik/pvenv/graph/badge.svg?token=Q20F84BW72
[codecov_url]: https://codecov.io/github/spapanik/pvenv
[readthedocs_badge]: https://readthedocs.org/projects/p-venv/badge/?version=latest
[readthedocs_url]: https://p-venv.readthedocs.io/en/latest/
[pypi_badge]: https://img.shields.io/pypi/v/pvenv
[pypi_url]: https://pypi.org/project/pvenv
[pepy_badge]: https://pepy.tech/badge/pvenv
[pepy_url]: https://pepy.tech/project/pvenv
[yam_badge]: https://img.shields.io/badge/build%20automation-yamk-success
[yam_url]: https://github.com/spapanik/yamk
[ruff_badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
[ruff_url]: https://github.com/charliermarsh/ruff
[uv]: https://docs.astral.sh/uv/
[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.io/en/stable/
[Documentation]: https://p-venv.readthedocs.io/en/stable/
[Changelog]: https://p-venv.readthedocs.io/en/stable/CHANGELOG/
