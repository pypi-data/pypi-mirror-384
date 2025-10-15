# Installation

This guide covers different ways to install Playfast.

## Requirements

- **Python**: 3.11 or higher (3.14 recommended for free-threading)
- **Operating System**: Linux, macOS, or Windows
- **Optional**: Rust 1.70+ (only for building from source)

## Install from PyPI

### Using UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a modern, extremely fast Python package manager:

```bash
uv pip install playfast
```

### Using pip

```bash
pip install playfast
```

### Using Poetry

```bash
poetry add playfast
```

### Using pipenv

```bash
pipenv install playfast
```

## Install from Source

For development or to get the latest unreleased changes:

```bash
# Clone the repository
git clone https://github.com/mixL1nk/playfast.git
cd playfast

# Set Python version (optional, for free-threading)
uv python pin 3.14t

# Install dependencies
uv sync --all-extras

# Build the Rust extension
uv run maturin develop --release
```

## Python 3.14 Free-Threading

For maximum performance, use Python 3.14 with free-threading enabled:

```bash
# Install Python 3.14t (free-threading build)
uv python install 3.14t

# Set it as the project Python version
uv python pin 3.14t

# Install playfast
uv pip install playfast
```

### Why Free-Threading?

Python 3.14's free-threading (PEP 703) removes the Global Interpreter Lock (GIL), allowing:

- True parallel execution of Python threads
- Better utilization of multi-core CPUs
- **3-10x performance improvement** for Playfast's workloads

## Verify Installation

```python
import playfast

print(f"Playfast version: {playfast.__version__}")
print(f"Free-threading: {playfast.is_free_threaded()}")
```

## Troubleshooting

### Windows: Microsoft Visual C++ Required

On Windows, you may need Microsoft Visual C++ 14.0 or greater:

1. Download [Build Tools for Visual Studio](https://visualstudio.microsoft.com/downloads/)
1. Install "Desktop development with C++"
1. Restart your terminal
1. Try installing again

### macOS: Command Line Tools

```bash
xcode-select --install
```

### Linux: Build Dependencies

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev pkg-config
```

#### Fedora/CentOS/RHEL

```bash
sudo dnf install gcc openssl-devel pkgconfig
```

#### Arch Linux

```bash
sudo pacman -S base-devel openssl
```

### Import Error After Installation

If you get `ModuleNotFoundError`:

```bash
# Check if playfast is installed
python -m pip list | grep playfast

# Check Python environment
which python
python --version

# Reinstall
pip uninstall playfast
pip install playfast
```

### Build Errors from Source

If building from source fails:

1. Ensure Rust is installed:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustc --version
```

2. Update Rust:

```bash
rustup update
```

3. Clean and rebuild:

```bash
cargo clean
uv run maturin develop --release
```

## Upgrading

```bash
# UV
uv pip install --upgrade playfast

# pip
pip install --upgrade playfast
```

## Uninstalling

```bash
# UV
uv pip uninstall playfast

# pip
pip uninstall playfast
```

## Next Steps

- [Getting Started](getting_started.md) - First steps with Playfast
- [Quick Start](quick_start.md) - Jump right in
- [User Guide](guides/overview.md) - Comprehensive documentation
