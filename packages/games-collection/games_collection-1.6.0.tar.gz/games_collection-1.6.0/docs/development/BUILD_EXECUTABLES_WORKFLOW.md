# Build Executables Workflow Guide

## Overview

The `build-executables.yml` workflow builds standalone executables for the Games collection on multiple platforms and uploads them to GitHub releases.

**Triggers:**

- Push to `master`/`main` branches (builds only, no release)
- Push to tags matching `v*` (builds and creates/updates release)
- **Release events** (when a release is published - coordinates with `publish-pypi.yml`)
- Pull requests (builds for validation)
- Manual workflow dispatch

**Coordination:** As of v1.2.1, this workflow triggers on release events alongside `publish-pypi.yml`, ensuring that executables are automatically added to releases when the package is published to PyPI.

## Workflow Jobs

### 1. build-pyinstaller

**Purpose:** Build standalone executables using PyInstaller

**Platforms:** Ubuntu, Windows, macOS

**Python Version:** 3.11

**Steps:**

1. Check out repository
1. Set up Python
1. Install dependencies
1. Build with PyInstaller
1. Validate executable exists
1. Test executable (platform-specific)
1. Upload artifacts

**Notes:**

- Dependencies now install the GUI extra (`pip install -e ".[gui]"`) so PyQt5 and Qt plugins are available before running PyInstaller.
- The validation step ensures the expected executable (`dist/games-collection.exe` on Windows, `dist/games-collection` on Linux/macOS) exists before proceeding. If the file is missing, the job fails with a clear error message.
- The smoke test launches a headless PyQt5 GUI using `./dist/games-collection --game dots_and_boxes --gui-framework pyqt5 --smoke-test` (with `QT_QPA_PLATFORM=offscreen`) to confirm Qt resources are bundled.

**Artifacts:**

- `games-collection-pyinstaller-ubuntu-latest-py3.11`
- `games-collection-pyinstaller-windows-latest-py3.11`
- `games-collection-pyinstaller-macos-latest-py3.11`

### 2. cross-platform-tests

**Purpose:** Verify package imports work across platforms and Python versions

**Platforms:** Ubuntu, Windows, macOS

**Python Versions:** 3.9, 3.10, 3.11, 3.12

**Tests:**

- Launcher import
- Crash reporter import
- Sample game imports (War, Go Fish)

### 3. docker-build

**Purpose:** Build and test Docker image

**Platform:** Ubuntu

**Steps:**

1. Build Docker image
1. Test Python version in container

### 4. create-release

**Purpose:** Create GitHub release with built executables

**Platform:** Ubuntu

**Trigger Condition:** `startsWith(github.ref, 'refs/tags/v')`

**Dependencies:** Requires all previous jobs to complete successfully

**Steps:**

1. Check out repository
1. Download all artifacts from build jobs
1. List artifacts (for debugging)
1. Verify all expected artifacts exist
1. Create GitHub release with artifacts attached

## Why create-release is "Skipped"

### The Condition

The `create-release` job has this condition:

```yaml
if: startsWith(github.ref, 'refs/tags/v')
```

This means the job **ONLY runs when a version tag starting with 'v' is pushed**.

### When It Runs

✅ **RUNS:**

- When you push a version tag: `git tag v1.0.0 && git push origin v1.0.0`
- Tag format must start with `v` (e.g., `v1.0.0`, `v2.1.3`, `v0.1.0-beta`)

⏭️ **SKIPPED:**

- Regular commits to master/main
- Pull requests
- Manual workflow dispatch
- Any push without a version tag

### Why This Is Correct Behavior

This is **intentional and correct** behavior because:

1. **Releases should be deliberate** - Creating a GitHub release should only happen when explicitly intended
1. **Avoid duplicate releases** - Every commit would create a release otherwise
1. **Version control** - Tags provide proper version tracking
1. **Artifact management** - Only release-worthy builds get published

## How to Create a Release

### Step 1: Ensure Everything is Ready

```bash
# Make sure all tests pass
pytest tests/ -v

# Verify workflow validation
make workflow-validate

# Ensure you're on master/main
git checkout master
git pull origin master
```

### Step 2: Create and Push a Version Tag

```bash
# Create a version tag (follow semantic versioning)
git tag v1.0.0

# Push the tag to trigger the release workflow
git push origin v1.0.0
```

### Step 3: Monitor the Workflow

The workflow will:

1. ✅ Build executables for all platforms
1. ✅ Run cross-platform tests
1. ✅ Build Docker image
1. ✅ Create GitHub release with all artifacts

You can monitor progress at:
`https://github.com/saint2706/Games/actions/workflows/build-executables.yml`

## Testing the Workflow Without Creating a Release

### Option 1: Debug Script (Recommended)

Use the debug script to simulate workflow execution:

```bash
# Analyze the workflow
python scripts/debug_workflow.py build-executables.yml --suggest

# Simulate different scenarios
python scripts/debug_workflow.py build-executables.py --simulate push --ref refs/tags/v1.0.0
python scripts/debug_workflow.py build-executables.py --simulate push --ref refs/heads/master
```

### Option 2: Test Locally with Act

Test the workflow locally without pushing:

```bash
# Test the entire workflow (create-release will be skipped)
./scripts/run_workflow.sh build

# Simulate a tag push (requires creating event JSON)
cat > /tmp/tag-event.json << EOF
{
  "ref": "refs/tags/v1.0.0",
  "repository": {
    "name": "Games",
    "owner": {
      "login": "saint2706"
    }
  }
}
EOF

act push -e /tmp/tag-event.json -W .github/workflows/build-executables.yml
```

### Option 3: Test Individual Jobs

Test specific jobs without running the full workflow:

```bash
# Test PyInstaller build
pip install -e .
pip install pyinstaller
pyinstaller build_configs/pyinstaller/games.spec --clean

# Test imports
python -c "from scripts.launcher import main; print('OK')"

# Test Docker build
docker build -t games-collection:test .
docker run --rm games-collection:test python -c "import sys; print(f'Python {sys.version}')"
```

## Workflow Execution Scenarios

### Scenario 1: Regular Push to Master

```bash
git push origin master
```

**Result:**

- ✅ build-pyinstaller: RUNS
- ✅ cross-platform-tests: RUNS
- ✅ docker-build: RUNS
- ⏭️ create-release: **SKIPPED** (no tag)

### Scenario 2: Pull Request

```bash
# Create and push PR
```

**Result:**

- ✅ build-pyinstaller: RUNS
- ✅ cross-platform-tests: RUNS
- ✅ docker-build: RUNS
- ⏭️ create-release: **SKIPPED** (no tag)

### Scenario 3: Version Tag Push

```bash
git tag v1.0.0
git push origin v1.0.0
```

**Result:**

- ✅ build-pyinstaller: RUNS
- ✅ cross-platform-tests: RUNS
- ✅ docker-build: RUNS
- ✅ create-release: **RUNS** ← Creates GitHub release!

### Scenario 4: Manual Workflow Dispatch

```bash
# Trigger via GitHub UI or API
```

**Result:**

- ✅ build-pyinstaller: RUNS
- ✅ cross-platform-tests: RUNS
- ✅ docker-build: RUNS
- ⏭️ create-release: **SKIPPED** (no tag)

## Debugging Tips

### Check Job Status

```bash
# Use the debug script
python scripts/debug_workflow.py build-executables.yml

# Use workflow info
python scripts/workflow_info.py build-executables.yml -v
```

### View Recent Runs

Go to: `https://github.com/saint2706/Games/actions/workflows/build-executables.yml`

### Check Artifacts

After the workflow runs, download artifacts from the Actions tab:

1. Go to Actions → Build Executables → Latest run
1. Scroll to "Artifacts" section
1. Download platform-specific executables

### Test Release Creation Locally

You can't fully test release creation locally (GitHub API required), but you can:

1. Test artifact downloads
1. Verify artifact structure
1. Check that softprops/action-gh-release@v2 is properly configured

## Common Issues

### Issue: "create-release job is skipped"

**Cause:** Not pushing a version tag

**Solution:** This is expected behavior. To create a release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Issue: "No artifacts to download"

**Cause:** Previous jobs failed

**Solution:**

1. Check build-pyinstaller, cross-platform-tests, and docker-build logs
1. Fix any build errors
1. Re-run the workflow

### Issue: "Release creation failed"

**Cause:** Missing permissions, tag already exists, or missing artifacts

**Solution:**

1. Ensure workflow has `contents: write` permission ✅
1. Check the "List artifacts" and "Verify artifacts exist" step logs to see if all expected artifacts are present
1. Delete existing tag if needed: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`
1. Create new tag with different version
1. If artifacts are missing, check that all build-pyinstaller jobs completed successfully

## Version Tagging Best Practices

### Semantic Versioning

Follow semantic versioning: `vMAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes
- **MINOR:** New features (backwards compatible)
- **PATCH:** Bug fixes

Examples:

- `v1.0.0` - First stable release
- `v1.1.0` - Added new game
- `v1.1.1` - Fixed bug in existing game
- `v2.0.0` - Major refactoring with breaking changes

### Pre-release Versions

For beta/alpha releases:

- `v1.0.0-alpha.1`
- `v1.0.0-beta.1`
- `v1.0.0-rc.1`

### Tag Annotations

Create annotated tags with descriptions:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0

Features:
- Added 9 new card games
- Improved AI opponents
- GUI support for major games

Bug fixes:
- Fixed scoring in Blackjack
- Improved error handling
"

git push origin v1.0.0
```

## Workflow Configuration

### Trigger Events

```yaml
on:
  push:
    branches: [master, main]
    tags: ['v*']
  pull_request:
    branches: [master, main]
  workflow_dispatch:
```

### Permissions

```yaml
permissions:
  contents: write  # Required for creating releases
```

### Job Dependencies

```
build-pyinstaller ─┐
                   ├─→ create-release
cross-platform-tests ─┤
                   ├─→ (only on tag push)
docker-build ──────┘
```

## Related Documentation

- [Workflow Validation Guide](WORKFLOW_VALIDATION.md)
- [Local Workflows Guide](LOCAL_WORKFLOWS.md)
- [Workflow Testing Quickstart](WORKFLOW_TESTING_QUICKSTART.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Quick Reference

```bash
# Debug workflow
python scripts/debug_workflow.py build-executables.yml --suggest

# Validate workflow
make workflow-validate

# Create release
git tag v1.0.0
git push origin v1.0.0

# Test locally
./scripts/run_workflow.sh build
```
