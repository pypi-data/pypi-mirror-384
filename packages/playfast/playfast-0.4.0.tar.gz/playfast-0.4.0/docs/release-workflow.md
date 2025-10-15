# Release Workflow

This document describes the release process for Playfast.

## Overview

The release process is automated using:

- **semantic-release**: Version bumping based on conventional commits
- **git-cliff**: Changelog generation
- **Custom scripts**: Finalizing commits with formatters

## Release Commands

### Local Release (Recommended)

```bash
# Create a release locally (no push)
uv run poe release
```

This command:

1. ✅ Runs `semantic-release version --no-push` to bump version and create tag
1. ✅ Generates changelogs (`CHANGELOG.md` and `docs/changelog.md`)
1. ✅ Amends the commit with changelog files
1. ✅ Runs formatters (mdformat, etc.)
1. ✅ Amends again if formatters modified files
1. ✅ Moves tag to final commit (if needed)

**Output**:

```
✓ Release finalized: 7c9b7cf chore(release): 0.3.2
✓ Tag: v0.3.2

Next steps:
  git push origin main
  git push origin v0.3.2
```

Then manually push:

```bash
git push origin main
git push origin v0.3.2
```

### Check Next Version

```bash
# Preview what the next version will be
uv run poe version_check
```

## How It Works

### Problem: Tag and Commit Mismatch

Previously, this workflow had an issue:

```
1. semantic-release creates commit + tag
   Commit A (tagged v0.3.2): chore(release): 0.3.2

2. User runs: git commit --amend --no-edit
   Pre-commit hooks run (mdformat modifies files)

3. Result:
   Commit A (tagged v0.3.2): chore(release): 0.3.2
   Commit B (HEAD): chore(release): 0.3.2  [with formatted files]

   ❌ Tag points to old commit!
```

### Solution: Automatic Tag Movement

The `finalize_release.py` script detects this situation and automatically moves the tag:

```python
# Check if previous commit has a tag
if tag_on_previous_commit:
    # Delete old tag
    git tag -d v0.3.2
    # Create tag on current commit
    git tag v0.3.2
```

Now the workflow is:

```
1. semantic-release creates commit + tag
2. finalize_release.py:
   - Amends commit with changelogs
   - Runs formatters
   - Amends again if needed
   - Moves tag to final commit

3. Result:
   Commit B (tagged v0.3.2, HEAD): chore(release): 0.3.2  [finalized]

   ✅ Tag and HEAD match!
```

## Conventional Commits

Releases are triggered by commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Version Bumps

| Commit Type | Version Bump          | Example                      |
| ----------- | --------------------- | ---------------------------- |
| `feat:`     | Minor (0.1.0 → 0.2.0) | `feat: add batch API`        |
| `fix:`      | Patch (0.1.0 → 0.1.1) | `fix: handle timeout errors` |
| `perf:`     | Patch                 | `perf: optimize parser`      |
| `refactor:` | Patch                 | `refactor: simplify client`  |
| `chore:`    | Patch                 | `chore: update dependencies` |
| `docs:`     | Patch                 | `docs: add examples`         |
| `ci:`       | Patch                 | `ci: add release workflow`   |

### Breaking Changes

Add `BREAKING CHANGE:` in the commit body to trigger a major version bump:

```
feat!: redesign API

BREAKING CHANGE: The client API has been completely redesigned.
Old code using `Client()` must be updated to `AsyncClient()`.
```

This will bump: `0.3.2` → `1.0.0`

## CI/CD Integration

When you push a tag, GitHub Actions automatically:

1. **Build wheels** for Linux, macOS, Windows
1. **Build sdist**
1. **Publish to PyPI**
1. **Create GitHub Release** with auto-generated notes

See [.github/workflows/release.yml](../.github/workflows/release.yml) for details.

## Troubleshooting

### Tag on Wrong Commit

If you already pushed and the tag is on the wrong commit:

```bash
# Delete remote tag
git push origin :refs/tags/v0.3.2

# Delete local tag
git tag -d v0.3.2

# Create tag on correct commit
git tag v0.3.2

# Push tag
git push origin v0.3.2
```

### Pre-commit Hooks Failing

If pre-commit hooks are blocking your release:

```bash
# Skip hooks (not recommended)
SKIP=uv-lock git commit --amend --no-edit

# Or fix issues and try again
uv run pre-commit run --all-files
git add -A
git commit --amend --no-edit
```

### Version Not Bumping

Check commit messages:

```bash
# See what version would be bumped
uv run poe version_check

# See recent commits
git log --oneline -10
```

If no version bump is detected, ensure commits follow conventional format:

- ✅ `feat: add feature`
- ✅ `fix: fix bug`
- ❌ `Add feature` (missing type)
- ❌ `feat add feature` (missing colon)

## Manual Version Bump

If you need to manually set a version:

```bash
# Edit version in pyproject.toml
# [project]
# version = "0.4.0"

# Commit
git add pyproject.toml
git commit -m "chore(release): 0.4.0"

# Create tag
git tag v0.4.0

# Push
git push origin main v0.4.0
```

## Best Practices

1. **Always use `uv run poe release`** for local releases

   - Ensures consistent process
   - Automatically handles formatting
   - Moves tags correctly

1. **Review changes before pushing**

   ```bash
   git log -1 --stat
   git show v0.3.2
   ```

1. **Test locally before releasing**

   ```bash
   uv run poe check  # Run all checks
   uv run poe build  # Build wheel
   ```

1. **Write good commit messages**

   - Clear, descriptive
   - Follow conventional format
   - Include breaking changes if applicable

1. **Never force push tags to main**

   - Tags trigger CI/CD
   - Force pushing can cause duplicate releases

## See Also

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CHANGELOG.md](../CHANGELOG.md) - Full changelog
- [Conventional Commits](https://www.conventionalcommits.org/)
- [semantic-release](https://python-semantic-release.readthedocs.io/)
