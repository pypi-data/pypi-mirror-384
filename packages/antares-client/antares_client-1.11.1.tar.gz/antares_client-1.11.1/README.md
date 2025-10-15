# antares-client

A light-weight client for receiving alerts from
[ANTARES](http://antares.noirlab.edu).

ANTARES is an Alert Broker developed by the [NSF NOIRLab](http://noirlab.edu) for ZTF and
LSST.

The client is available for use as a Python library and as a command line tool.
Directions for both use cases follow in the [Usage](#usage) section.

Table of Contents:
* [Installation](#installation)
* [Documentation](#documentation)
* [Upgrading](#upgrading)
* [Troubleshooting](#troubleshooting)

## Installation

The ANTARES client supports Python versions 3.6 and up.

To install:

```bash
$ pip install antares-client
```

To install with kafka to use the StreamingClient:

```bash
$ pip install "antares-client[subscriptions]"
```

Verify the client installed correctly:

```bash
$ antares --version
antares, version v1.1.0
```

## Documentation

Visit the [full documentation](https://nsf-noirlab.gitlab.io/csdc/antares/client) for usage
guides, API reference docs, and more.

## Development

To install the development dependencies
```bash
pip install uv
uv sync --all-groups --all-extras
```

## Troubleshooting

Issues? See the
[documentation](https://nsf-noirlab.gitlab.io/csdc/antares/client/troubleshooting) for
common gotchas and, if you can't find a solution there, please open an issue.

