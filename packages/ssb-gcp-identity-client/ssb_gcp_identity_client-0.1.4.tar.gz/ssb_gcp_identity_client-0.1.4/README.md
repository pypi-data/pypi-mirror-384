# SSB GCP Identity Client

[![PyPI](https://img.shields.io/pypi/v/ssb-gcp-identity-client.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-gcp-identity-client.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-gcp-identity-client)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-gcp-identity-client)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-gcp-identity-client/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-gcp-identity-client/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-gcp-identity-client&metric=coverage&token=2cda1160a6f9af5fe5de964c00333f95a5d0efcb)](https://sonarcloud.io/summary/new_code?id=statisticsnorway_ssb-gcp-identity-client)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-gcp-identity-client&metric=alert_status&token=2cda1160a6f9af5fe5de964c00333f95a5d0efcb)](https://sonarcloud.io/summary/new_code?id=statisticsnorway_ssb-gcp-identity-client)

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-gcp-identity-client/
[documentation]: https://statisticsnorway.github.io/ssb-gcp-identity-client
[tests]: https://github.com/statisticsnorway/ssb-gcp-identity-client/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-gcp-identity-client
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-gcp-identity-client
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

A Python library for creating Google Cloud clients using Workload Identity Federation with Maskinporten-issued tokens.

## Features

- Create federated GCP storage client with Maskinporten-token.

## Requirements

- Python 3.10+
- Google Cloud SDK libraries (google-auth, google-cloud-storage)
- Maskinporten token (for authentication)
- Poetry (for development / building docs)

## Installation

You can install _SSB GCP Identity Client_ via [pip] from [PyPI]:

```console
pip install ssb-gcp-identity-client
```

## Usage

Please see the [Reference Guide] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_SSB GCP Identity Client_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/ssb-gcp-identity-client/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-gcp-identity-client/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/ssb-gcp-identity-client/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-gcp-identity-client/reference.html
