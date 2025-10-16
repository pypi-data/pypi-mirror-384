# GitHub Actions Workflows Documentation

This directory contains documentation related to GitHub Actions workflows, debugging, validation, and fixes.

## Documentation Files

### [VALIDATION_REPORT.md](VALIDATION_REPORT.md)

Comprehensive validation report showing the status of all GitHub Actions workflows.

**Topics:**

- Workflow validation results
- Event payload validation
- GitHub Actions version check
- Script references verification
- Documentation consistency

### [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md)

Summary of workflow validation implementation and tools.

**Topics:**

- Validation system overview
- Tool descriptions
- Test suite results
- Integration with CI

### [DEBUG_REPORT.md](DEBUG_REPORT.md)

Debug report analyzing workflow failures and issues.

**Topics:**

- Failure analysis
- Root cause identification
- Quick fix guides
- Prevention strategies
- Action items

### [FIX_SUMMARY.md](FIX_SUMMARY.md)

Summary of specific workflow fixes and resolutions.

**Topics:**

- Problem analysis
- Solutions implemented
- Verification steps
- Impact assessment

### [PYPI_PUBLISH_DEBUG_RUN_18520989869.md](PYPI_PUBLISH_DEBUG_RUN_18520989869.md)

Detailed debug report for PyPI publish workflow failure run #18520989869.

**Topics:**

- Version mismatch analysis
- Root cause: Tag vs code version inconsistency
- Fix instructions (multiple options)
- Prevention: New validation system
- Future safeguards implemented

### [HOW_TO_FIX_V1_1_1.md](HOW_TO_FIX_V1_1_1.md)

Step-by-step guide to fix the v1.1.1 release issue.

**Topics:**

- Current state analysis
- Fix options (clean slate vs move forward)
- New safeguards explanation
- Testing procedures
- Quick command reference

## Quick Reference

### Validate Workflows

```bash
make workflow-validate
# or
python scripts/validate_workflows.py
```

### Show Workflow Information

```bash
make workflow-info
# or
python scripts/workflow_info.py ci.yml -v
```

### Run Workflow Tests

```bash
pytest tests/test_workflows.py -v
```

### Run Workflows Locally

```bash
# Using act (requires installation)
make workflow-ci
make workflow-lint
make workflow-test
```

## Workflow Files

All workflow files are located in `.github/workflows/`:

- `ci.yml` - Continuous integration
- `format-and-lint.yml` - Code formatting and linting
- `manual-tests.yml` - Manual test execution
- `manual-coverage.yml` - Manual coverage reporting
- `mutation-testing.yml` - Mutation testing
- `build-executables.yml` - Build standalone executables
- `codeql.yml` - Code security scanning
- `publish-pypi.yml` - PyPI package publishing
- `test-act-setup.yml` - Local workflow testing setup

## Event Payloads

Test event payloads for local workflow testing are in `.github/workflows/events/`:

- `push.json` - Mock push event
- `pull_request.json` - Mock PR event
- `release.json` - Mock release event
- `workflow_dispatch.json` - Mock manual trigger event

## Validation Tools

### scripts/validate_workflows.py

Comprehensive validation script that checks:

- YAML syntax
- JSON payloads
- Workflow structure
- Script references
- GitHub Actions versions
- Documentation consistency

### scripts/workflow_info.py

Information display tool showing:

- Trigger events
- Required permissions
- Environment variables
- Jobs and dependencies
- Actions used

## Development Guides

For detailed guides on working with workflows:

- [Local Workflows Guide](../development/LOCAL_WORKFLOWS.md)
- [Workflow Testing Quickstart](../development/WORKFLOW_TESTING_QUICKSTART.md)
- [Workflow Validation Guide](../development/WORKFLOW_VALIDATION.md)

### scripts/check_version_consistency.py

Version consistency validation script that checks:

- Version in `pyproject.toml`
- Version in `scripts/__init__.py`
- Git tag version (optional)
- Provides clear error messages
- Used by CI to prevent version mismatches

## Common Issues

### PyPI Publishing Version Mismatch

**Error:** `File already exists on PyPI`

**Cause:** Git tag version doesn't match code version

**Solution:**

```bash
# Check version consistency
python scripts/check_version_consistency.py --tag v1.2.3

# Follow fix guide
See: HOW_TO_FIX_V1_1_1.md
```

### Markdown Formatting Failures

**Error:** `mdformat --check failed`

**Solution:**

```bash
mdformat .
git add .
git commit -m "fix: format markdown files"
```

### Python Formatting Failures

**Error:** `black --check failed`

**Solution:**

```bash
black .
git add .
git commit -m "fix: format Python files"
```

### Test Failures

**Error:** `Tests failed`

**Solution:**

```bash
pytest -v  # Run locally to identify issue
# Fix the failing test
git add .
git commit -m "fix: resolve test failure"
```

## Best Practices

1. **Always run pre-commit hooks** - `pre-commit install`
1. **Test locally first** - `make workflow-validate`
1. **Check formatting** - `black .` and `mdformat .`
1. **Run tests** - `pytest`
1. **Use validation tools** - `python scripts/validate_workflows.py`

## Related Documentation

- [CI/CD Documentation](../development/BUILD_EXECUTABLES_WORKFLOW.md)
- [Testing Guide](../development/TESTING.md)
- [Code Quality Standards](../development/CODE_QUALITY.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
