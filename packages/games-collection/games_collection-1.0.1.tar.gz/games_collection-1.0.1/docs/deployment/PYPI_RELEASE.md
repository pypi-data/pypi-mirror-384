# PyPI Release Process

This document describes how to release the games-collection package to PyPI.

## Prerequisites

### 1. PyPI Account and Trusted Publishing

1. **PyPI Account**: Create an account at https://pypi.org
1. **Trusted Publishing**: Configure trusted publishing (OIDC) in PyPI project settings:
   - Go to PyPI project settings for `games-collection`
   - Add a new publisher under "Trusted Publishers"
   - Select "GitHub" as the publisher
   - Owner: `saint2706`
   - Repository: `Games`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi`

### 2. GitHub Environment Configuration

The workflow requires a GitHub environment named `pypi` to be configured:

1. Go to repository **Settings** > **Environments**
1. Click **New environment**
1. Enter name: `pypi`
1. Click **Configure environment**
1. (Optional) Add protection rules:
   - **Required reviewers**: Add reviewers who must approve deployments
   - **Wait timer**: Add delay before deployment proceeds
   - **Deployment branches**: Restrict to specific branches (e.g., `main` or tags matching `v*`)
1. Click **Save protection rules**

**Important Notes**:

- The environment name **must** be `pypi` to match PyPI trusted publishing configuration
- No environment secrets are needed - the workflow uses OpenID Connect (OIDC) for authentication
- Protection rules are optional but recommended for production deployments
- The workflow will fail if the environment doesn't exist or access is denied

## Automated Release Process

The package is automatically published to PyPI when a GitHub Release is created:

1. **Update Version**: Edit `version` in `pyproject.toml` (e.g., `"1.0.1"`)
1. **Update Changelog**: Document changes in `CHANGELOG.md`
1. **Commit and Push**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 1.0.1"
   git push
   ```
1. **Create GitHub Release**:
   - Go to https://github.com/saint2706/Games/releases/new
   - Create a new tag: `v1.0.1`
   - Set the release title: `v1.0.1`
   - Add release notes from CHANGELOG.md
   - Click "Publish release"
1. **Automated Publishing**: GitHub Actions automatically:
   - Builds distribution packages (wheel and source distribution)
   - Publishes to PyPI using trusted publishing
   - Signs packages with Sigstore
   - Uploads signed packages to the GitHub Release

## Manual Testing (Local Build)

Before creating a release, test the package build locally:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Check the built packages exist
ls -lh dist/

# Optionally, install locally to test
pip install dist/games_collection-*.whl
```

**Note**: Local testing with `twine check` may show a false positive error about the `License-File` metadata field. This is a known compatibility issue between setuptools and twine 6.x. PyPI will accept the package despite this validation warning.

## Local Workflow Testing

Test the publish workflow locally using `act`:

```bash
# Test just the build job
./scripts/run_workflow.sh publish --job build --event .github/workflows/events/release.json --dry-run

# Note: Full publish requires PyPI credentials and should only run on GitHub Actions
```

## Manual Trigger

The workflow can also be triggered manually via GitHub Actions UI:

1. Go to Actions tab
1. Select "Publish to PyPI" workflow
1. Click "Run workflow"
1. Confirm to trigger

This will build the package but NOT publish it (publishing only happens on release events).

## Post-Release Verification

After the release is published:

1. **Verify on PyPI**: Visit https://pypi.org/project/games-collection/
1. **Test Installation**:
   ```bash
   pip install games-collection
   # Or upgrade
   pip install --upgrade games-collection
   ```
1. **Verify Package Contents**:
   ```bash
   pip show games-collection
   pip list | grep games-collection
   ```
1. **Test Entry Points**:
   ```bash
   games-uno --help
   games-blackjack --help
   ```

## Troubleshooting

### Build Fails

- Check that `pyproject.toml` is valid
- Ensure all required files (LICENSE, README.md) exist
- Verify Python version compatibility (>=3.9)

### Jobs Are Skipped After Build

If the `build` job succeeds but `publish-to-pypi` and `github-release` jobs are skipped:

1. **Check Event Type**:

   - These jobs only run on `release` events with action `published`
   - They will be skipped on `workflow_dispatch` (manual trigger)
   - This is intentional security behavior

1. **Verify Environment Exists**:

   - Go to repository **Settings** > **Environments**
   - Confirm the `pypi` environment exists
   - If missing, see "GitHub Environment Configuration" in Prerequisites section

1. **Check Environment Protection Rules**:

   - If environment has required reviewers, deployment needs approval
   - Check the Actions tab for pending approval requests
   - Reviewers will receive notification to approve the deployment

1. **Review Workflow Logs**:
   - Go to Actions tab and select the workflow run
   - Check for error messages or warnings
   - Look for "Environment protection rules" or "Waiting for approval" messages

### Publishing Fails

- Verify trusted publishing is configured correctly in PyPI
- Check that the workflow has `id-token: write` permission
- Ensure the release tag matches the version in `pyproject.toml`
- Confirm the PyPI trusted publishing configuration matches:
  - Workflow name: `publish-pypi.yml`
  - Environment name: `pypi`

### Environment Configuration Issues

- **Error: "Environment not found"**: Create the `pypi` environment (see Prerequisites)
- **Error: "Deployment rejected"**: Check environment protection rules and required reviewers
- **Jobs pending indefinitely**: Required reviewer approval may be needed

### Package Version Already Exists

- PyPI does not allow overwriting existing versions
- Bump the version number and create a new release
- For fixes, create a patch version (e.g., 1.0.1 → 1.0.2)

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

Examples:

- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New game added
- `1.1.0` → `2.0.0`: API breaking change
