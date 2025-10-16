# fakenode

A simulated [Autonomi](https://autonomi.com) node for testing node management software.

## What is fakenode?

fakenode provides a lightweight simulator that mimics the HTTP endpoints of an Autonomi node. It's designed for testing node management tools without running actual nodes, making development and testing faster and easier.

## Features

- Simulates `/metadata` and `/metrics` endpoints with realistic OpenMetrics format responses
- Configurable node version, peer ID, and performance metrics
- Creates node environment files (PID, peer-id, logs) for testing process management
- Lightweight Flask-based server with minimal dependencies
- Available as a Python package on PyPI

## Installation

```bash
pip install fakenode
```

## Quick Start

### Running directly with Python

```bash
# Run a simulated node on port 9090 using the fakenode command
fakenode \
  --metrics-server-port 9090 \
  --show-version "v0.4.4" \
  --root-dir /tmp/test-node \
  --create-files

# Or run as a Python module
python3 -m fakenode.server \
  --metrics-server-port 9090 \
  --show-version "v0.4.4" \
  --root-dir /tmp/test-node \
  --create-files
```

### Creating deployment scripts with fakeshell

For node management software that deploys nodes as executables, use `fakeshell` to generate shell script wrappers:

```bash
# Generate an executable script for a specific node version using the fakeshell command
fakeshell \
  --show-version "v0.4.4" \
  --output ./antnode

# Or run as a Python module
python3 -m fakenode.fakeshell \
  --show-version "v0.4.4" \
  --output ./antnode

# The generated script can now be used like a binary
./antnode \
  --metrics-server-port 9090 \
  --root-dir /tmp/test-node \
  --create-files
```

You can also customize the Python interpreter and enable file creation:

```bash
# Use a specific Python installation and enable file creation
fakeshell \
  --show-version "v0.5.0" \
  --python "/usr/local/bin/python3.11" \
  --create-files \
  --output ./antnode

# Or run as a Python module
python3 -m fakenode.fakeshell \
  --show-version "v0.5.0" \
  --python "/usr/local/bin/python3.11" \
  --create-files \
  --output ./antnode
```

The generated script contains editable variables for version, Python path, and file creation settings, allowing manual customization after generation.

**Note**: The `--create-files` option in fakeshell sets a variable in the generated script that controls whether the `--create-files` flag is passed to fakenode. This is a custom fakenode option not used by antctl or other node managers, so it must be configured either during script generation or by manually editing the `CREATE_FILES` variable in the generated script.

## Use Cases

- Testing node management software during development
- Automated testing of monitoring systems
- Simulating node behavior without resource overhead
- Development environments where running real nodes isn't practical

## Documentation

For detailed usage, API documentation, and all available command-line options, see [FAKENODE.md](FAKENODE.md).

## License

MIT
