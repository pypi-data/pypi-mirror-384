"""Unit tests for workstack gt branches command."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from tests.fakes.context import create_test_context
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli.commands.gt import gt_branches_cmd
from workstack.cli.core import RepoContext
from workstack.core.branch_metadata import BranchMetadata


def test_gt_branches_text_format(tmp_path: Path) -> None:
    """Test gt branches command with default text format."""
    # Arrange: Set up branch metadata
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["feat-1"],
            is_trunk=True,
            commit_sha="abc123",
        ),
        "feat-1": BranchMetadata(
            name="feat-1",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="def456",
        ),
        "feat-2": BranchMetadata(
            name="feat-2",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="ghi789",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    git_ops = FakeGitOps(
        git_common_dirs={tmp_path: tmp_path / ".git"},
    )

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    # Mock discover_repo_context to return a test repo
    repo = RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command with default text format
    with patch("workstack.cli.commands.gt.discover_repo_context", return_value=repo):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(gt_branches_cmd, [], obj=ctx, catch_exceptions=False)

    # Assert: Verify success and text output (sorted branch names)
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    assert lines == ["feat-1", "feat-2", "main"]


def test_gt_branches_json_format(tmp_path: Path) -> None:
    """Test gt branches command with JSON format."""
    # Arrange: Set up branch metadata
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["feat-1"],
            is_trunk=True,
            commit_sha="abc123",
        ),
        "feat-1": BranchMetadata(
            name="feat-1",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="def456",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    git_ops = FakeGitOps(
        git_common_dirs={tmp_path: tmp_path / ".git"},
    )

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    repo = RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command with JSON format
    with patch("workstack.cli.commands.gt.discover_repo_context", return_value=repo):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                gt_branches_cmd, ["--format", "json"], obj=ctx, catch_exceptions=False
            )

    # Assert: Verify success and JSON output
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "branches" in data
    assert len(data["branches"]) == 2

    # Verify main branch
    main_branch = next(b for b in data["branches"] if b["name"] == "main")
    assert main_branch["parent"] is None
    assert main_branch["children"] == ["feat-1"]
    assert main_branch["is_trunk"] is True
    assert main_branch["commit_sha"] == "abc123"

    # Verify feat-1 branch
    feat_branch = next(b for b in data["branches"] if b["name"] == "feat-1")
    assert feat_branch["parent"] == "main"
    assert feat_branch["children"] == []
    assert feat_branch["is_trunk"] is False
    assert feat_branch["commit_sha"] == "def456"


def test_gt_branches_empty(tmp_path: Path) -> None:
    """Test gt branches command with no branches."""
    # Arrange: Empty branch data
    graphite_ops = FakeGraphiteOps(branches={})
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    git_ops = FakeGitOps(
        git_common_dirs={tmp_path: tmp_path / ".git"},
    )

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    repo = RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command with default text format - empty should give empty output
    with patch("workstack.cli.commands.gt.discover_repo_context", return_value=repo):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(gt_branches_cmd, [], obj=ctx, catch_exceptions=False)

    # Assert: Verify empty output with success
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_gt_branches_graphite_disabled(tmp_path: Path) -> None:
    """Test gt branches command fails when graphite is disabled."""
    # Arrange: Graphite disabled
    graphite_ops = FakeGraphiteOps()
    global_config_ops = FakeGlobalConfigOps(use_graphite=False)
    git_ops = FakeGitOps()

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command - should fail before discover_repo_context
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(gt_branches_cmd, [], obj=ctx, catch_exceptions=False)

    # Assert: Verify error (fails before discovery, so no need to mock)
    assert result.exit_code == 1
    assert "Graphite not enabled" in result.output


def test_gt_branches_multiple_children(tmp_path: Path) -> None:
    """Test gt branches command with branch that has multiple children."""
    # Arrange: Main with multiple children
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["feat-1", "feat-2"],
            is_trunk=True,
            commit_sha="abc123",
        ),
        "feat-1": BranchMetadata(
            name="feat-1",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="def456",
        ),
        "feat-2": BranchMetadata(
            name="feat-2",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="ghi789",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    git_ops = FakeGitOps(git_common_dirs={tmp_path: tmp_path / ".git"})

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    repo = RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command
    with patch("workstack.cli.commands.gt.discover_repo_context", return_value=repo):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                gt_branches_cmd, ["--format", "json"], obj=ctx, catch_exceptions=False
            )

    # Assert: Verify multiple children properly serialized
    assert result.exit_code == 0

    data = json.loads(result.output)
    main_branch = next(b for b in data["branches"] if b["name"] == "main")
    assert set(main_branch["children"]) == {"feat-1", "feat-2"}


def test_gt_branches_linear_stack(tmp_path: Path) -> None:
    """Test gt branches command with a linear stack."""
    # Arrange: Linear stack: main -> feat-1 -> feat-2
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["feat-1"],
            is_trunk=True,
            commit_sha="aaa111",
        ),
        "feat-1": BranchMetadata(
            name="feat-1",
            parent="main",
            children=["feat-2"],
            is_trunk=False,
            commit_sha="bbb222",
        ),
        "feat-2": BranchMetadata(
            name="feat-2",
            parent="feat-1",
            children=[],
            is_trunk=False,
            commit_sha="ccc333",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    git_ops = FakeGitOps(git_common_dirs={tmp_path: tmp_path / ".git"})

    ctx = create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
    )

    repo = RepoContext(root=tmp_path, repo_name="test-repo", workstacks_dir=tmp_path / "workstacks")

    runner = CliRunner()

    # Act: Execute command
    with patch("workstack.cli.commands.gt.discover_repo_context", return_value=repo):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                gt_branches_cmd, ["--format", "json"], obj=ctx, catch_exceptions=False
            )

    # Assert: Verify linear stack
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert len(data["branches"]) == 3

    # Verify parent-child relationships
    main = next(b for b in data["branches"] if b["name"] == "main")
    feat1 = next(b for b in data["branches"] if b["name"] == "feat-1")
    feat2 = next(b for b in data["branches"] if b["name"] == "feat-2")

    assert main["parent"] is None
    assert feat1["parent"] == "main"
    assert feat2["parent"] == "feat-1"

    assert main["children"] == ["feat-1"]
    assert feat1["children"] == ["feat-2"]
    assert feat2["children"] == []
