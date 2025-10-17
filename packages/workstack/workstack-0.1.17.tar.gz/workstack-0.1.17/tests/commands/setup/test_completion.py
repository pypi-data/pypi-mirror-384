import subprocess


def test_completion_bash_help() -> None:
    """Test bash completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "bash", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "source <(workstack completion bash)" in result.stdout
    assert "bash_completion.d" in result.stdout


def test_completion_zsh_help() -> None:
    """Test zsh completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "zsh", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "source <(workstack completion zsh)" in result.stdout
    assert "compinit" in result.stdout


def test_completion_fish_help() -> None:
    """Test fish completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "fish", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "workstack completion fish" in result.stdout
    assert ".config/fish/completions" in result.stdout


def test_completion_bash_generates_script() -> None:
    """Test bash completion generates a script."""
    import os

    # Set up environment to generate bash completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "bash_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Bash completion scripts typically contain these
    assert "complete" in result.stdout or "_workstack_completion" in result.stdout


def test_completion_zsh_generates_script() -> None:
    """Test zsh completion generates a script."""
    import os

    # Set up environment to generate zsh completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "zsh_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Zsh completion scripts typically start with #compdef
    assert "#compdef" in result.stdout


def test_completion_fish_generates_script() -> None:
    """Test fish completion generates a script."""
    import os

    # Set up environment to generate fish completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "fish_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Fish completion scripts typically contain complete command
    assert "complete" in result.stdout


def test_completion_group_help() -> None:
    """Test completion group help lists subcommands."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "bash" in result.stdout
    assert "zsh" in result.stdout
    assert "fish" in result.stdout
