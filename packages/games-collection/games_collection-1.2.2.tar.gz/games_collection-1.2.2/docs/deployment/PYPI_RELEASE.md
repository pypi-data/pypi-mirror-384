# PyPI Release Process

This document describes how to release the games-collection package to PyPI.

## Quick Start: Releasing v1.2.1

Version 1.2.1 is already set in both `pyproject.toml` and `scripts/__init__.py`. To release it:

1. **Create GitHub Release** (recommended):

   - Go to https://github.com/saint2706/Games/releases/new
   - Tag: `v1.2.1`
   - Title: `v1.2.1`
   - Add release notes describing changes
   - Click "Publish release"

1. **Automated Process**: Two workflows will automatically run:

   - ✅ `publish-pypi.yml`: Publishes to PyPI and uploads wheel/sdist
   - ✅ `build-executables.yml`: Builds and uploads executables for Linux, Windows, macOS

1. **Verify**: Check that the release has all artifacts:

   - Distribution packages (.whl, .tar.gz)
   - Executables (games-collection for each platform)
   - Signatures (.sigstore files)

______________________________________________________________________

## Workflow Coordination

As of v1.2.1, the release process is fully coordinated between two GitHub Actions workflows:

- **`publish-pypi.yml`**: Handles PyPI publishing, package signing, and uploading distribution packages
- **`build-executables.yml`**: Handles building standalone executables for all platforms and uploading them

Both workflows trigger on the same release event, ensuring that:
✅ When you create a release (manually or via automated workflow), both workflows run automatically
✅ Executables are built and added to the GitHub Release
✅ The package is published to PyPI
✅ All artifacts (executables, wheels, source distributions) are in one release

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

### Option 1: Automated Version Bump (Recommended)

The workflow now includes automated version bumping. To create a new release:

1. **Update Changelog**: Document your changes in `CHANGELOG.md`
1. **Commit and Push**:
   ```bash
   git add CHANGELOG.md
   git commit -m "docs: update changelog for next release"
   git push
   ```
1. **Trigger Workflow**: Go to [Actions > Publish to PyPI](https://github.com/saint2706/Games/actions/workflows/publish-pypi.yml)
   - Click "Run workflow"
   - Select branch: `master`
   - Choose version bump type:
     - `patch` (1.0.1 → 1.0.2) - Bug fixes
     - `minor` (1.0.1 → 1.1.0) - New features
     - `major` (1.0.1 → 2.0.0) - Breaking changes
   - Click "Run workflow"
1. **Automated Process**: GitHub Actions automatically:
   - Bumps version in `pyproject.toml` and `scripts/__init__.py`
   - Commits the version change
   - Creates and pushes a git tag (e.g., `v1.0.2`)
   - Creates a GitHub Release
   - **PyPI Publishing** (`publish-pypi.yml`):
     - Validates version consistency
     - Builds distribution packages (wheel and source distribution)
     - Publishes to PyPI using trusted publishing
     - Signs packages with Sigstore
     - Uploads signed packages to the GitHub Release
   - **Executable Building** (`build-executables.yml`):
     - Builds standalone executables for Linux, Windows, and macOS
     - Runs cross-platform tests
     - Uploads executables to the GitHub Release

### Option 2: Manual Release Process

If you prefer to bump the version manually:

1. **Update Version**: Edit `version` in `pyproject.toml` (e.g., `"1.0.1"`)
1. **Update Scripts Version**: Edit `__version__` in `scripts/__init__.py` to match
1. **Update Changelog**: Document changes in `CHANGELOG.md`
1. **Commit and Push**:
   ```bash
   git add pyproject.toml scripts/__init__.py CHANGELOG.md
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
   - **PyPI Publishing** (`publish-pypi.yml`):
     - Validates version consistency
     - Builds distribution packages (wheel and source distribution)
     - Publishes to PyPI using trusted publishing
     - Signs packages with Sigstore
     - Uploads signed packages to the GitHub Release
   - **Executable Building** (`build-executables.yml`):
     - Builds standalone executables for Linux, Windows, and macOS
     - Runs cross-platform tests
     - Uploads executables to the GitHub Release

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
- The workflow now checks for existing release assets and will fail with a clear error message
- To fix:
  1. Delete the existing release and tag: `git tag -d v1.0.1 && git push origin :refs/tags/v1.0.1`
  1. Run the automated version bump workflow again
  1. Or manually bump to a new version (e.g., 1.0.1 → 1.0.2)

### Release Assets Already Exist

If you see an error like "The following assets already exist in release":

- The workflow automatically checks for existing assets before upload
- This prevents accidental overwrites and version conflicts
- To fix:
  1. Delete the existing release: `gh release delete v1.0.1 --yes`
  1. Delete the tag: `git tag -d v1.0.1 && git push origin :refs/tags/v1.0.1`
  1. Run the automated version bump workflow again with a higher version

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

Examples:

- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New game added
- `1.1.0` → `2.0.0`: API breaking change
