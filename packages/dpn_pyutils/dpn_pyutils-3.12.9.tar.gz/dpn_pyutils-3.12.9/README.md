# DPN Python Utils

[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen.svg)](coverage.xml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A collection of python utils used by the DPN.

Target minimum python version: `3.12`

## Documentation and Examples

📚 **[Comprehensive Examples and Documentation](examples/README.md)**

Looking to get the most out of `dpn_pyutils`? Extensive documentation provides:

- **Detailed Module Guides**: In-depth explanations of each module's purpose and capabilities
- **Practical Code Examples**: Copy-pasteable examples showing real-world usage patterns
- **Architecture Insights**: Design decisions, best practices, and integration guidance
- **Getting Started**: Quick-start guides for both beginners and advanced users

Whether you're implementing CLI color formatting, secure token generation, robust file operations, powerful logging, or timezone-aware scheduling, examples will help you integrate `dpn_pyutils` effectively into your projects.

**Start here** → [examples/README.md](examples/README.md) for comprehensive usage guidance!

## High-level Design Notes

To be broadly compatible with running in synchronous or asynchronous mode.

The principles behind the modules are to:

- Be dependable and provide least surprise
- Fail safe and raise informative exceptions
- Optimize code for readability and maintainability
- Design for backwards compatibility

Major versions of dpn_pyutils releases track major Python versions in general
availability

## Getting Started

The fastest way to get start is with [Astral uv](https://docs.astral.sh/uv/).

_Otherwise, use `pip install dpn_pyutils` in your virtual environment._

With uv installed on the system, create an environment

```bash
uv init
uv add dpn_pyutils
uv sync
```

This will create a virtual environment with dpn_pyutils installed.

### Upgrade versions

Upgrading is done by uninstalling the package and installing the upgraded version

```bash
uv sync --upgrade-package dpn_pyutils
```

## Testing

This project uses `uv` and `tox` via the [`tox-uv`](https://github.com/tox-dev/tox-uv) plugin. Set it up via:

```bash
uv tool install tox --with tox-uv
```

## Building

Building dpn_pyutils can be done with python 3 and poetry

```bash
uv run pytest tests/
tox
uv build
```

The distribution-ready files will be in the `dist/` directory.

## Packaging and Distribution

Packaging after changes need the following to be executed:

### Update the version number

Bump the version number

- The MAJOR and MINOR versions should **always** match the minimum Python versions
- The PATCH version should be an incremental counter of library versions

```bash
uv lock
uv version --dry-run --bump patch
uv version --bump patch
git add pyproject.toml uv.lock
git commit -m "Bump version to $(uv version | awk '{print $2}')"
git tag "v$(uv version | awk '{print $2}')"
git push && git push --tags
```

### Distribute

```bash
uv build && uv publish && rm -rf dist
```

Remember to set the `username` to `__token__` and the `password` to your PyPI token.
