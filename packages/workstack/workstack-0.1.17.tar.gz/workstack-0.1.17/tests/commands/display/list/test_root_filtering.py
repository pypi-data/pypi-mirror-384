"""Tests for root worktree stack filtering behavior.

These tests verify that root worktree shows only ancestors + current branch,
while other worktrees show full context with checked-out descendants.

## Bug History

Before the fix (commit XXXX), the code had special handling for "trunk" branches
that would show descendants if they had worktrees. This caused incorrect behavior:

    root [main]
      ◯  feature-b    <- WRONG: showed descendant with worktree
      ◉  main

The fix replaced `is_trunk` logic with `is_root_worktree` logic, which correctly
shows only ancestors + current for the root worktree:

    root [main]
      ◉  main         <- CORRECT: only trunk shown

These tests would have failed with the old implementation, catching the regression.
"""

import json
from pathlib import Path

from click.testing import CliRunner

from tests.commands.display.list import strip_ansi
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.gitops import WorktreeInfo


def test_root_on_trunk_shows_only_trunk() -> None:
    """Root worktree on trunk branch shows only the trunk itself (no descendants).

    Setup:
        - Stack: main → feature-a → feature-b
        - Root on main (trunk)
        - Worktree on feature-b

    Before fix:
        root [main]
          ◯  feature-b    <- WRONG: showed descendant with worktree
          ◉  main

    After fix:
        root [main]
          ◉  main         <- CORRECT: only trunk shown
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache: main → feature-a → feature-b
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-a"]}],
                ["feature-a", {"parentBranchName": "main", "children": ["feature-b"]}],
                ["feature-b", {"parentBranchName": "feature-a", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create feature-b worktree
        repo_name = cwd.name
        workstacks_dir = workstacks_root / repo_name
        feature_b_dir = workstacks_dir / "feature-b"
        feature_b_dir.mkdir(parents=True)

        # Build fake git ops - root on main, feature-b worktree
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=feature_b_dir, branch="feature-b"),
                ],
            },
            git_common_dirs={
                cwd: git_dir,
                feature_b_dir: git_dir,
            },
            current_branches={
                cwd: "main",
                feature_b_dir: "feature-b",
            },
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Strip ANSI codes for easier assertion
        output = strip_ansi(result.output)
        lines = output.strip().splitlines()

        # Find root and feature-b sections
        root_section_start = None
        feature_b_section_start = None
        for i, line in enumerate(lines):
            if line.startswith("root ["):
                root_section_start = i
            if line.startswith("feature-b ["):
                feature_b_section_start = i

        assert root_section_start is not None
        assert feature_b_section_start is not None

        # Get root section (from root header to feature-b header)
        root_section = lines[root_section_start:feature_b_section_start]
        root_section_text = "\n".join(root_section)

        # Root should show ONLY main (no descendants, even with worktrees)
        assert "◉  main" in root_section_text, "Root should show main"
        assert "feature-a" not in root_section_text, (
            f"Root should NOT show feature-a (descendant). Root section:\n{root_section_text}"
        )
        assert "feature-b" not in root_section_text, (
            "Root should NOT show feature-b even though it has a worktree. "
            f"Root section:\n{root_section_text}"
        )


def test_root_on_non_trunk_shows_ancestors_only() -> None:
    """Root worktree on non-trunk branch shows ancestors + current (no descendants).

    Setup:
        - Stack: main → feature-a → feature-b → feature-c
        - Root on feature-b
        - Worktree on feature-c

    Expected:
        root [feature-b]
          ◉  feature-b       <- current
          ◯  feature-a       <- ancestor
          ◯  main            <- ancestor
                             <- feature-c NOT shown (descendant)

        feature-c [feature-c]
          ◉  feature-c
          ◯  feature-b
          ◯  feature-a
          ◯  main
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache: main → feature-a → feature-b → feature-c
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-a"]}],
                ["feature-a", {"parentBranchName": "main", "children": ["feature-b"]}],
                ["feature-b", {"parentBranchName": "feature-a", "children": ["feature-c"]}],
                ["feature-c", {"parentBranchName": "feature-b", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create feature-c worktree
        repo_name = cwd.name
        workstacks_dir = workstacks_root / repo_name
        feature_c_dir = workstacks_dir / "feature-c"
        feature_c_dir.mkdir(parents=True)

        # Build fake git ops - root on feature-b, feature-c worktree
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="feature-b"),
                    WorktreeInfo(path=feature_c_dir, branch="feature-c"),
                ],
            },
            git_common_dirs={
                cwd: git_dir,
                feature_c_dir: git_dir,
            },
            current_branches={
                cwd: "feature-b",
                feature_c_dir: "feature-c",
            },
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Strip ANSI codes for easier assertion
        output = strip_ansi(result.output)
        lines = output.strip().splitlines()

        # Find root and feature-c sections
        root_section_start = None
        feature_c_section_start = None
        for i, line in enumerate(lines):
            if line.startswith("root ["):
                root_section_start = i
            if line.startswith("feature-c ["):
                feature_c_section_start = i

        assert root_section_start is not None
        assert feature_c_section_start is not None

        # Get root section (from root header to feature-c header)
        root_section = lines[root_section_start:feature_c_section_start]
        root_section_text = "\n".join(root_section)

        # Root should show: feature-b (current), feature-a (ancestor), main (ancestor)
        # But NOT feature-c (descendant)
        assert "◉  feature-b" in root_section_text, "Root should show feature-b (current)"
        assert "◯  feature-a" in root_section_text, "Root should show feature-a (ancestor)"
        assert "◯  main" in root_section_text, "Root should show main (ancestor)"
        assert "feature-c" not in root_section_text, (
            f"Root should NOT show feature-c (descendant). Root section:\n{root_section_text}"
        )

        # Get feature-c section (from feature-c header to end)
        feature_c_section = lines[feature_c_section_start:]
        feature_c_section_text = "\n".join(feature_c_section)

        # Feature-c worktree should show full stack (all ancestors)
        assert "◉  feature-c" in feature_c_section_text
        assert "◯  feature-b" in feature_c_section_text
        assert "◯  feature-a" in feature_c_section_text
        assert "◯  main" in feature_c_section_text


def test_non_root_worktree_shows_descendants_with_worktrees() -> None:
    """Non-root worktrees show descendants that are checked out somewhere.

    Setup:
        - Stack: main → feature-a → feature-b → feature-c
        - Root on main
        - Worktree-a on feature-a
        - Worktree-c on feature-c

    Expected:
        root [main]
          ◉  main            <- only main (no descendants for root)

        worktree-a [feature-a]
          ◉  feature-a       <- current
          ◯  main            <- ancestor
          ◯  feature-c       <- descendant with worktree (skips feature-b)
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache: main → feature-a → feature-b → feature-c
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-a"]}],
                ["feature-a", {"parentBranchName": "main", "children": ["feature-b"]}],
                ["feature-b", {"parentBranchName": "feature-a", "children": ["feature-c"]}],
                ["feature-c", {"parentBranchName": "feature-b", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create worktrees
        repo_name = cwd.name
        workstacks_dir = workstacks_root / repo_name
        feature_a_dir = workstacks_dir / "worktree-a"
        feature_c_dir = workstacks_dir / "worktree-c"
        feature_a_dir.mkdir(parents=True)
        feature_c_dir.mkdir(parents=True)

        # Build fake git ops
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=feature_a_dir, branch="feature-a"),
                    WorktreeInfo(path=feature_c_dir, branch="feature-c"),
                ],
            },
            git_common_dirs={
                cwd: git_dir,
                feature_a_dir: git_dir,
                feature_c_dir: git_dir,
            },
            current_branches={
                cwd: "main",
                feature_a_dir: "feature-a",
                feature_c_dir: "feature-c",
            },
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Strip ANSI codes for easier assertion
        output = strip_ansi(result.output)
        lines = output.strip().splitlines()

        # Find sections
        root_section_start = None
        worktree_a_section_start = None
        worktree_c_section_start = None
        for i, line in enumerate(lines):
            if line.startswith("root ["):
                root_section_start = i
            if line.startswith("worktree-a ["):
                worktree_a_section_start = i
            if line.startswith("worktree-c ["):
                worktree_c_section_start = i

        assert root_section_start is not None
        assert worktree_a_section_start is not None
        assert worktree_c_section_start is not None

        # Get root section
        root_section = lines[root_section_start:worktree_a_section_start]
        root_section_text = "\n".join(root_section)

        # Root should show only main
        assert "◉  main" in root_section_text
        assert "feature-a" not in root_section_text
        assert "feature-c" not in root_section_text

        # Get worktree-a section
        worktree_a_section = lines[worktree_a_section_start:worktree_c_section_start]
        worktree_a_section_text = "\n".join(worktree_a_section)

        # Worktree-a should show: feature-a (current), main (ancestor), feature-c (descendant)
        # But NOT feature-b (no worktree)
        assert "◉  feature-a" in worktree_a_section_text
        assert "◯  main" in worktree_a_section_text
        assert "◯  feature-c" in worktree_a_section_text, (
            "worktree-a should show feature-c (descendant with worktree). "
            f"Section:\n{worktree_a_section_text}"
        )
        assert "feature-b" not in worktree_a_section_text, (
            "worktree-a should NOT show feature-b (no worktree). "
            f"Section:\n{worktree_a_section_text}"
        )
