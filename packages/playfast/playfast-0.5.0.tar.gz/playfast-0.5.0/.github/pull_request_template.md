## Description

<!-- Provide a clear and concise description of your changes -->

## Motivation and Context

<!-- Why is this change required? What problem does it solve? -->

<!-- If it fixes an open issue, please link to the issue here -->

Closes #(issue)

## Type of Change

<!-- Mark relevant options with an [x] -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] Test update
- [ ] CI/CD update
- [ ] Other (please describe):

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Test Environment

- Python version:
- Playfast version:
- OS:

### Test Cases

<!-- Mark completed items with [x] -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All existing tests pass
- [ ] Benchmarks run (if performance-related)

### Test Results

```bash
# Paste relevant test output here
```

## Performance Impact

<!-- If applicable, include benchmark results -->

### Before

```
# Benchmark results before changes
```

### After

```
# Benchmark results after changes
```

**Performance Change**: <!-- e.g., 2x faster, no impact, 10% slower -->

## Documentation

<!-- Mark completed items with [x] -->

- [ ] README.md updated
- [ ] CLAUDE.md updated (if development-related)
- [ ] CONTRIBUTING.md updated (if contribution process changed)
- [ ] Docstrings added/updated
- [ ] Type hints added/updated
- [ ] Examples added/updated
- [ ] CHANGELOG.md updated (under "Unreleased")

## Code Quality

<!-- Mark completed items with [x] -->

### Python

- [ ] Code follows project style guidelines (Ruff)
- [ ] Type checking passes (`uv run mypy python/`)
- [ ] Linting passes (`uv run ruff check python/`)
- [ ] Formatting applied (`uv run ruff format python/`)
- [ ] All tests pass (`uv run pytest`)

### Rust

- [ ] Code follows Rust style guidelines (`cargo fmt`)
- [ ] Clippy lints pass (`cargo clippy -- -D warnings`)
- [ ] All tests pass (`cargo test`)
- [ ] No unsafe code added (or justified if necessary)

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

### What breaks?

<!-- Describe what will break for existing users -->

### Migration Guide

<!-- Provide step-by-step migration instructions -->

```python
# Before
old_code_example()

# After
new_code_example()
```

## Dependencies

<!-- List any new dependencies or version updates -->

### Python Dependencies

-
-

### Rust Dependencies

-
-

**Justification**: <!-- Why are these dependencies needed? -->

## Related Issues and PRs

<!-- Link related issues and pull requests -->

- Related to #
- Depends on #
- Blocks #

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Checklist

<!-- Mark completed items with [x] -->

- [ ] I have read the [CONTRIBUTING.md](../CONTRIBUTING.md) guide
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] I have checked my code and corrected any misspellings

## Additional Notes

<!-- Add any additional notes, concerns, or questions for reviewers -->

## Reviewer Guidance

<!-- Help reviewers know where to focus -->

## **Focus Areas**

-

## **Potential Concerns**

-

## Deployment Notes

<!-- Any special considerations for deployment -->

- [ ] Requires database migration
- [ ] Requires configuration changes
- [ ] Requires documentation deployment
- [ ] Can be deployed independently
- [ ] Requires coordinated deployment

______________________________________________________________________

**For Maintainers**:

### Review Checklist

- [ ] Code quality meets project standards
- [ ] Tests are comprehensive and pass
- [ ] Documentation is complete and accurate
- [ ] Breaking changes are justified and documented
- [ ] Performance impact is acceptable
- [ ] Security implications considered
- [ ] Backward compatibility maintained (or breaking change justified)

### Merge Checklist

- [ ] All CI checks pass
- [ ] At least one approval from maintainer
- [ ] No unresolved conversations
- [ ] Branch is up to date with main
- [ ] Squash and merge or create merge commit (as appropriate)
- [ ] Update release notes if needed
