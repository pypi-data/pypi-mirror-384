# Pre-commit Hooks Strategy

This document explains the pre-commit hooks configuration for Playfast.

## Overview

We use a **multi-stage hook strategy** to balance code quality and developer productivity:

1. **Pre-commit (Fast)**: Auto-fix formatting and linting
1. **Pre-push (Comprehensive)**: Type-checking and tests
1. **Manual (Full)**: Complete validation before release

## Hook Stages

### Stage 1: Pre-commit (Every Commit) ⚡

**Goal**: Keep code formatted and catch obvious errors

**Hooks**:

- ✅ **Ruff Format** - Auto-format Python code
- ✅ **Ruff Lint** - Auto-fix linting issues
- ✅ **mdformat** - Format Markdown files
- ✅ **markdownlint** - Lint Markdown files
- ✅ **uv lock** - Update lockfile if pyproject.toml changed

**Speed**: ~2-5 seconds

**Behavior**:

- Automatically fixes most issues
- Fails only if auto-fix isn't possible
- Skippable with `git commit --no-verify` (not recommended)

### Stage 2: Pre-push (Before Push) 🧪

**Goal**: Ensure code quality before sharing

**Hooks**:

- ✅ **All pre-commit checks**
- ✅ **Pyright** - Static type checking
- ✅ **Mypy** - Additional type validation
- ✅ **Pytest** - Run test suite

**Speed**: ~30-60 seconds (depends on test suite)

**Behavior**:

- Runs automatically before `git push`
- Catches type errors and test failures
- Prevents pushing broken code

### Stage 3: Manual (Release/Review) 🔍

**Goal**: Complete validation before release

**Command**:

```bash
uv run pre-commit run --hook-stage manual --all-files
```

**Includes**:

- All checks from pre-commit and pre-push
- Additional custom validations
- Full project scan

## Configuration Summary

```yaml
# .pre-commit-config.yaml

# Fast checks (every commit)
- ruff-format: Auto-format Python
- ruff-lint: Auto-fix linting
- mdformat: Format Markdown
- uv-lock: Update lockfile

# Comprehensive checks (pre-push)
- poe-check-full: Run full test suite
  stages: [manual, push]
```

## Usage Examples

### Normal Development

```bash
# Make changes
vim python/playfast/client.py

# Commit (pre-commit hooks auto-run)
git add .
git commit -m "feat: add new feature"

# Hooks will:
# 1. Format your code
# 2. Fix linting issues
# 3. Update lockfile if needed
# 4. Fail if unfixable issues exist

# Push (pre-push hooks auto-run)
git push origin main

# Hooks will:
# 1. Run all pre-commit checks
# 2. Run type checking (pyright, mypy)
# 3. Run tests (pytest)
# 4. Fail if any check fails
```

### Skip Hooks (Emergency Only)

```bash
# Skip pre-commit (not recommended)
git commit --no-verify -m "WIP: emergency fix"

# Skip pre-push (not recommended)
git push --no-verify
```

### Manual Full Check

```bash
# Before creating PR or release
uv run pre-commit run --hook-stage manual --all-files

# Or use poe task
uv run poe check
```

## Release Workflow Integration

The release workflow automatically:

1. **Skips uv-lock** during semantic-release (uses `SKIP=uv-lock`)
1. **Runs formatters** after changelog generation
1. **Amends commit** with formatting changes
1. **Moves tag** to final commit

See [release-workflow.md](release-workflow.md) for details.

## Troubleshooting

### Hook Fails: "Ruff Format"

**Cause**: Code has formatting issues that couldn't be auto-fixed

**Solution**:

```bash
# Run formatter manually
uv run ruff format python/

# Check for syntax errors
uv run ruff check python/

# Try committing again
git add .
git commit -m "fix: resolve formatting"
```

### Hook Fails: "Ruff Lint"

**Cause**: Linting issues that require manual intervention

**Solution**:

```bash
# See what needs fixing
uv run ruff check python/

# Try auto-fix
uv run ruff check --fix python/

# Manual fix if needed
vim python/playfast/client.py

# Commit again
git add .
git commit -m "fix: resolve linting issues"
```

### Hook Fails: "uv lock"

**Cause**: pyproject.toml changed but lockfile not updated

**Solution**:

```bash
# Update lockfile manually
uv lock

# Commit with updated lockfile
git add uv.lock
git commit -m "chore: update lockfile"
```

### Pre-push Fails: Type Errors

**Cause**: Type checking found issues

**Solution**:

```bash
# Run type checker locally
uv run pyright
uv run mypy python/

# Fix type errors
vim python/playfast/client.py

# Try pushing again
git push
```

### Pre-push Fails: Tests

**Cause**: Test failures

**Solution**:

```bash
# Run tests locally
uv run pytest

# Fix failing tests
vim tests/test_client.py

# Try pushing again
git push
```

### Pre-push Too Slow

If pre-push hooks are too slow, you can:

**Option 1**: Skip specific tests

```bash
# In pyproject.toml, modify pre-commit-check:
pre-commit-check = ["fmt", "lint", "pyright"]  # Remove "test"
```

**Option 2**: Use pytest markers

```bash
# Run only fast tests in hook
# In .pre-commit-config.yaml:
entry: uv run pytest -m "not slow"
```

**Option 3**: Disable pre-push locally

```bash
# Remove pre-push hook
rm .git/hooks/pre-push

# Push without checks (your responsibility!)
git push
```

## Best Practices

### ✅ Do

1. **Let hooks auto-fix** - Commit, let hooks run, review changes, commit again
1. **Run checks before push** - `uv run poe check` before important pushes
1. **Keep tests fast** - Mark slow tests with `@pytest.mark.slow`
1. **Update hooks regularly** - `uv run pre-commit autoupdate`

### ❌ Don't

1. **Don't skip hooks regularly** - They catch bugs early
1. **Don't commit broken code** - Fix issues before committing
1. **Don't disable all checks** - Balance speed and quality
1. **Don't ignore type errors** - They often indicate real bugs

## Performance Tips

### Speed Up Ruff

Ruff is already fast, but you can cache results:

```bash
# Ruff uses automatic caching
# Just ensure .ruff_cache/ is in .gitignore
```

### Speed Up Tests

```bash
# Use pytest-xdist for parallel tests
uv add --dev pytest-xdist

# Run tests in parallel
uv run pytest -n auto
```

### Speed Up Type Checking

```bash
# Pyright is fast, but you can limit scope
# In pyproject.toml:
[tool.pyright]
include = ["python"]  # Only check main code
exclude = ["tests", "examples"]  # Skip non-critical
```

## Comparison with CI

| Check        | Pre-commit  | Pre-push      | CI                |
| ------------ | ----------- | ------------- | ----------------- |
| Ruff Format  | ✅ Auto-fix | ✅ Verify     | ✅ Verify         |
| Ruff Lint    | ✅ Auto-fix | ✅ Verify     | ✅ Verify         |
| Pyright      | ❌          | ✅ Run        | ✅ Run            |
| Mypy         | ❌          | ✅ Run        | ✅ Run            |
| Pytest       | ❌          | ✅ Fast tests | ✅ Full suite     |
| Coverage     | ❌          | ❌            | ✅ With report    |
| Build Wheels | ❌          | ❌            | ✅ Multi-platform |

**Philosophy**:

- **Pre-commit**: Fast feedback loop
- **Pre-push**: Quality gate
- **CI**: Comprehensive validation + deployment

## See Also

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [release-workflow.md](release-workflow.md) - Release process
- [pre-commit documentation](https://pre-commit.com/)
