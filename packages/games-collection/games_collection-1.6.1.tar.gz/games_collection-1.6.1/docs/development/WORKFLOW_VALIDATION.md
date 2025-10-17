# GitHub Actions Workflow Validation

This guide explains how to validate GitHub Actions workflows in this repository.

## Overview

The repository includes a comprehensive validation system for GitHub Actions workflows to ensure:

- Correct YAML syntax
- Valid workflow structure
- Proper configuration
- Working script references
- Consistent documentation

## Validation Tools

### validate_workflows.py

The main validation script that checks all aspects of workflow files.

**Location:** `scripts/validate_workflows.py`

**Usage:**

```bash
# Direct execution
python scripts/validate_workflows.py

# Via Make
make workflow-validate

# In tests
pytest tests/test_workflows.py -v
```

### What Gets Validated

#### 1. YAML Syntax

Ensures all `.yml` files in `.github/workflows/` are valid YAML:

- Proper indentation
- Valid key-value pairs
- No syntax errors
- Parseable by PyYAML

#### 2. Event Payloads

Validates all JSON files in `.github/workflows/events/`:

- Valid JSON syntax
- Proper structure
- Event-specific fields

#### 3. Workflow Structure

Checks that each workflow has:

- **name**: Workflow display name
- **on**: Trigger events (push, pull_request, etc.)
- **jobs**: At least one job definition

#### 4. Job Structure

Verifies each job includes:

- **runs-on**: Runner platform (ubuntu-latest, etc.)
- **steps**: Array of steps to execute

#### 5. Script References

Ensures all referenced scripts:

- Exist in the repository
- Are actual files (not directories)
- Are executable (for `.sh` files)

#### 6. Documentation Consistency

Validates that:

- `run_workflow.sh` documents all workflows
- Documentation files exist
- Scripts are properly referenced

## Validation Output

### Success

```bash
🔍 Validating GitHub Actions Workflows
============================================================

📄 Validating YAML Syntax...
  ✓ ci.yml
  ✓ format-and-lint.yml
  ✓ manual-tests.yml
  ✓ manual-coverage.yml
  ✓ mutation-testing.yml
  ✓ build-executables.yml
  ✓ codeql.yml
  ✓ publish-pypi.yml
  ✓ test-act-setup.yml

📦 Validating Event Payloads...
  ✓ push.json
  ✓ pull_request.json
  ✓ release.json
  ✓ workflow_dispatch.json

🏗️  Validating Workflow Structure...
  ✓ ci.yml: Structure valid
  ✓ format-and-lint.yml: Structure valid
  ...

📜 Validating Script References...
  ✓ scripts/run_workflow.sh

📚 Validating Documentation...
  ✓ run_workflow.sh exists and documents 8 workflows

============================================================

📊 Validation Summary
------------------------------------------------------------

✅ All validations passed! Workflows are healthy.
```

### Failures

When validation fails, you'll see detailed error messages:

```bash
📊 Validation Summary
------------------------------------------------------------

❌ 2 Error(s) found:
   • ci.yml: Job 'test' missing 'runs-on'
   • scripts/missing-script.sh: Referenced script not found

⚠️  1 Warning(s):
   • build-executables.yml: Script not executable
```

## Running Validation

### Locally

#### Quick Check

```bash
make workflow-validate
```

#### Verbose Testing

```bash
pytest tests/test_workflows.py -v
```

#### Direct Script Execution

```bash
python scripts/validate_workflows.py
```

### In CI

Validation runs automatically in the `test-act-setup.yml` workflow when:

- Changes are made to workflow files
- Changes are made to workflow scripts
- Changes are made to event payloads
- Manual workflow dispatch

### Pre-commit Hook

To run validation before every commit, add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: validate-workflows
      name: Validate GitHub Actions Workflows
      entry: python scripts/validate_workflows.py
      language: system
      pass_filenames: false
      always_run: false
      files: ^\.github/workflows/.*\.(yml|json)$
```

## Common Issues and Fixes

### Invalid YAML Syntax

**Error:** `Invalid YAML in ci.yml: expected <block end>, but found '-'`

**Fix:** Check indentation and ensure proper YAML structure. Use a YAML validator.

### Missing Required Fields

**Error:** `ci.yml: Job 'test' missing 'runs-on'`

**Fix:** Add the required field to the job:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - ...
```

### Script Not Found

**Error:** `Referenced script not found: scripts/missing-script.sh`

**Fix:** Either:

- Create the missing script
- Update the workflow to reference the correct script path
- Remove the reference if no longer needed

### Script Not Executable

**Warning:** `Script not executable: scripts/run_workflow.sh`

**Fix:** Make the script executable:

```bash
chmod +x scripts/run_workflow.sh
```

## Workflow Files

### Current Workflows

| Workflow | File | Purpose | Trigger |
| -------------------- | --------------------------- | -------------------------- | -------------------------- |
| CI | `ci.yml` | Lint and test | push, pull_request |
| Format and Lint | `format-and-lint.yml` | Auto-format code | workflow_dispatch |
| Manual Tests | `manual-tests.yml` | Run tests on demand | workflow_dispatch |
| Manual Coverage | `manual-coverage.yml` | Generate coverage report | workflow_dispatch |
| Mutation Testing | `mutation-testing.yml` | Validate test quality | workflow_dispatch, schedule |
| Build Executables | `build-executables.yml` | Build standalone binaries | push, pull_request, tags |
| CodeQL | `codeql.yml` | Security analysis | push, pull_request, schedule |
| Publish to PyPI | `publish-pypi.yml` | Publish releases | release |
| Test Act Setup | `test-act-setup.yml` | Test workflow tooling | workflow_dispatch, pull_request |

### Event Payloads

Located in `.github/workflows/events/`:

| File | Purpose |
| ---------------------- | ------------------------------------ |
| `push.json` | Mock push event for local testing |
| `pull_request.json` | Mock PR event for local testing |
| `release.json` | Mock release event for local testing |
| `workflow_dispatch.json` | Mock manual trigger event |

## Automated Testing

### Test Suite

The repository includes comprehensive tests in `tests/test_workflows.py`:

```python
def test_workflow_files_exist()
def test_event_payload_files_exist()
def test_workflow_validation_script_exists()
def test_workflow_validation_passes()
def test_workflow_syntax_valid()
def test_event_payload_syntax_valid()
def test_workflow_structure()
def test_workflow_scripts_exist()
def test_workflow_documentation_exists()
```

### Running Tests

```bash
# Run all workflow tests
pytest tests/test_workflows.py -v

# Run specific test
pytest tests/test_workflows.py::test_workflow_validation_passes -v

# Run with coverage
pytest tests/test_workflows.py --cov=scripts -v
```

## Continuous Integration

Workflows are validated:

1. **Before merge**: Tests run on every pull request
1. **After merge**: CI validates on push to master
1. **Scheduled**: Weekly CodeQL security scans
1. **On changes**: When workflow files are modified

## Best Practices

### When Creating New Workflows

1. **Start with a template**: Copy an existing workflow
1. **Validate early**: Run `make workflow-validate` frequently
1. **Test locally**: Use `act` to test before pushing
1. **Add documentation**: Update `run_workflow.sh` help text
1. **Include in tests**: Reference in test suite

### Workflow Structure

```yaml
name: My Workflow

on:
  push:
    branches: [master]
  workflow_dispatch:

permissions:
  contents: read

env:
  PYTHON_VERSION: "3.12"

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Run script
        run: ./scripts/my-script.sh
```

### Event Payload Structure

```json
{
  "ref": "refs/heads/master",
  "repository": {
    "name": "Games",
    "owner": {
      "login": "saint2706"
    }
  }
}
```

## Troubleshooting

### Validation Script Fails

```bash
# Check Python version (3.9+ required)
python3 --version

# Ensure PyYAML is installed
pip install pyyaml

# Run with verbose output
python3 -v scripts/validate_workflows.py
```

### Tests Fail

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run specific test
pytest tests/test_workflows.py::test_workflow_syntax_valid -vv

# Check pytest configuration
cat pytest.ini
```

### YAML Parsing Issues

```bash
# Validate YAML manually
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Use yamllint
yamllint .github/workflows/ci.yml

# Check with pre-commit
pre-commit run check-yaml --files .github/workflows/ci.yml
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Act - Local Testing](https://github.com/nektos/act)
- [Local Workflows Guide](LOCAL_WORKFLOWS.md)
- [Workflow Testing Quickstart](WORKFLOW_TESTING_QUICKSTART.md)

## Related Documentation

- [LOCAL_WORKFLOWS.md](LOCAL_WORKFLOWS.md) - Running workflows locally with act
- [WORKFLOW_TESTING_QUICKSTART.md](WORKFLOW_TESTING_QUICKSTART.md) - Quick start guide
- [CODE_QUALITY.md](CODE_QUALITY.md) - Code quality standards
- [TESTING.md](TESTING.md) - Testing guidelines
