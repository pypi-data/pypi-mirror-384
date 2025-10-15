# Agent Jupyter Toolkit

A Python toolkit for building agent tools that interact with Jupyter kernels and the Jupyter protocol. This package provides high-level wrappers and abstractions around [jupyter_client](https://pypi.org/project/jupyter-client/), making it easy to manage kernels, execute code, and build agent-driven workflows for automation, orchestration, and integration with Model Context Protocol (MCP) servers.

## Features
- High-level, async-friendly wrappers for Jupyter kernel management and code execution
- Session and variable management for agent tools
- Designed for use in agent toolkits, automation, and MCP server backends
- Extensible hooks and integration points for custom workflows

## Use Cases
- Build agent tools that execute code in Jupyter kernels
- Integrate Jupyter kernel execution into MCP servers or other orchestration systems
- Automate notebook and code execution for data science, ML, and automation pipelines

## Installation

You can install the package and its dependencies from PyPI or set up a development environment using pip or [uv](https://github.com/astral-sh/uv).

### Install from PyPI

```sh
# Using pip
pip install agent-jupyter-toolkit

# Or using uv
uv pip install agent-jupyter-toolkit
```

### Environment Setup

### Development Environment (contributors)

#### Option 1: Using pip

```sh
# Create a virtual environment (Python 3.10+ recommended)
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the package in editable mode with dev dependencies
pip install -e '.[dev]'
```

#### Option 2: Using uv

```sh
# Create and activate a virtual environment
uv venv .venv
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
uv pip install '.[dev]'
```

## Configuration

- All configuration is managed via `pyproject.toml`.
- Development dependencies and test tools are specified in the `[project.optional-dependencies]` section.
- See `tox.ini` for test and linting environments.

## Reference: jupyter_client

[jupyter_client](https://pypi.org/project/jupyter-client/) is the reference implementation of the Jupyter protocol, providing client and kernel management APIs. This toolkit builds on top of jupyter_client to provide a more ergonomic, agent-oriented interface for automation and integration.

## Project Goals

- Define reusable components and abstractions for agent tools that interact with Jupyter kernels
- Enable both direct use in agent toolkits and integration as part of an MCP server
- Provide a robust, modern, and extensible foundation for agent-driven Jupyter workflows


## Release Process

To publish a new release to PyPI:

1. Ensure all changes are committed and tests pass:
    ```sh
    uv run pytest
    ```

2. Create and push an **annotated tag** for the release:
    ```sh
    git tag -a v0.1.2 -m "Release 0.1.2"
    git push origin v0.1.2
    ```

3. Checkout the tag to ensure you are building exactly from it:
    ```sh
    git checkout v0.1.2
    ```

4. Clean old build artifacts:
    ```sh
    rm -rf dist
    rm -rf build
    rm -rf src/*.egg-info
    ``` 

5. Upgrade build and upload tools:
    ```sh
    uv pip install --upgrade build twine packaging setuptools wheel setuptools_scm
    ```

6. Build the package:
    ```sh
    uv run python -m build
    ```

7. (Optional) Check metadata:
    ```sh
    uv run twine check dist/*
    ```

8. Upload to PyPI:
    ```sh
    uv run twine upload dist/*
    ```

**Notes:**
* Twine ≥ 6 and packaging ≥ 24.2 are required for modern metadata support.
* Always build from the tag (`git checkout vX.Y.Z`) so setuptools_scm resolves the exact version.
* `git checkout v0.1.2` puts you in detached HEAD mode; that’s normal. When done, return to your branch with:
    ```sh
    git switch -
    ```
* If you’re building in CI, make sure tags are fetched:
    ```sh
    git fetch --tags --force --prune
    git fetch --unshallow || true
    ```

---

See the `tests/` directory for usage examples and test coverage.  
Contributions and feedback are welcome!

## Fix Ruff

```bash
uv venv .venv
source .venv/bin/activate

# install your package in editable mode with dev tools
uv pip install -e ".[dev]"

# ruff: lint + fix
ruff check src tests --fix

# black: format
black src tests
```