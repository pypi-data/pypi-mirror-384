"""Tests for the init command."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext


def create_isolated_shell_rc(shell: str, initial_content: str = "") -> Path:
    """Create an isolated shell rc file in a temporary directory.

    Args:
        shell: Shell type ('bash', 'zsh', or 'fish')
        initial_content: Initial content to write to the file

    Returns:
        Path to the created rc file in an isolated temp directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=f"test_shell_{shell}_"))

    if shell == "bash":
        rc_file = temp_dir / ".bashrc"
    elif shell == "zsh":
        rc_file = temp_dir / ".zshrc"
    elif shell == "fish":
        rc_file = temp_dir / ".config" / "fish" / "config.fish"
        rc_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        raise ValueError(f"Unsupported shell: {shell}")

    rc_file.write_text(initial_content, encoding="utf-8")
    return rc_file


def test_init_creates_global_config_first_time() -> None:
    """Test that init creates global config on first run."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\nn\n")

        assert result.exit_code == 0, result.output
        assert "Global config not found" in result.output
        assert "Created global config" in result.output
        assert global_config_ops.exists()


def test_init_prompts_for_workstacks_root() -> None:
    """Test that init prompts for workstacks root when creating config."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "my-workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\nn\n")

        assert result.exit_code == 0, result.output
        assert "Worktrees root directory" in result.output
        assert global_config_ops.get_workstacks_root() == workstacks_root.resolve()


def test_init_detects_graphite_installed() -> None:
    """Test that init detects when Graphite (gt) is installed."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(installed_tools={"gt": "/usr/local/bin/gt"}),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\nn\n")

        assert result.exit_code == 0, result.output
        assert "Graphite (gt) detected" in result.output
        assert global_config_ops.get_use_graphite()


def test_init_detects_graphite_not_installed() -> None:
    """Test that init detects when Graphite (gt) is NOT installed."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\nn\n")

        assert result.exit_code == 0, result.output
        assert "Graphite (gt) not detected" in result.output
        assert not global_config_ops.get_use_graphite()


def test_init_skips_global_with_repo_flag() -> None:
    """Test that --repo flag skips global config creation."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--repo"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "Global config not found" not in result.output
        assert (cwd / "config.toml").exists()


def test_init_fails_repo_flag_without_global_config() -> None:
    """Test that --repo flag fails when global config doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--repo"], obj=test_ctx)

        assert result.exit_code == 1
        assert "Global config not found" in result.output
        assert "Run 'workstack init' without --repo" in result.output


def test_init_auto_preset_detects_dagster() -> None:
    """Test that auto preset detects dagster repo and uses dagster preset."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create pyproject.toml with dagster as the project name
        pyproject = cwd / "pyproject.toml"
        pyproject.write_text('[project]\nname = "dagster"\n', encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Config should be created in workstacks_dir
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert config_path.exists()


def test_init_auto_preset_uses_generic_fallback() -> None:
    """Test that auto preset falls back to generic for non-dagster repos."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create pyproject.toml with different project name
        pyproject = cwd / "pyproject.toml"
        pyproject.write_text('[project]\nname = "myproject"\n', encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert config_path.exists()


def test_init_explicit_preset_dagster() -> None:
    """Test that explicit --preset dagster uses dagster preset."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--preset", "dagster"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert config_path.exists()


def test_init_explicit_preset_generic() -> None:
    """Test that explicit --preset generic uses generic preset."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--preset", "generic"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert config_path.exists()


def test_init_list_presets_displays_available() -> None:
    """Test that --list-presets displays available presets."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--list-presets"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "Available presets:" in result.output
        assert "dagster" in result.output
        assert "generic" in result.output


def test_init_invalid_preset_fails() -> None:
    """Test that invalid preset name fails with helpful error."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--preset", "nonexistent"], obj=test_ctx)

        assert result.exit_code == 1
        assert "Invalid preset 'nonexistent'" in result.output


def test_init_creates_config_at_workstacks_dir() -> None:
    """Test that init creates config.toml in workstacks_dir by default."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Config should be in workstacks_dir, not repo root
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert config_path.exists()
        assert not (cwd / "config.toml").exists()


def test_init_repo_flag_creates_config_at_root() -> None:
    """Test that --repo creates config.toml at repo root."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--repo"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Config should be at repo root
        config_path = cwd / "config.toml"
        assert config_path.exists()


def test_init_force_overwrites_existing_config() -> None:
    """Test that --force overwrites existing config."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        # Create existing config
        config_path = workstacks_dir / "config.toml"
        config_path.write_text("# Old config\n", encoding="utf-8")

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init", "--force"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert config_path.exists()
        # Verify content was overwritten (shouldn't contain "Old config")
        content = config_path.read_text(encoding="utf-8")
        assert "# Old config" not in content


def test_init_fails_without_force_when_exists() -> None:
    """Test that init fails when config exists without --force."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        # Create existing config
        config_path = workstacks_dir / "config.toml"
        config_path.write_text("# Existing config\n", encoding="utf-8")

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx)

        assert result.exit_code == 1
        assert "Config already exists" in result.output
        assert "Use --force to overwrite" in result.output


def test_init_adds_plan_md_to_gitignore() -> None:
    """Test that init offers to add .PLAN.md to .gitignore."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create .gitignore
        gitignore = cwd / ".gitignore"
        gitignore.write_text("*.pyc\n", encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Accept both prompts (y for .PLAN.md, y for .env)
        result = runner.invoke(cli, ["init"], obj=test_ctx, input="y\ny\n")

        assert result.exit_code == 0, result.output
        gitignore_content = gitignore.read_text(encoding="utf-8")
        assert ".PLAN.md" in gitignore_content


def test_init_adds_env_to_gitignore() -> None:
    """Test that init offers to add .env to .gitignore."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create .gitignore
        gitignore = cwd / ".gitignore"
        gitignore.write_text("*.pyc\n", encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Accept both prompts
        result = runner.invoke(cli, ["init"], obj=test_ctx, input="y\ny\n")

        assert result.exit_code == 0, result.output
        gitignore_content = gitignore.read_text(encoding="utf-8")
        assert ".env" in gitignore_content


def test_init_skips_gitignore_entries_if_declined() -> None:
    """Test that init skips gitignore entries if user declines."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create .gitignore
        gitignore = cwd / ".gitignore"
        gitignore.write_text("*.pyc\n", encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Decline both prompts
        result = runner.invoke(cli, ["init"], obj=test_ctx, input="n\nn\n")

        assert result.exit_code == 0, result.output
        gitignore_content = gitignore.read_text(encoding="utf-8")
        assert ".PLAN.md" not in gitignore_content
        assert ".env" not in gitignore_content


def test_init_handles_missing_gitignore() -> None:
    """Test that init handles missing .gitignore gracefully."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # No .gitignore file

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Should not crash or prompt about gitignore


def test_init_preserves_gitignore_formatting() -> None:
    """Test that init preserves existing gitignore formatting."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create .gitignore with specific formatting
        gitignore = cwd / ".gitignore"
        original_content = "# Python\n*.pyc\n__pycache__/\n"
        gitignore.write_text(original_content, encoding="utf-8")

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Accept both prompts
        result = runner.invoke(cli, ["init"], obj=test_ctx, input="y\ny\n")

        assert result.exit_code == 0, result.output
        gitignore_content = gitignore.read_text(encoding="utf-8")
        # Original content should be preserved
        assert "# Python" in gitignore_content
        assert "*.pyc" in gitignore_content
        # New entries should be added
        assert ".PLAN.md" in gitignore_content
        assert ".env" in gitignore_content


def test_init_first_time_offers_shell_setup() -> None:
    """Test that first-time init offers shell integration setup."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated bashrc in temporary directory
        bashrc = create_isolated_shell_rc("bash")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        # Provide input: workstacks_root, decline shell setup
        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\nn\n")

        assert result.exit_code == 0, result.output
        # Should mention shell integration
        assert "shell integration" in result.output.lower()


def test_init_shell_flag_only_setup() -> None:
    """Test that --shell flag only performs shell setup."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=True, workstacks_root=workstacks_root)

        # Create isolated bashrc in temporary directory
        bashrc = create_isolated_shell_rc("bash")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        # Decline shell setup
        result = runner.invoke(cli, ["init", "--shell"], obj=test_ctx, input="n\n")

        assert result.exit_code == 0, result.output
        # Should mention shell but not create config
        workstacks_dir = workstacks_root / cwd.name
        config_path = workstacks_dir / "config.toml"
        assert not config_path.exists()


def test_init_detects_bash_shell() -> None:
    """Test that init correctly detects bash shell."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated bashrc in temporary directory
        bashrc = create_isolated_shell_rc("bash")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\nn\n",
        )

        assert result.exit_code == 0, result.output
        assert "bash" in result.output.lower()


def test_init_detects_zsh_shell() -> None:
    """Test that init correctly detects zsh shell."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated zshrc in temporary directory
        zshrc = create_isolated_shell_rc("zsh")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("zsh", zshrc)),
            dry_run=False,
        )

        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\nn\n",
        )

        assert result.exit_code == 0, result.output
        assert "zsh" in result.output.lower()


def test_init_detects_fish_shell() -> None:
    """Test that init correctly detects fish shell."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated fish config in temporary directory
        fish_config = create_isolated_shell_rc("fish")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("fish", fish_config)),
            dry_run=False,
        )

        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\nn\n",
        )

        assert result.exit_code == 0, result.output
        assert "fish" in result.output.lower()


def test_init_skips_unknown_shell() -> None:
    """Test that init skips shell setup for unknown shells."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=None),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input=f"{workstacks_root}\n")

        assert result.exit_code == 0, result.output
        assert "Unable to detect shell" in result.output


def test_init_adds_completion_to_rc_file() -> None:
    """Test that init adds completion line to rc file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated bashrc in temporary directory
        bashrc = create_isolated_shell_rc("bash", "# Existing content\n")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        # Accept shell setup and both prompts (completion and wrapper)
        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\ny\ny\ny\n",
        )

        assert result.exit_code == 0, result.output
        bashrc_content = bashrc.read_text(encoding="utf-8")
        assert "workstack completion" in bashrc_content


def test_init_adds_wrapper_to_rc_file() -> None:
    """Test that init adds wrapper function to rc file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated bashrc in temporary directory
        bashrc = create_isolated_shell_rc("bash", "# Existing content\n")

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        # Accept shell setup and both prompts
        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\ny\ny\ny\n",
        )

        assert result.exit_code == 0, result.output
        bashrc_content = bashrc.read_text(encoding="utf-8")
        assert "workstack" in bashrc_content


def test_init_skips_shell_if_declined() -> None:
    """Test that init skips shell setup if user declines."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(exists=False)

        # Create isolated bashrc in temporary directory
        original_content = "# Existing content\n"
        bashrc = create_isolated_shell_rc("bash", original_content)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(detected_shell=("bash", bashrc)),
            dry_run=False,
        )

        # Decline shell setup
        result = runner.invoke(
            cli,
            ["init"],
            obj=test_ctx,
            input=f"{workstacks_root}\nn\n",
        )

        assert result.exit_code == 0, result.output
        bashrc_content = bashrc.read_text(encoding="utf-8")
        # Should not modify bashrc
        assert bashrc_content == original_content


def test_init_not_in_git_repo_fails() -> None:
    """Test that init fails when not in a git repository."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # No .git directory

        git_ops = FakeGitOps()  # Empty, no git_common_dirs
        global_config_ops = FakeGlobalConfigOps(exists=False)

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["init"], obj=test_ctx, input="/tmp/workstacks\n")

        # The command should fail at repo discovery
        assert result.exit_code != 0
