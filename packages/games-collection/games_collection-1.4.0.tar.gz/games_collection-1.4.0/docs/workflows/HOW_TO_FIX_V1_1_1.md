# How to Fix the v1.1.1 Release Issue

## Quick Summary

The v1.1.1 release failed to publish to PyPI because the git tag v1.1.1 points to code that has version 1.0.1, not 1.1.1. PyPI already has version 1.0.1, so it rejected the duplicate upload.

______________________________________________________________________

## Current State

- ✅ **Tag v1.1.1 exists** - But points to wrong code (version 1.0.1)
- ✅ **Release v1.1.1 exists** - With executables from build-executables workflow
- ✅ **PyPI has version 1.0.1** - Cannot overwrite or re-upload
- ✅ **Master branch has version 1.1.0** - Latest development version
- ❌ **v1.1.1 never published to PyPI** - Need to fix and republish

______________________________________________________________________

## Recommended Fix: Option A (Clean Slate)

This approach recreates v1.1.1 properly with matching versions.

### Step 1: Clean Up Existing Release

```bash
# Delete the GitHub release (via UI or CLI)
gh release delete v1.1.1 --yes

# Delete the tag
git push --delete origin v1.1.1
git tag -d v1.1.1
```

### Step 2: Use Automated Workflow

The easiest way is to use the built-in automation:

1. Go to: **Actions** → **Publish to PyPI** → **Run workflow**
1. Configure:
   - **Branch:** master
   - **Bump version:** minor (this will bump 1.1.0 → 1.1.1)
1. Click **Run workflow**

The workflow will:

- ✅ Bump version to 1.1.1 in both `pyproject.toml` and `scripts/__init__.py`
- ✅ Commit the version bump
- ✅ Create tag v1.1.1 (pointing to correct commit)
- ✅ Create release v1.1.1
- ✅ Trigger build and publish to PyPI automatically

### Step 3: Verify

1. Check workflow completes successfully
1. Verify release appears on GitHub: https://github.com/saint2706/Games/releases/tag/v1.1.1
1. Verify package on PyPI: https://pypi.org/project/games-collection/1.1.1/

______________________________________________________________________

## Alternative Fix: Option B (Move to v1.1.2)

If you don't want to deal with deleting tags, just skip v1.1.1:

### Step 1: Acknowledge Failed Release

The v1.1.1 release remains as-is (you can edit the description to mark it as failed).

### Step 2: Create v1.1.2

1. Go to: **Actions** → **Publish to PyPI** → **Run workflow**
1. Configure:
   - **Branch:** master
   - **Bump version:** patch (1.1.0 → 1.1.1 → 1.1.2, but workflow handles this)
1. Click **Run workflow**

**Note:** You may need to manually update to 1.1.2:

```bash
sed -i 's/version = "1.1.0"/version = "1.1.2"/' pyproject.toml
sed -i 's/__version__ = "1.1.0"/__version__ = "1.1.2"/' scripts/__init__.py
git add pyproject.toml scripts/__init__.py
git commit -m "chore: bump version to 1.1.2"
git push
```

Then use the workflow with branch master and it will create v1.1.2.

______________________________________________________________________

## What's Been Fixed for the Future

Your repository now has safeguards to prevent this from happening again:

### 1. Version Validation Job

The `publish-pypi.yml` workflow now has a `validate-version` job that:

- ✅ Runs automatically on every release event
- ✅ Checks that git tag matches `pyproject.toml` version
- ✅ Checks that git tag matches `scripts/__init__.py` version
- ✅ Fails fast with clear error messages if versions don't match
- ✅ Prevents wasted build time and confusing PyPI errors

### 2. Version Consistency Checker Script

New script: `scripts/check_version_consistency.py`

**Usage:**

```bash
# Check current version consistency
python scripts/check_version_consistency.py

# Check against a specific tag
python scripts/check_version_consistency.py --tag v1.2.3
```

**Example Output (Success):**

```
Version Check Results:
  pyproject.toml: 1.1.1
  scripts/__init__.py: 1.1.1
  Git tag: 1.1.1

✅ Version Consistency Check PASSED
   All versions match: 1.1.1
```

**Example Output (Failure):**

```
Version Check Results:
  pyproject.toml: 1.0.1
  scripts/__init__.py: 1.0.1
  Git tag: 1.1.1

❌ Version Consistency Check FAILED:
  • Version mismatch: Git tag (1.1.1) != pyproject.toml (1.0.1)
  • Version mismatch: Git tag (1.1.1) != scripts/__init__.py (1.0.1)
```

### 3. Comprehensive Documentation

New guides created:

- **[PYPI_PUBLISHING_GUIDE.md](../development/PYPI_PUBLISHING_GUIDE.md)** - Complete guide to proper releases
- **[PYPI_PUBLISH_DEBUG_RUN_18520989869.md](PYPI_PUBLISH_DEBUG_RUN_18520989869.md)** - Detailed analysis of this failure

______________________________________________________________________

## Key Lessons

1. ✅ **Always use the automated workflow** for version bumps and releases
1. ✅ **Never create tags manually** - Let the workflow do it
1. ✅ **Version consistency is critical** - Tag name must match code version
1. ✅ **PyPI versions are permanent** - Can't overwrite or delete
1. ✅ **Validation catches errors early** - Before wasting time on builds

______________________________________________________________________

## Testing Your Fix

After recreating v1.1.1 (or creating v1.1.2):

```bash
# Create a test environment
python -m venv test-env
source test-env/bin/activate

# Install from PyPI
pip install games-collection==1.1.1  # or 1.1.2

# Test it works
games-collection --help
python -m card_games.poker --help

# Clean up
deactivate
rm -rf test-env
```

______________________________________________________________________

## Need Help?

- **PyPI Publishing Guide:** [docs/development/PYPI_PUBLISHING_GUIDE.md](../development/PYPI_PUBLISHING_GUIDE.md)
- **Full Debug Report:** [PYPI_PUBLISH_DEBUG_RUN_18520989869.md](PYPI_PUBLISH_DEBUG_RUN_18520989869.md)
- **Version Checker:** `python scripts/check_version_consistency.py --help`

______________________________________________________________________

## Quick Commands Reference

```bash
# Delete release and tag (Option A)
gh release delete v1.1.1 --yes
git push --delete origin v1.1.1
git tag -d v1.1.1

# Check version consistency
python scripts/check_version_consistency.py

# Manual version bump (if needed)
sed -i 's/version = "OLD"/version = "NEW"/' pyproject.toml
sed -i 's/__version__ = "OLD"/__version__ = "NEW"/' scripts/__init__.py

# Validate before committing
python scripts/check_version_consistency.py --tag vNEW
```

______________________________________________________________________

**Status:** Issue identified and fixed ✅\
**Prevention:** Validation added to workflow ✅\
**Documentation:** Complete ✅\
**Action Required:** Choose Option A or B above to complete the fix
