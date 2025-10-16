"""Tests for find_worktrees_containing_branch function in graphite.py."""

from pathlib import Path

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from tests.test_utils.graphite_helpers import setup_graphite_stack
from workstack.cli.graphite import find_worktrees_containing_branch
from workstack.core.context import WorkstackContext
from workstack.core.gitops import WorktreeInfo


def test_find_worktrees_containing_branch_single_match(tmp_path: Path) -> None:
    """Test finding a branch that exists in exactly one worktree's stack."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()
    work_dir = tmp_path / "workstacks" / "repo"
    work_dir.mkdir(parents=True)

    # Set up stack: main -> feature-1 -> feature-2
    # Another worktree: main -> other-feature
    setup_graphite_stack(
        git_dir,
        {
            "main": {"parent": None, "children": ["feature-1", "other-feature"], "is_trunk": True},
            "feature-1": {"parent": "main", "children": ["feature-2"]},
            "feature-2": {"parent": "feature-1", "children": []},
            "other-feature": {"parent": "main", "children": []},
        },
    )

    # Worktree 1 has feature-2 checked out (stack: main -> feature-1 -> feature-2)
    # Worktree 2 has other-feature checked out (stack: main -> other-feature)
    wt1_path = work_dir / "feature-2-wt"
    wt2_path = work_dir / "other-wt"

    worktrees = [
        WorktreeInfo(path=repo_root, branch="main"),
        WorktreeInfo(path=wt1_path, branch="feature-2"),
        WorktreeInfo(path=wt2_path, branch="other-feature"),
    ]

    git_ops = FakeGitOps(
        worktrees={repo_root: worktrees},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
    )

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Search for feature-1, which is in the stack of worktree 1 but not worktree 2
    matching = find_worktrees_containing_branch(ctx, repo_root, worktrees, "feature-1")

    # Should find exactly two worktrees (main and feature-2) that contain feature-1 in their stacks
    assert len(matching) == 2
    assert wt1_path in [wt.path for wt in matching]
    assert repo_root in [wt.path for wt in matching]  # main is also in this stack


def test_find_worktrees_containing_branch_multiple_matches(tmp_path: Path) -> None:
    """Test finding a branch that exists in multiple worktrees' stacks."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()
    work_dir = tmp_path / "workstacks" / "repo"
    work_dir.mkdir(parents=True)

    # Set up stack where main is parent of both branches
    # main -> feature-1 -> feature-1-child
    # main -> feature-2 -> feature-2-child
    setup_graphite_stack(
        git_dir,
        {
            "main": {"parent": None, "children": ["feature-1", "feature-2"], "is_trunk": True},
            "feature-1": {"parent": "main", "children": ["feature-1-child"]},
            "feature-1-child": {"parent": "feature-1", "children": []},
            "feature-2": {"parent": "main", "children": ["feature-2-child"]},
            "feature-2-child": {"parent": "feature-2", "children": []},
        },
    )

    wt1_path = work_dir / "feature-1-wt"
    wt2_path = work_dir / "feature-2-wt"
    wt3_path = work_dir / "main-wt"

    worktrees = [
        WorktreeInfo(path=wt3_path, branch="main"),
        WorktreeInfo(path=wt1_path, branch="feature-1-child"),
        WorktreeInfo(path=wt2_path, branch="feature-2-child"),
    ]

    git_ops = FakeGitOps(
        worktrees={repo_root: worktrees},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
    )

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Search for "main" which is in all stacks
    matching = find_worktrees_containing_branch(ctx, repo_root, worktrees, "main")

    # Should find all three worktrees since main is in every stack
    assert len(matching) == 3
    assert {wt.path for wt in matching} == {wt1_path, wt2_path, wt3_path}


def test_find_worktrees_containing_branch_no_match(tmp_path: Path) -> None:
    """Test searching for a branch that doesn't exist in any stack."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()
    work_dir = tmp_path / "workstacks" / "repo"
    work_dir.mkdir(parents=True)

    # Set up stack: main -> feature-1
    setup_graphite_stack(
        git_dir,
        {
            "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
            "feature-1": {"parent": "main", "children": []},
        },
    )

    wt1_path = work_dir / "feature-1-wt"

    worktrees = [
        WorktreeInfo(path=repo_root, branch="main"),
        WorktreeInfo(path=wt1_path, branch="feature-1"),
    ]

    git_ops = FakeGitOps(
        worktrees={repo_root: worktrees},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
    )

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Search for a branch that doesn't exist in any stack
    matching = find_worktrees_containing_branch(ctx, repo_root, worktrees, "nonexistent-branch")

    # Should return empty list
    assert len(matching) == 0
    assert matching == []


def test_find_worktrees_containing_branch_detached_head(tmp_path: Path) -> None:
    """Test that worktrees with detached HEAD are skipped."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()
    work_dir = tmp_path / "workstacks" / "repo"
    work_dir.mkdir(parents=True)

    # Set up stack: main -> feature-1
    setup_graphite_stack(
        git_dir,
        {
            "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
            "feature-1": {"parent": "main", "children": []},
        },
    )

    wt1_path = work_dir / "feature-1-wt"
    wt2_path = work_dir / "detached-wt"

    worktrees = [
        WorktreeInfo(path=repo_root, branch="main"),
        WorktreeInfo(path=wt1_path, branch="feature-1"),
        WorktreeInfo(path=wt2_path, branch=None),  # Detached HEAD
    ]

    git_ops = FakeGitOps(
        worktrees={repo_root: worktrees},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
    )

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Search for feature-1
    matching = find_worktrees_containing_branch(ctx, repo_root, worktrees, "feature-1")

    # Should find two worktrees (main and feature-1), but not the detached HEAD worktree
    assert len(matching) == 2
    assert wt2_path not in [wt.path for wt in matching]
    assert wt1_path in [wt.path for wt in matching]
    assert repo_root in [wt.path for wt in matching]


def test_find_worktrees_containing_branch_no_graphite_cache(tmp_path: Path) -> None:
    """Test that function returns empty list when Graphite cache doesn't exist."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()
    # No graphite cache file created

    work_dir = tmp_path / "workstacks" / "repo"
    work_dir.mkdir(parents=True)

    wt1_path = work_dir / "feature-1-wt"

    worktrees = [
        WorktreeInfo(path=repo_root, branch="main"),
        WorktreeInfo(path=wt1_path, branch="feature-1"),
    ]

    git_ops = FakeGitOps(
        worktrees={repo_root: worktrees},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
    )

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Search for any branch when no cache exists
    matching = find_worktrees_containing_branch(ctx, repo_root, worktrees, "feature-1")

    # Should return empty list since no cache exists
    assert len(matching) == 0
    assert matching == []
