"""Tests for the __prepare_cwd_recovery hidden command."""

import os
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.context import create_test_context
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from workstack.cli.commands.prepare_cwd_recovery import prepare_cwd_recovery_cmd
from workstack.core.context import WorkstackContext


def build_ctx(repo_root: Path | None, workstacks_root: Path) -> WorkstackContext:
    """Create a WorkstackContext with test fakes."""
    git_common_dirs: dict[Path, Path] = {}
    if repo_root is not None:
        git_common_dirs[repo_root] = repo_root / ".git"

    git_ops = FakeGitOps(git_common_dirs=git_common_dirs)
    global_config_ops = FakeGlobalConfigOps(workstacks_root=workstacks_root)
    return create_test_context(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        dry_run=False,
    )


def test_prepare_cwd_recovery_outputs_script(tmp_path: Path) -> None:
    """Command should emit a script path when inside a repo."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    workstacks_root = tmp_path / "workstacks"
    workstacks_root.mkdir()

    ctx = build_ctx(repo, workstacks_root)

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(repo)
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    script_path = Path(result.output.strip())
    assert script_path.exists()
    script_path.unlink(missing_ok=True)


def test_prepare_cwd_recovery_no_repo(tmp_path: Path) -> None:
    """Command should emit nothing outside a repository."""
    workstacks_root = tmp_path / "workstacks"
    workstacks_root.mkdir()

    ctx = build_ctx(None, workstacks_root)

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    assert result.output == ""


def test_prepare_cwd_recovery_missing_cwd(tmp_path: Path) -> None:
    """Command should handle missing cwd gracefully."""
    ctx = build_ctx(None, tmp_path)

    broken_dir = tmp_path / "vanish"
    broken_dir.mkdir()

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(broken_dir)
        broken_dir.rmdir()
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    assert result.output == ""
