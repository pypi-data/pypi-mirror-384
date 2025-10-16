# Running GitHub Actions Workflows Locally

This guide explains how to run and debug GitHub Actions workflows locally using `act`, a tool that runs your workflows in
Docker containers.

## Table of Contents

- [Why Run Workflows Locally?](#why-run-workflows-locally)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Running Specific Workflows](#running-specific-workflows)
- [Advanced Usage](#advanced-usage)
- [Debugging Workflows](#debugging-workflows)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Why Run Workflows Locally?

Running GitHub Actions workflows locally offers several benefits:

- **Faster feedback**: Test changes without pushing to GitHub
- **Cost savings**: Avoid using GitHub Actions minutes for debugging
- **Easier debugging**: Use local tools to inspect container state
- **Offline development**: Work without internet connectivity
- **Experimentation**: Try workflow changes safely before committing

## Prerequisites

### Required

- **Docker**: Act runs workflows in Docker containers
  - Install from [docker.com](https://www.docker.com/get-started)
  - Ensure Docker daemon is running: `docker ps`
  - At least 10GB of free disk space for container images

### Optional

- **Python 3.9+**: For Python-specific workflows
- **Git**: For version control operations

## Installation

### Automated Installation (Linux/macOS)

Run the setup script:

```bash
./scripts/setup_act.sh
```

This script will:

- Detect your operating system
- Download and install the latest version of `act`
- Configure your PATH (if needed)
- Verify the installation

### Manual Installation

#### macOS

```bash
brew install act
```

#### Linux

```bash
# Download latest release
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or manually from GitHub releases
VERSION=0.2.54  # Check for latest version
wget https://github.com/nektos/act/releases/download/v${VERSION}/act_Linux_x86_64.tar.gz
tar xzf act_Linux_x86_64.tar.gz
sudo mv act /usr/local/bin/
```

#### Windows

Using Chocolatey:

```powershell
choco install act-cli
```

Using Scoop:

```powershell
scoop install act
```

Using winget:

```powershell
winget install nektos.act
```

### Verify Installation

```bash
act --version
```

You should see output like: `act version 0.2.54`

## Quick Start

### 1. First Run

The first time you run `act`, it will prompt you to choose a Docker image size:

```bash
cd /path/to/Games
act --list
```

Choose "Medium" for the best balance of speed and compatibility.

### 2. Run a Workflow

Use the convenience script to run workflows:

```bash
# Run the main CI workflow
./scripts/run_workflow.sh ci

# Run the linting workflow
./scripts/run_workflow.sh lint

# Run the test workflow
./scripts/run_workflow.sh test
```

### 3. List Available Workflows

```bash
./scripts/run_workflow.sh all
```

## GUI Workflow Environment Variables

Some workflows (CI, manual tests, coverage, and mutation testing) exercise PyQt-based GUI code. When running these workflows
locally with `act`, configure the environment to use Qt's offscreen platform plugin and provide a writable XDG runtime
directory:

```bash
mkdir -p /tmp/qt-runtime
chmod 700 /tmp/qt-runtime

act --env QT_QPA_PLATFORM=offscreen --env XDG_RUNTIME_DIR=/tmp/qt-runtime
```

You can also place the variables in an `.env` file for reuse:

```ini
QT_QPA_PLATFORM=offscreen
XDG_RUNTIME_DIR=/tmp/qt-runtime
```

Ensuring these variables are present prevents Qt from trying to access a real display server, allowing PyQt tests to run
headlessly both locally and in GitHub Actions.

## Running Specific Workflows

### Available Workflows

The project includes several workflows you can run locally:

| Workflow | Command | Description |
| --------------- | ---------------------------------- | --------------------------------- |
| CI | `./scripts/run_workflow.sh ci` | Lint and test (main workflow) |
| Lint | `./scripts/run_workflow.sh lint` | Format and lint code |
| Tests | `./scripts/run_workflow.sh test` | Run test suite |
| Coverage | `./scripts/run_workflow.sh coverage` | Generate coverage reports |
| Mutation | `./scripts/run_workflow.sh mutation` | Run mutation tests |
| Build | `./scripts/run_workflow.sh build` | Build executables |
| CodeQL | `./scripts/run_workflow.sh codeql` | Security analysis |
| PyPI Publishing | `./scripts/run_workflow.sh publish --job build` | Test package build (publish requires credentials) |

### Running Specific Jobs

Most workflows have multiple jobs. To run only a specific job:

```bash
# Run only the lint job from the CI workflow
./scripts/run_workflow.sh ci --job lint

# Run only the test job from the CI workflow
./scripts/run_workflow.sh ci --job test

# List all jobs in a workflow
./scripts/run_workflow.sh ci --list-jobs
```

### Using Custom Event Payloads

Workflows can be triggered by different events (push, pull_request, workflow_dispatch, release, schedule, etc.). The
script automatically detects the primary event type from the workflow file, prioritizing in this order:

1. `release` - For release/publish workflows
1. `schedule` - For scheduled/cron workflows
1. `pull_request` - For PR-triggered workflows
1. `workflow_dispatch` - For manually triggered workflows
1. `push` - Default fallback

You can also provide custom event payloads:

```bash
# Run with a custom push event
./scripts/run_workflow.sh ci --event .github/workflows/events/push.json

# Run with a custom pull request event
./scripts/run_workflow.sh ci --event .github/workflows/events/pull_request.json

# Run a workflow_dispatch workflow with inputs
./scripts/run_workflow.sh test --event .github/workflows/events/workflow_dispatch.json

# Test package build locally (publish workflow, build job only)
./scripts/run_workflow.sh publish --job build --event .github/workflows/events/release.json

# Note: Full publish requires PyPI credentials and should only run on GitHub Actions
```

## Advanced Usage

### Using act Directly

For more control, use `act` directly:

```bash
# List all workflows and their jobs
act --list

# Run a specific workflow file
act -W .github/workflows/ci.yml

# Run a specific job
act -W .github/workflows/ci.yml --job lint

# Run with secrets
act -W .github/workflows/ci.yml --secret-file .secrets

# Run with environment variables
act -W .github/workflows/ci.yml --env VAR=value

# Dry run (show what would run without executing)
act -W .github/workflows/ci.yml --dryrun

# Verbose output for debugging
act -W .github/workflows/ci.yml --verbose

# Run on specific platform
act -W .github/workflows/ci.yml -P ubuntu-latest=node:16-buster
```

### Configuration Files

#### .actrc

The `.actrc` file in the project root configures default behavior:

```
# Use medium Docker images
-P ubuntu-latest=catthehacker/ubuntu:act-latest

# Reuse containers for speed
--reuse

# Bind project directory
--bind

# Enable network access
--container-options "--network host"
```

You can override these defaults with command-line flags.

#### .secrets

For workflows that require secrets:

1. Copy the example file: `cp .secrets.example .secrets`
1. Add your secrets to `.secrets`
1. **Never commit `.secrets`** (it's in `.gitignore`)

Example `.secrets` file:

```
GITHUB_TOKEN=ghp_your_token_here
CODECOV_TOKEN=your_codecov_token
```

**Note**: The PyPI publishing workflow uses GitHub's trusted publishing (OIDC) and does not require API tokens. Publishing only occurs on GitHub Actions when a release is created. Local testing is limited to the build step.

### Environment Variables

Set environment variables for workflows:

```bash
# Using command line
act -W .github/workflows/ci.yml --env PYTHON_VERSION=3.12

# Using .env file
echo "PYTHON_VERSION=3.12" > .env
act -W .github/workflows/ci.yml --env-file .env
```

### Platform Selection

Choose different Docker images for different needs:

```bash
# Use micro image (fastest, but may be missing tools)
act -P ubuntu-latest=node:16-alpine

# Use medium image (recommended)
act -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Use large image (slowest, but most compatible)
act -P ubuntu-latest=catthehacker/ubuntu:full-latest

# Use official GitHub image (largest, exact CI environment)
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
```

## Debugging Workflows

### Verbose Output

Enable verbose logging to see detailed execution:

```bash
./scripts/run_workflow.sh ci --verbose
```

### Interactive Debugging

Use `act`'s debugging features:

```bash
# Run with shell access on failure
act -W .github/workflows/ci.yml --shell

# Keep container running after failure
act -W .github/workflows/ci.yml --keep

# Run specific step and stop
act -W .github/workflows/ci.yml --step "Install dependencies"
```

### Inspecting Containers

While a workflow is running, inspect the container:

```bash
# In another terminal, list running containers
docker ps

# Execute commands in the running container
docker exec -it <container_id> bash

# View logs
docker logs <container_id>
```

### Common Debugging Scenarios

#### Workflow Fails Locally But Works on GitHub

This usually means:

1. **Docker image differences**: Try using the large image: `-P ubuntu-latest=catthehacker/ubuntu:full-latest`
1. **Missing secrets**: Ensure all required secrets are in `.secrets`
1. **Environment differences**: Check if the workflow depends on GitHub-specific features

#### Workflow Works on GitHub But Fails Locally

Check for:

1. **Local environment issues**: Ensure Docker is running and has enough resources
1. **Network restrictions**: Some workflows need network access (use `--container-options "--network host"`)
1. **Docker image compatibility**: Try different image sizes

#### Workflow Hangs or Times Out

Try:

1. **Increase Docker resources**: Give Docker more CPU/memory
1. **Use faster image**: Switch to medium or micro image
1. **Run specific jobs**: Use `--job` to isolate the problem

## Troubleshooting

### Docker Issues

#### Error: Cannot connect to Docker daemon

```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# or open Docker Desktop (macOS/Windows)

# Verify Docker is running
docker ps
```

#### Error: No space left on device

```bash
# Clean up Docker images and containers
docker system prune -a

# Remove unused images
docker image prune -a
```

### Act Issues

#### Error: Container image not found

```bash
# Pull the image manually
docker pull catthehacker/ubuntu:act-latest

# Or use a different image
act -P ubuntu-latest=node:16-buster
```

#### Error: Permission denied

On Linux, you may need to:

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker ps
```

### Workflow-Specific Issues

#### Tests fail with import errors

The workflow may not be installing the package correctly. Check:

1. The workflow's installation steps use `pip install -e ".[dev]"`
1. The Python version matches your requirements (3.9+)
1. All dependencies are properly declared in `pyproject.toml`

#### Secrets not working

Ensure:

1. `.secrets` file exists and has correct format: `KEY=value`
1. Secret names match exactly (case-sensitive)
1. No extra spaces around `=`

## Best Practices

### 1. Test Before Pushing

Always test workflow changes locally before pushing:

```bash
# After modifying .github/workflows/ci.yml
./scripts/run_workflow.sh ci
```

### 2. Use Appropriate Image Sizes

- **Development/iteration**: Use micro or medium images for speed
- **Final testing**: Use large image to match GitHub environment
- **Debugging specific issues**: Use full image with all tools

### 3. Keep Secrets Secure

- Never commit `.secrets` file
- Use different secrets for local testing and production
- Rotate secrets regularly

### 4. Optimize Workflow Performance

- Use `--reuse` to reuse containers between runs
- Use `--bind` to avoid copying files into containers
- Cache dependencies when possible

### 5. Debug Systematically

When a workflow fails:

1. Run with `--verbose` to see detailed output
1. Run specific jobs with `--job` to isolate issues
1. Use `--dryrun` to see what would execute
1. Compare with GitHub Actions logs

### 6. Monitor Resource Usage

```bash
# Check Docker disk usage
docker system df

# Monitor running containers
docker stats

# Clean up regularly
docker system prune
```

## Examples

### Example 1: Quick CI Check

```bash
# Before committing, run the CI workflow
./scripts/run_workflow.sh ci

# If it passes, commit and push
git add .
git commit -m "Your changes"
git push
```

### Example 2: Debug Test Failures

```bash
# Run tests with verbose output
./scripts/run_workflow.sh test --verbose

# Run only the test job
./scripts/run_workflow.sh ci --job test

# Keep container for inspection
act -W .github/workflows/ci.yml --job test --keep
```

### Example 3: Test Workflow Changes

```bash
# After modifying a workflow file
./scripts/run_workflow.sh ci --dry-run  # See what would run

# Run for real
./scripts/run_workflow.sh ci

# Run specific job if needed
./scripts/run_workflow.sh ci --job lint
```

### Example 4: Test Multi-Platform Build

```bash
# Test Linux build
./scripts/run_workflow.sh build --job build-pyinstaller

# Note: Cross-platform builds (Windows/macOS) require
# those specific runners and won't work with act on Linux
```

## Integration with Development Workflow

### Pre-Commit Hook

Add a pre-commit hook to automatically test workflows:

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/run_workflow.sh lint --job format-and-lint
```

### CI/CD Pipeline

1. **Local testing**: Run workflows locally during development
1. **Pre-commit**: Quick lint check before committing
1. **Pre-push**: Full CI check before pushing
1. **GitHub Actions**: Final validation on all platforms

## Additional Resources

- [act GitHub Repository](https://github.com/nektos/act)
- [act Documentation](https://github.com/nektos/act/blob/master/README.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
1. Review workflow logs with `--verbose`
1. Search [act issues](https://github.com/nektos/act/issues)
1. Review [GitHub Actions logs](https://github.com/saint2706/Games/actions)

## Summary

Running workflows locally with `act` provides:

- ✅ Faster development iteration
- ✅ Cost savings on CI/CD minutes
- ✅ Better debugging capabilities
- ✅ Offline development support
- ✅ Safer experimentation

Start with:

```bash
# Install act
./scripts/setup_act.sh

# Run your first workflow
./scripts/run_workflow.sh ci

# List all workflows
./scripts/run_workflow.sh all
```

Happy testing! 🚀
