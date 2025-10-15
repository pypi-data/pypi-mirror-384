# Disguise TestBroker Agent Communication Helper Library

A lib for interacting with the internal tool TB-Agent

[PyPi Page](https://pypi.org/project/d3-tb-agent-comms/)

## Usage

To use:

```
  from d3-tb-agent-comms import AgentHandler
```

Types can be imported as well:

```
  from d3-tb-agent-comms import AgentHandlerException, D3SystemInfo, MachineHealthInfo
```

## Development

To make packaging easier and also to move in general to faster and better tooling for python this project does not use venv or pip, instead it uses [uv by Astral](https://docs.astral.sh/uv/) (The maintainers of Ruff). 

### Steps to setup

Prerequisites

- [Git](https://git-scm.com/downloads/win)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Python](https://www.python.org/downloads/) 3.12 or newer

Steps

1. Clone the repo
2.
  ```
    uv sync
  ```

3. Done

## Updating PyPi package

Developers don't have to worry about building and uploading to PyPi, a GitHub Action takes care of this on any push to main
