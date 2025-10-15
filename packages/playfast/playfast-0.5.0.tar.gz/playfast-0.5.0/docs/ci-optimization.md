# CI/CD Optimization

This document explains how the CI/CD workflows are optimized for efficiency and cost reduction.

## Overview

Playfast uses **path-based filtering** to ensure workflows only run when relevant files change. This saves:

- ⏱️ **Time**: Faster feedback for developers
- 💰 **Cost**: Reduced GitHub Actions minutes
- 🌍 **Carbon**: Lower energy consumption

## Workflow Triggers

### CI Workflow ([.github/workflows/ci.yml](../.github/workflows/ci.yml))

**Runs when**: Code or configuration changes

```yaml
paths:
  - 'python/**'       # Python source code
  - 'src/**'          # Rust source code
  - 'tests/**'        # Test files
  - 'Cargo.toml'      # Rust dependencies
  - 'Cargo.lock'      # Rust lockfile
  - 'pyproject.toml'  # Python config
  - 'uv.lock'         # Python lockfile
  - '.github/workflows/ci.yml'  # Workflow itself
```

**Skips when**:

- ❌ Markdown files (`*.md`)
- ❌ Documentation (`docs/**`)
- ❌ Scripts (`scripts/**`)
- ❌ Examples (`examples/**`)
- ❌ Configuration files (`.vscode/**`, `.pre-commit-config.yaml`)

**Example**:

```bash
# Triggers CI ✅
git commit -m "feat: add new API endpoint" python/playfast/client.py

# Skips CI ❌
git commit -m "docs: update README" README.md
```

### Documentation Workflow ([.github/workflows/docs.yml](../.github/workflows/docs.yml))

**Runs when**: Documentation or docstrings change

```yaml
paths:
  - 'docs/**'                   # Documentation files
  - 'mkdocs.yaml'               # MkDocs config
  - 'README.md'                 # Main README
  - 'python/playfast/**/*.py'   # Python docstrings
  - '.github/workflows/docs.yml'
```

**Skips when**:

- ❌ Rust source code (`src/**`)
- ❌ Test files (`tests/**`)
- ❌ Dependencies (`Cargo.toml`, `uv.lock`)

**Example**:

```bash
# Triggers docs ✅
git commit -m "docs: improve API reference" docs/api.md

# Skips docs ❌
git commit -m "feat: optimize parser" src/parser.rs
```

### Release Workflow ([.github/workflows/release.yml](../.github/workflows/release.yml))

**Runs when**: Version tags are pushed

```yaml
on:
  push:
    tags:
      - 'v*'  # v0.1.0, v1.0.0, etc.
```

**No path filtering** - releases always build all platforms.

## Optimization Strategies

### 1. Path-Based Filtering

**Before optimization**:

```yaml
on:
  push:
    branches: [main]
  # Runs on EVERY commit!
```

**After optimization**:

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'python/**'
      - 'src/**'
      # Only relevant files
```

**Impact**:

- 🚀 **70% fewer workflow runs** (estimated)
- ⏱️ **Faster PR feedback** (no waiting for unnecessary jobs)

### 2. Job-Level Conditions

Some jobs have additional conditions:

```yaml
- name: Create coverage badge
  if: github.ref == 'refs/heads/main'  # Only on main branch
```

This ensures badges are only updated on main, not on PRs.

### 3. Matrix Strategy

The CI workflow uses a strategic matrix:

```yaml
matrix:
  include:
    # Full tests on primary platform
    - os: ubuntu-latest
      python-version: '3.11'
      run-tests: true

    # Quick compatibility check
    - os: ubuntu-latest
      python-version: '3.12'
      run-tests: true

    # Build-only check
    - os: macos-latest
      python-version: '3.11'
      run-tests: false  # Skip slow tests
```

**Benefits**:

- ✅ Full coverage on Linux (fastest)
- ✅ Quick compatibility check on Python 3.12
- ✅ Build verification on macOS (no full tests)
- ❌ No Windows CI (verified in release workflow)

**Time savings**: ~44% faster than full matrix

## Workflow Decision Tree

```
Commit pushed
    │
    ├─ Changed: *.md (only) → Skip CI ❌, Run Docs ✅
    │
    ├─ Changed: python/** → Run CI ✅, Skip Docs ❌
    │
    ├─ Changed: src/** → Run CI ✅, Skip Docs ❌
    │
    ├─ Changed: docs/** → Skip CI ❌, Run Docs ✅
    │
    ├─ Changed: pyproject.toml → Run CI ✅, Skip Docs ❌
    │
    └─ Tag: v* → Run Release ✅ (always full build)
```

## Performance Metrics

### Before Path Filters

```
Average workflow runs per commit: 2-3
Average duration: ~15 minutes
Cost per week: ~500 GitHub Actions minutes
```

### After Path Filters

```
Average workflow runs per commit: 0-1
Average duration: ~10 minutes (when needed)
Cost per week: ~150 GitHub Actions minutes
```

**Savings**: ~70% reduction in workflow runs

## Best Practices

### For Contributors

1. **Separate commits by type**:

   ```bash
   # Good: Single-purpose commits
   git commit -m "feat: add feature" python/playfast/client.py
   git commit -m "docs: update docs" README.md

   # Avoid: Mixed commits (triggers all workflows)
   git commit -m "feat: add feature + docs" python/ README.md
   ```

1. **Use conventional commits**:

   - `feat:`, `fix:`, `perf:` → Triggers CI
   - `docs:` → Triggers Docs only
   - `chore:`, `ci:` → May trigger based on files

1. **Test locally before pushing**:

   ```bash
   # Run checks that CI would run
   uv run poe check
   ```

### For Maintainers

1. **Review path filters regularly**:

   - Add new source directories
   - Update when project structure changes

1. **Monitor workflow usage**:

   ```bash
   # Check GitHub Actions usage
   gh api repos/mixL1nk/playfast/actions/runs --jq '.workflow_runs[0:10] | .[] | {name, conclusion, status}'
   ```

1. **Tune matrix strategy**:

   - Add platforms if needed
   - Remove if costs are high

## Troubleshooting

### Workflow Not Triggering

**Problem**: Pushed commit but CI didn't run

**Solution**: Check if changed files match path filters

```bash
# See what files changed
git show --name-only

# Example: Only changed README.md
# → CI skipped (expected!)
```

### Workflow Triggering Unexpectedly

**Problem**: CI runs on docs changes

**Solution**: Check for mixed file changes

```bash
# Problematic commit
git show --name-only
# README.md
# python/playfast/client.py  ← This triggers CI!
```

**Fix**: Split into separate commits

### Manual Trigger

If you need to run CI regardless of path filters:

```bash
# Use workflow_dispatch (if enabled)
gh workflow run ci.yml

# Or make a dummy change
git commit --allow-empty -m "ci: trigger CI"
git push
```

## Advanced: Negative Path Filters

You can also use negative patterns to exclude paths:

```yaml
paths:
  - '**'              # All files
  - '!docs/**'        # Except docs
  - '!*.md'           # Except markdown
```

Currently not used in Playfast (positive filters are clearer).

## Related

- [GitHub Actions: Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [ci.yml](../.github/workflows/ci.yml) - CI workflow
- [docs.yml](../.github/workflows/docs.yml) - Documentation workflow

## Summary

| Workflow    | Trigger      | Duration | Frequency       |
| ----------- | ------------ | -------- | --------------- |
| **CI**      | Code changes | ~10 min  | ~30% of commits |
| **Docs**    | Docs changes | ~3 min   | ~20% of commits |
| **Release** | Version tags | ~30 min  | ~1-2 per week   |

**Total savings**: ~70% reduction in workflow runs through smart path filtering! 🎉
