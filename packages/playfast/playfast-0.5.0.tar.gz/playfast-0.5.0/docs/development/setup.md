# Development Setup

Complete guide for setting up your Playfast development environment.

## Requirements

### Essential

- **Python 3.11+** (Python 3.14t recommended for free-threading)
- **Rust 1.70+**
- **UV** (package manager)

### Optional

- **Git** (version control)
- **Visual Studio Code** (recommended editor)
- **Docker** (for testing in different environments)

## Installation

### 1. Install Rust

```bash
# Linux/macOS
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Windows
# Download from https://rustup.rs/

# Verify installation
rustc --version
cargo --version
```

### 2. Install UV

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Verify installation
uv --version
```

### 3. Clone Repository

```bash
git clone https://github.com/mixL1nk/playfast.git
cd playfast
```

### 4. Set Up Python Environment

```bash
# Use Python 3.14t (free-threading build) for best performance
uv python install 3.14t
uv python pin 3.14t

# Or use standard Python 3.11+
uv python pin 3.12
```

### 5. Install Dependencies

```bash
# Install all dependencies including dev tools
uv sync

# This installs:
# - Python packages (aiohttp, pydantic, pytest, etc.)
# - Development tools (ruff, mypy, pyright)
# - Documentation tools (mkdocs, mkdocstrings)
```

### 6. Build Rust Extension

```bash
# Development build (faster compilation, slower runtime)
uv run maturin develop

# Release build (slower compilation, faster runtime)
uv run maturin develop --release
```

### 7. Verify Installation

```bash
# Run tests
uv run pytest

# Should see output like:
# ===== 161 passed, 23 skipped in 2.34s =====
```

## Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes to code

# 4. Rebuild Rust (if you edited Rust code)
uv run maturin develop

# 5. Run tests
uv run pytest

# 6. Format and lint
uv run ruff format
uv run ruff check python/
cargo fmt
cargo clippy

# 7. Commit changes
git add .
git commit -m "feat: add my feature"

# 8. Push to your fork
git push origin feature/my-feature
```

### Common Commands

```bash
# Python development
uv run pytest                    # Run tests
uv run pytest --cov=playfast    # With coverage
uv run ruff format               # Format code
uv run ruff check python/        # Lint code
uv run mypy python/              # Type check
uv run pyright                   # Type check (stricter)

# Rust development
cargo fmt                        # Format Rust code
cargo clippy                     # Lint Rust code
cargo test                       # Run Rust tests
cargo build --release            # Build optimized

# Documentation
uv run mkdocs serve              # Preview docs locally
uv run mkdocs build              # Build docs

# Quick tasks (using poe)
uv run poe install               # Reinstall dependencies
uv run poe fmt                   # Format all code
uv run poe lint                  # Lint all code
uv run poe fix                   # Auto-fix lint issues
```

## IDE Setup

### Visual Studio Code

Recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "rust-lang.rust-analyzer",
    "tamasfe.even-better-toml",
    "ms-vscode.cpptools"
  ]
}
```

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "python.linting.enabled": false,
  "ruff.enable": true,
  "ruff.lint.run": "onSave",
  "ruff.format.args": ["--config", "pyproject.toml"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  },
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer",
    "editor.formatOnSave": true
  },
  "rust-analyzer.cargo.features": "all",
  "rust-analyzer.checkOnSave.command": "clippy"
}
```

### PyCharm

1. Open project in PyCharm
1. Set Python interpreter to `.venv/bin/python`
1. Install Rust plugin
1. Configure Ruff:
   - Preferences → Tools → Ruff
   - Enable "Run ruff on save"

## Troubleshooting

### Rust Compilation Errors

**Issue**: `error: linker 'cc' not found`

**Solution**:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

### Python Import Errors

**Issue**: `ModuleNotFoundError: No module named 'playfast'`

**Solution**:

```bash
# Rebuild Rust extension
uv run maturin develop --release

# Verify installation
uv run python -c "import playfast; print(playfast.__version__)"
```

### UV Issues

**Issue**: `uv` command not found

**Solution**:

```bash
# Ensure UV is in PATH
export PATH="$HOME/.cargo/bin:$PATH"  # Linux/macOS
# Or restart terminal after installation
```

### Test Failures

**Issue**: Tests fail with network errors

**Solution**:

```bash
# Skip integration tests
uv run pytest -m "not integration"

# Run with verbose output
uv run pytest -v
```

### Maturin Build Fails

**Issue**: `error: failed to run custom build command for 'pyo3-ffi'`

**Solution**:

```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
uv run maturin develop --release
```

## Platform-Specific Notes

### Windows

- Use PowerShell or Windows Terminal (not CMD)
- Some commands may need Admin privileges
- Path separators use backslash: `python\playfast\client.py`

### macOS (Apple Silicon)

- Use Rosetta if needed: `arch -x86_64 uv run maturin develop`
- May need to install Command Line Tools: `xcode-select --install`

### Linux

- Install build dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev pkg-config python3-dev

# Fedora/RHEL
sudo dnf install gcc openssl-devel pkgconfig python3-devel

# Arch
sudo pacman -S base-devel openssl python
```

## Next Steps

- [Contributing Guide](contributing.md) - Learn how to contribute
- [Testing](testing.md) - Write and run tests
- [Architecture](architecture.md) - Understand the codebase
- [Benchmarking](benchmarking.md) - Measure performance
