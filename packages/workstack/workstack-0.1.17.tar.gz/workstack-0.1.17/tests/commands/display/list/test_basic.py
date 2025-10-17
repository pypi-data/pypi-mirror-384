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


def test_list_outputs_names_not_paths() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        Path(".git").mkdir()

        # Create worktrees in the location determined by global config
        repo_name = cwd.name
        workstacks_dir = workstacks_root / repo_name
        (workstacks_dir / "foo").mkdir(parents=True)
        (workstacks_dir / "bar").mkdir(parents=True)

        # Build fake git ops with worktree info
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=workstacks_dir / "foo", branch="foo"),
                    WorktreeInfo(path=workstacks_dir / "bar", branch="feature/bar"),
                ],
            },
            git_common_dirs={cwd: cwd / ".git"},
        )

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
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

        result = runner.invoke(cli, ["list"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Strip ANSI codes for easier comparison
        output = strip_ansi(result.output)
        lines = output.strip().splitlines()

        # First line should be root with path
        assert lines[0].startswith("root")
        assert str(cwd) in lines[0]

        # Remaining lines should be worktrees with paths, sorted
        worktree_lines = sorted(lines[1:])
        assert worktree_lines == [
            f"bar [{workstacks_dir / 'bar'}]",
            f"foo [{workstacks_dir / 'foo'}]",
        ]
