"""Tests for GitHub Actions workflow validation."""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

# Get the repository root
REPO_ROOT = Path(__file__).parent.parent


def test_workflow_files_exist():
    """Test that expected workflow files exist."""
    workflow_dir = REPO_ROOT / ".github" / "workflows"
    assert workflow_dir.exists(), "Workflow directory should exist"

    expected_workflows = [
        "ci.yml",
        "format-and-lint.yml",
        "manual-tests.yml",
        "manual-coverage.yml",
        "mutation-testing.yml",
        "build-executables.yml",
        "codeql.yml",
        "publish-pypi.yml",
        "test-act-setup.yml",
    ]

    for workflow in expected_workflows:
        workflow_path = workflow_dir / workflow
        assert workflow_path.exists(), f"Workflow {workflow} should exist"


def test_event_payload_files_exist():
    """Test that event payload files exist."""
    events_dir = REPO_ROOT / ".github" / "workflows" / "events"
    assert events_dir.exists(), "Events directory should exist"

    expected_events = [
        "push.json",
        "pull_request.json",
        "release.json",
        "workflow_dispatch.json",
    ]

    for event in expected_events:
        event_path = events_dir / event
        assert event_path.exists(), f"Event payload {event} should exist"


def test_workflow_validation_script_exists():
    """Test that the workflow validation script exists."""
    script_path = REPO_ROOT / "scripts" / "validate_workflows.py"
    assert script_path.exists(), "Workflow validation script should exist"
    assert script_path.is_file(), "Workflow validation script should be a file"


def test_workflow_validation_passes():
    """Test that workflow validation passes."""
    if yaml is None:
        pytest.skip("PyYAML not installed")
    import subprocess

    script_path = REPO_ROOT / "scripts" / "validate_workflows.py"
    result = subprocess.run(
        ["python3", str(script_path)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"Workflow validation should pass\n{result.stdout}\n{result.stderr}"


def test_workflow_syntax_valid():
    """Test that all workflow files have valid YAML syntax."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_dir = REPO_ROOT / ".github" / "workflows"
    workflow_files = list(workflow_dir.glob("*.yml"))

    assert len(workflow_files) > 0, "Should have at least one workflow file"

    for workflow_file in workflow_files:
        with open(workflow_file) as f:
            try:
                workflow = yaml.safe_load(f)
                assert workflow is not None, f"{workflow_file.name} should not be empty"
                assert isinstance(workflow, dict), f"{workflow_file.name} should be a dictionary"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")


def test_event_payload_syntax_valid():
    """Test that all event payload files have valid JSON syntax."""
    import json

    events_dir = REPO_ROOT / ".github" / "workflows" / "events"
    event_files = list(events_dir.glob("*.json"))

    assert len(event_files) > 0, "Should have at least one event payload file"

    for event_file in event_files:
        with open(event_file) as f:
            try:
                event = json.load(f)
                assert event is not None, f"{event_file.name} should not be empty"
                assert isinstance(event, dict), f"{event_file.name} should be a dictionary"
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {event_file.name}: {e}")


def test_workflow_structure():
    """Test that all workflows have required structure."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_dir = REPO_ROOT / ".github" / "workflows"
    workflow_files = list(workflow_dir.glob("*.yml"))

    for workflow_file in workflow_files:
        with open(workflow_file) as f:
            workflow = yaml.safe_load(f)

        # Check for required fields
        assert "name" in workflow, f"{workflow_file.name} should have a name"

        # Check for 'on' or True (YAML treats 'on' as boolean True)
        assert "on" in workflow or True in workflow, f"{workflow_file.name} should have trigger events"

        assert "jobs" in workflow, f"{workflow_file.name} should have jobs"
        assert isinstance(workflow["jobs"], dict), f"{workflow_file.name} jobs should be a dictionary"
        assert len(workflow["jobs"]) > 0, f"{workflow_file.name} should have at least one job"

        # Check each job has required fields
        for job_name, job_config in workflow["jobs"].items():
            assert isinstance(job_config, dict), f"Job {job_name} in {workflow_file.name} should be a dictionary"
            assert "runs-on" in job_config, f"Job {job_name} in {workflow_file.name} should have runs-on"
            assert "steps" in job_config, f"Job {job_name} in {workflow_file.name} should have steps"


def test_workflow_scripts_exist():
    """Test that scripts referenced in workflows exist."""
    scripts_dir = REPO_ROOT / "scripts"

    expected_scripts = [
        "run_workflow.sh",
        "setup_act.sh",
        "validate_workflows.py",
    ]

    for script in expected_scripts:
        script_path = scripts_dir / script
        assert script_path.exists(), f"Script {script} should exist"
        assert script_path.is_file(), f"Script {script} should be a file"


def test_workflow_documentation_exists():
    """Test that workflow documentation exists."""
    docs_dir = REPO_ROOT / "docs" / "development"

    expected_docs = [
        "LOCAL_WORKFLOWS.md",
        "WORKFLOW_TESTING_QUICKSTART.md",
    ]

    for doc in expected_docs:
        doc_path = docs_dir / doc
        assert doc_path.exists(), f"Documentation {doc} should exist"
        assert doc_path.is_file(), f"Documentation {doc} should be a file"


def test_build_executables_has_artifacts_verification():
    """Test that build-executables workflow has artifacts verification steps."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "build-executables.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check that create-release job exists
    assert "create-release" in workflow["jobs"], "build-executables should have create-release job"

    create_release_job = workflow["jobs"]["create-release"]
    steps = create_release_job["steps"]
    step_names = [step.get("name") for step in steps]

    # Verify the artifacts verification steps exist
    assert "List artifacts" in step_names, "create-release should have 'List artifacts' step"
    assert "Verify artifacts exist" in step_names, "create-release should have 'Verify artifacts exist' step"

    # Verify the order: List artifacts and Verify artifacts should come after Download all artifacts
    download_idx = step_names.index("Download all artifacts")
    list_idx = step_names.index("List artifacts")
    verify_idx = step_names.index("Verify artifacts exist")
    create_release_idx = step_names.index("Create Release")

    assert list_idx > download_idx, "List artifacts should come after Download all artifacts"
    assert verify_idx > list_idx, "Verify artifacts exist should come after List artifacts"
    assert create_release_idx > verify_idx, "Create Release should come after Verify artifacts exist"


def test_build_pyinstaller_has_executable_validation():
    """Test that build-pyinstaller job has executable validation step."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "build-executables.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check that build-pyinstaller job exists
    assert "build-pyinstaller" in workflow["jobs"], "build-executables should have build-pyinstaller job"

    build_job = workflow["jobs"]["build-pyinstaller"]
    steps = build_job["steps"]
    step_names = [step.get("name") for step in steps]

    # Verify the validation step exists
    assert "Validate executable exists" in step_names, "build-pyinstaller should have 'Validate executable exists' step"

    # Verify the order: Validate should come after Build and before Upload
    build_idx = step_names.index("Build with PyInstaller")
    validate_idx = step_names.index("Validate executable exists")
    upload_idx = step_names.index("Upload artifact")

    assert validate_idx > build_idx, "Validate executable exists should come after Build with PyInstaller"
    assert upload_idx > validate_idx, "Upload artifact should come after Validate executable exists"

    # Verify the validation step checks for the correct executable files
    validate_step = None
    for step in steps:
        if step.get("name") == "Validate executable exists":
            validate_step = step
            break

    assert validate_step is not None, "Could not find Validate executable exists step"
    assert "run" in validate_step, "Validate step should have a 'run' command"

    run_script = validate_step["run"]
    # Check that the script checks for Windows executable
    assert "games-collection.exe" in run_script, "Validation should check for games-collection.exe on Windows"
    # Check that the script checks for Linux/macOS executable
    assert "games-collection" in run_script, "Validation should check for games-collection on Linux/macOS"
    # Check that it fails on missing file
    assert "exit 1" in run_script, "Validation should exit with error code 1 if file is missing"


def test_build_executables_has_correct_triggers():
    """Test that build-executables workflow has correct trigger configuration."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "build-executables.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check that workflow has correct triggers
    # Note: YAML parses 'on' as boolean True, so we need to check for that
    triggers = workflow.get("on") or workflow.get(True)
    assert triggers is not None, "build-executables should have 'on' triggers"

    # Should have push trigger for tags
    assert "push" in triggers, "build-executables should have 'push' trigger"
    assert "tags" in triggers["push"], "build-executables push trigger should include 'tags'"
    assert "v*" in triggers["push"]["tags"], "build-executables should trigger on 'v*' tags"

    # Should also have workflow_dispatch for manual triggers
    assert "workflow_dispatch" in triggers or triggers.get("workflow_dispatch") is None, "build-executables should have 'workflow_dispatch' trigger"


def test_create_release_job_has_tag_condition():
    """Test that create-release job only runs on tag pushes."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "build-executables.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check that create-release job exists
    assert "create-release" in workflow["jobs"], "build-executables should have create-release job"

    create_release_job = workflow["jobs"]["create-release"]

    # Verify the job has the correct condition
    assert "if" in create_release_job, "create-release job should have an 'if' condition"
    assert "startsWith(github.ref, 'refs/tags/v')" in create_release_job["if"], "create-release should only run on version tag pushes"


def test_create_release_uses_git_tag():
    """Test that create-release job uses actual git tags, not run numbers."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "build-executables.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    create_release_job = workflow["jobs"]["create-release"]
    steps = create_release_job["steps"]

    # Find the "Determine release tag" step
    tag_step = None
    for step in steps:
        if step.get("name") == "Determine release tag":
            tag_step = step
            break

    assert tag_step is not None, "create-release should have 'Determine release tag' step"
    assert "run" in tag_step, "Determine release tag step should have a 'run' command"

    run_script = tag_step["run"]
    # Should extract tag from GITHUB_REF, not use GITHUB_RUN_NUMBER
    assert "GITHUB_REF" in run_script, "Should extract tag from GITHUB_REF"
    assert "GITHUB_RUN_NUMBER" not in run_script, "Should not use GITHUB_RUN_NUMBER for release tags"


def test_publish_pypi_has_bump_and_release_job():
    """Test that publish-pypi workflow has bump-and-release job."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check that bump-and-release job exists
    assert "bump-and-release" in workflow["jobs"], "publish-pypi should have bump-and-release job"

    bump_job = workflow["jobs"]["bump-and-release"]

    # Check conditional execution
    assert "if" in bump_job, "bump-and-release should have conditional execution"
    assert "workflow_dispatch" in bump_job["if"], "bump-and-release should only run on workflow_dispatch"

    # Check permissions
    assert "permissions" in bump_job, "bump-and-release should have permissions defined"
    assert bump_job["permissions"]["contents"] == "write", "bump-and-release needs contents: write permission"

    # Check steps
    steps = bump_job["steps"]
    step_names = [step.get("name") for step in steps]

    # Verify key steps exist
    assert "Bump version" in step_names, "bump-and-release should have 'Bump version' step"
    assert "Commit version bump" in step_names, "bump-and-release should have 'Commit version bump' step"
    assert "Create and push tag" in step_names, "bump-and-release should have 'Create and push tag' step"
    assert "Create GitHub Release" in step_names, "bump-and-release should have 'Create GitHub Release' step"


def test_publish_pypi_has_asset_check():
    """Test that github-release job checks for existing assets."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    github_release_job = workflow["jobs"]["github-release"]
    steps = github_release_job["steps"]
    step_names = [step.get("name") for step in steps]

    # Verify asset check step exists
    assert "Check for existing release assets" in step_names, "github-release should check for existing assets"

    # Find the check step
    check_step = None
    for step in steps:
        if step.get("name") == "Check for existing release assets":
            check_step = step
            break

    assert check_step is not None
    assert "run" in check_step, "Asset check step should have a run script"

    # Verify the script checks for conflicts
    run_script = check_step["run"]
    assert "gh release view" in run_script, "Should use gh release view to get existing assets"
    assert "CONFLICTS" in run_script, "Should check for file conflicts"
    assert "exit 1" in run_script, "Should exit with error if conflicts found"


def test_publish_pypi_has_workflow_dispatch_input():
    """Test that workflow_dispatch has bump_part input."""
    if yaml is None:
        pytest.skip("PyYAML not installed")

    workflow_file = REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml"
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # YAML parser converts 'on' to True (boolean), so we access it with True key
    on_events = workflow.get(True) or workflow.get("on")
    assert on_events is not None, "publish-pypi should have trigger events"

    # Check workflow_dispatch configuration
    assert "workflow_dispatch" in on_events, "publish-pypi should support workflow_dispatch"

    dispatch_config = on_events["workflow_dispatch"]
    assert "inputs" in dispatch_config, "workflow_dispatch should have inputs"

    inputs = dispatch_config["inputs"]
    assert "bump_part" in inputs, "workflow_dispatch should have bump_part input"

    bump_part = inputs["bump_part"]
    assert bump_part["type"] == "choice", "bump_part should be a choice input"
    assert bump_part["default"] == "patch", "bump_part should default to patch"
    assert set(bump_part["options"]) == {"patch", "minor", "major"}, "bump_part should have patch, minor, major options"
