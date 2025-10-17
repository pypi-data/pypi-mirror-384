import os
import subprocess
from pathlib import Path

from click.testing import CliRunner

from workstack.cli.commands.shell_integration import hidden_shell_cmd
from workstack.cli.shell_utils import render_cd_script


def test_create_with_plan_file(tmp_path: Path) -> None:
    """Test creating a worktree from a plan file."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "Add_Auth_Feature.md"
    plan_content = "# Auth Feature Plan\n\n- Add login\n- Add signup\n"
    plan_file.write_text(plan_content)

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "Add_Auth_Feature.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree was created with sanitized name
    worktree_path = workstacks_root / "repo" / "add-auth-feature"
    assert worktree_path.exists()
    assert worktree_path.is_dir()

    # Verify plan file was moved to .PLAN.md in worktree
    plan_dest = worktree_path / ".PLAN.md"
    assert plan_dest.exists()
    assert plan_dest.read_text() == plan_content

    # Verify original plan file was moved (not copied)
    assert not plan_file.exists()

    # Verify .env was created
    assert (worktree_path / ".env").exists()


def test_create_with_plan_name_sanitization(tmp_path: Path) -> None:
    """Test that plan filename gets properly sanitized for worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file with underscores and mixed case
    plan_file = repo / "MY_COOL_Plan_File.md"
    plan_file.write_text("# Cool Plan\n")

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "MY_COOL_Plan_File.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree name is lowercase with hyphens and "plan" removed
    worktree_path = workstacks_root / "repo" / "my-cool-file"
    assert worktree_path.exists()

    # Verify plan was moved
    assert (worktree_path / ".PLAN.md").exists()
    assert not plan_file.exists()


def test_create_with_both_name_and_plan_fails(tmp_path: Path) -> None:
    """Test that providing both NAME and --plan is an error."""
    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "plan.md"
    plan_file.write_text("# Plan\n")

    # Run workstack create with both NAME and --plan
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "myname", "--plan", "plan.md"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0
    assert (
        "Cannot specify both NAME and --plan" in result.stdout
        or "Cannot specify both NAME and --plan" in result.stderr
    )


def test_create_rejects_reserved_name_root(tmp_path: Path) -> None:
    """Test that 'root' is rejected as a reserved worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "root"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "root", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with reserved name error
    assert result.returncode != 0
    assert "root" in result.stderr.lower() and "reserved" in result.stderr.lower(), (
        f"Expected error about 'root' being reserved, got: {result.stderr}"
    )

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "root"
    assert not worktree_path.exists()


def test_create_rejects_reserved_name_root_case_insensitive(tmp_path: Path) -> None:
    """Test that 'ROOT', 'Root', etc. are also rejected (case-insensitive)."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Test various cases of "root"
    for name_variant in ["ROOT", "Root", "RoOt"]:
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        result = subprocess.run(
            ["uv", "run", "workstack", "create", name_variant, "--no-post"],
            cwd=repo,
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail with reserved name error
        assert result.returncode != 0, f"Expected failure for name '{name_variant}'"
        assert "reserved" in result.stderr.lower(), (
            f"Expected error about 'root' being reserved for '{name_variant}', got: {result.stderr}"
        )


def test_create_rejects_main_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'main' is rejected as a worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "main"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "main", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "main" in result.stderr.lower()
    assert "workstack switch root" in result.stderr

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "main"
    assert not worktree_path.exists()


def test_create_rejects_master_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'master' is rejected as a worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "master"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "master", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "master" in result.stderr.lower()
    assert "workstack switch root" in result.stderr

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "master"
    assert not worktree_path.exists()


def test_render_cd_script() -> None:
    """Test that render_cd_script generates proper shell code."""
    worktree_path = Path("/example/workstacks/repo/my-worktree")
    script = render_cd_script(
        worktree_path,
        comment="workstack create - cd to new worktree",
        success_message="✓ Switched to new worktree.",
    )

    assert "# workstack create - cd to new worktree" in script
    assert f"cd '{worktree_path}'" in script
    assert 'echo "✓ Switched to new worktree."' in script


def test_create_with_script_flag(tmp_path: Path) -> None:
    """Test that --script flag outputs cd script instead of regular messages."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Run workstack create with --script flag, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "test-worktree", "--no-post", "--script"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree was created
    worktree_path = workstacks_root / "repo" / "test-worktree"
    assert worktree_path.exists()

    # Output should be a temp file path
    script_path = Path(result.stdout.strip())
    assert script_path.exists()
    assert script_path.name.startswith("workstack-create-")
    assert script_path.name.endswith(".sh")

    # Verify script content contains the cd command
    script_content = script_path.read_text()
    expected_script = render_cd_script(
        worktree_path,
        comment="cd to new worktree",
        success_message="✓ Switched to new worktree.",
    ).strip()
    assert expected_script in script_content

    # Cleanup
    script_path.unlink(missing_ok=True)


def test_hidden_shell_cmd_create_passthrough_on_help() -> None:
    """Shell integration command signals passthrough for help."""
    runner = CliRunner()
    result = runner.invoke(hidden_shell_cmd, ["create", "--help"])

    assert result.exit_code == 0
    assert result.output.strip() == "__WORKSTACK_PASSTHROUGH__"


def test_hidden_shell_cmd_create_passthrough_on_error() -> None:
    """Shell integration command signals passthrough for errors."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Try to create without any setup - should error
        result = runner.invoke(hidden_shell_cmd, ["create", "test-worktree"])

        # Should passthrough on error
        assert result.exit_code != 0
        assert result.output.strip() == "__WORKSTACK_PASSTHROUGH__"
