# Core Component Testing Patterns

## Overview

This directory contains unit tests for core workstack components - the business logic layer that sits below CLI commands. Tests here focus on pure logic without CLI integration.

## Subdirectory Organization

| Directory     | Focus                            | When to Load                   |
| ------------- | -------------------------------- | ------------------------------ |
| `config/`     | Configuration management         | Config loading and environment |
| `operations/` | Git, Graphite, GitHub operations | Operations layer with fakes    |
| `detection/`  | Auto-detection logic             | Dagster, branch detection      |
| `utils/`      | Utility functions                | File utils, naming conventions |
| `foundation/` | Core infrastructure              | Context, templates             |

## Core vs Command Tests

**Core tests** focus on:

- Business logic without CLI concerns
- Direct function/class testing
- Pure unit tests with minimal setup
- Algorithm and data structure testing

**Command tests** focus on:

- CLI interface (Click commands)
- User-facing output formatting
- Command-line argument parsing
- Integration via CliRunner

## Standard Core Test Pattern

```python
from workstack.core.operations.gitops import GitOps
from tests.fakes.fake_gitops import FakeGitOps

def test_core_logic() -> None:
    # Arrange: Set up fakes
    git_ops = FakeGitOps(
        current_branch="main",
        all_branches=["main", "feature"]
    )

    # Act: Call core function directly
    result = some_core_function(git_ops)

    # Assert: Verify behavior
    assert result == expected_value
    assert "feature" in git_ops.created_branches
```

## Dependency Injection at Core Layer

Core components use constructor injection:

```python
from dataclasses import dataclass
from workstack.core.operations.gitops_abc import GitOpsABC

@dataclass(frozen=True)
class WorkspaceManager:
    git_ops: GitOpsABC

    def create_workspace(self, name: str) -> None:
        self.git_ops.create_branch(name)

def test_workspace_manager() -> None:
    git_ops = FakeGitOps(current_branch="main")
    manager = WorkspaceManager(git_ops=git_ops)

    manager.create_workspace("new-branch")

    assert "new-branch" in git_ops.created_branches
```

## Testing Without CLI

Core tests don't use `CliRunner`:

```python
# ❌ DON'T: Use CliRunner for core tests
from click.testing import CliRunner

# ✅ DO: Call functions directly
from workstack.core.naming import sanitize_branch_name

def test_sanitize_branch_name() -> None:
    result = sanitize_branch_name("Feature/Test Branch")
    assert result == "feature/test-branch"
```

## Common Core Test Patterns

### Pure Functions

```python
def test_pure_function() -> None:
    # Pure functions are easiest to test
    input_value = "test-input"
    expected = "expected-output"

    result = pure_function(input_value)

    assert result == expected
```

### Stateful Classes

```python
def test_stateful_class() -> None:
    # Use fakes for dependencies
    git_ops = FakeGitOps(current_branch="main")

    # Construct with dependencies
    instance = MyClass(git_ops=git_ops)

    # Exercise behavior
    instance.do_something()

    # Assert via fake's read-only properties
    assert len(git_ops.created_branches) == 1
```

### Algorithm Testing

```python
def test_algorithm() -> None:
    # Test edge cases
    assert algorithm([]) == []
    assert algorithm([1]) == [1]
    assert algorithm([1, 2, 3]) == [3, 2, 1]

    # Test error conditions
    with pytest.raises(ValueError):
        algorithm(None)
```

## Subdirectory-Specific Guidance

### Config Tests

See `config/` - Testing configuration loading, validation, and environment variable handling.

### Operations Tests

See `operations/CLAUDE.md` - Testing git, Graphite, and GitHub operations with fakes. **Critical for understanding mutation tracking.**

### Detection Tests

See `detection/` - Testing auto-detection logic for Dagster projects, default branches, etc.

### Utils Tests

See `utils/` - Testing utility functions like file operations, naming conventions.

### Foundation Tests

See `foundation/` - Testing core infrastructure like WorkstackContext, setup templates.

## Testing Strategies

### LBYL Pattern Testing

Core code follows LBYL (Look Before You Leap):

```python
def test_lbyl_pattern() -> None:
    git_ops = FakeGitOps(
        current_branch="main",
        all_branches=["main"]
    )

    # Function checks existence before acting
    if "feature" in git_ops.all_branches:
        result = switch_to_branch(git_ops, "feature")
    else:
        result = None

    assert result is None  # Branch doesn't exist
```

### Mutation Tracking

Never use mocks - track mutations via read-only properties:

```python
def test_mutation_tracking() -> None:
    git_ops = FakeGitOps(current_branch="main")

    create_branch(git_ops, "new-branch")

    # ❌ DON'T: mock.assert_called_with(...)
    # ✅ DO: Check read-only property
    assert "new-branch" in git_ops.created_branches
```

## See Also

- [operations/CLAUDE.md](operations/CLAUDE.md) - Operations testing patterns (critical)
- [../CLAUDE.md](../CLAUDE.md) - Overall test structure
- [../.agent/docs/TESTING.md](../../.agent/docs/TESTING.md) - Complete testing guide
