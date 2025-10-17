"""Fake git operations for testing.

FakeGitOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path

import click

from workstack.core.gitops import GitOps, WorktreeInfo


class FakeGitOps(GitOps):
    """In-memory fake implementation of git operations.

    State Management:
    -----------------
    This fake maintains mutable state to simulate git's stateful behavior.
    Operations like add_worktree, checkout_branch modify internal state.
    State changes are visible to subsequent method calls within the same test.

    When to Use Mutation:
    --------------------
    - Operations that simulate stateful external systems (git, databases)
    - When tests need to verify sequences of operations
    - When simulating side effects visible to production code

    Constructor Injection:
    ---------------------
    All INITIAL state is provided via constructor (immutable after construction).
    Runtime mutations occur through operation methods.
    Tests should construct fakes with complete initial state.

    Mutation Tracking:
    -----------------
    This fake tracks mutations for test assertions via read-only properties:
    - deleted_branches: Branches deleted via delete_branch_with_graphite()
    - added_worktrees: Worktrees added via add_worktree()
    - removed_worktrees: Worktrees removed via remove_worktree()
    - checked_out_branches: Branches checked out via checkout_branch()

    Examples:
    ---------
        # Initial state via constructor
        git_ops = FakeGitOps(
            worktrees={repo: [WorktreeInfo(path=wt1, branch="main")]},
            current_branches={wt1: "main"},
            git_common_dirs={repo: repo / ".git"},
        )

        # Mutation through operation
        git_ops.add_worktree(repo, wt2, branch="feature")

        # Verify mutation
        assert len(git_ops.list_worktrees(repo)) == 2
        assert (wt2, "feature") in git_ops.added_worktrees

        # Verify sequence of operations
        git_ops.checkout_branch(repo, "feature")
        git_ops.delete_branch_with_graphite(repo, "old-feature", force=True)
        assert (repo, "feature") in git_ops.checked_out_branches
        assert "old-feature" in git_ops.deleted_branches
    """

    def __init__(
        self,
        *,
        worktrees: dict[Path, list[WorktreeInfo]] | None = None,
        current_branches: dict[Path, str | None] | None = None,
        default_branches: dict[Path, str] | None = None,
        git_common_dirs: dict[Path, Path] | None = None,
        branch_heads: dict[str, str] | None = None,
        staged_repos: set[Path] | None = None,
    ) -> None:
        """Create FakeGitOps with pre-configured state.

        Args:
            worktrees: Mapping of repo_root -> list of worktrees
            current_branches: Mapping of cwd -> current branch
            default_branches: Mapping of repo_root -> default branch
            git_common_dirs: Mapping of cwd -> git common directory
            branch_heads: Mapping of branch name -> commit SHA
            staged_repos: Set of repo roots that should report staged changes
        """
        self._worktrees = worktrees or {}
        self._current_branches = current_branches or {}
        self._default_branches = default_branches or {}
        self._git_common_dirs = git_common_dirs or {}
        self._branch_heads = branch_heads or {}
        self._repos_with_staged_changes: set[Path] = staged_repos or set()

        # Mutation tracking
        self._deleted_branches: list[str] = []
        self._added_worktrees: list[tuple[Path, str | None]] = []
        self._removed_worktrees: list[Path] = []
        self._checked_out_branches: list[tuple[Path, str]] = []

    def list_worktrees(self, repo_root: Path) -> list[WorktreeInfo]:
        """List all worktrees in the repository."""
        return self._worktrees.get(repo_root, [])

    def get_current_branch(self, cwd: Path) -> str | None:
        """Get the currently checked-out branch."""
        return self._current_branches.get(cwd)

    def detect_default_branch(self, repo_root: Path) -> str:
        """Detect the default branch."""
        if repo_root in self._default_branches:
            return self._default_branches[repo_root]
        click.echo("Error: Could not find 'main' or 'master' branch.", err=True)
        raise SystemExit(1)

    def get_git_common_dir(self, cwd: Path) -> Path | None:
        """Get the common git directory."""
        return self._git_common_dirs.get(cwd)

    def has_staged_changes(self, repo_root: Path) -> bool:
        """Report whether the repository has staged changes."""
        return repo_root in self._repos_with_staged_changes

    def add_worktree(
        self,
        repo_root: Path,
        path: Path,
        *,
        branch: str | None = None,
        ref: str | None = None,
        create_branch: bool = False,
    ) -> None:
        """Add a new worktree (mutates internal state and creates directory)."""
        if repo_root not in self._worktrees:
            self._worktrees[repo_root] = []
        self._worktrees[repo_root].append(WorktreeInfo(path=path, branch=branch))
        # Create the worktree directory to simulate git worktree add behavior
        path.mkdir(parents=True, exist_ok=True)
        # Track the addition
        self._added_worktrees.append((path, branch))

    def move_worktree(self, repo_root: Path, old_path: Path, new_path: Path) -> None:
        """Move a worktree (mutates internal state and simulates filesystem move)."""
        if repo_root in self._worktrees:
            for i, wt in enumerate(self._worktrees[repo_root]):
                if wt.path == old_path:
                    self._worktrees[repo_root][i] = WorktreeInfo(path=new_path, branch=wt.branch)
                    break
        # Simulate the filesystem move if the paths exist
        if old_path.exists():
            old_path.rename(new_path)

    def remove_worktree(self, repo_root: Path, path: Path, *, force: bool = False) -> None:
        """Remove a worktree (mutates internal state)."""
        if repo_root in self._worktrees:
            self._worktrees[repo_root] = [
                wt for wt in self._worktrees[repo_root] if wt.path != path
            ]
        # Track the removal
        self._removed_worktrees.append(path)

    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout a branch (mutates internal state).

        Validates that the branch is not already checked out in another worktree,
        matching Git's behavior.
        """
        # Check if branch is already checked out in a different worktree
        for _repo_root, worktrees in self._worktrees.items():
            for wt in worktrees:
                if wt.branch == branch and wt.path.resolve() != cwd.resolve():
                    msg = f"fatal: '{branch}' is already checked out at '{wt.path}'"
                    raise RuntimeError(msg)

        self._current_branches[cwd] = branch
        # Update worktree branch in the worktrees list
        for repo_root, worktrees in self._worktrees.items():
            for i, wt in enumerate(worktrees):
                if wt.path.resolve() == cwd.resolve():
                    self._worktrees[repo_root][i] = WorktreeInfo(path=wt.path, branch=branch)
                    break
        # Track the checkout
        self._checked_out_branches.append((cwd, branch))

    def checkout_detached(self, cwd: Path, ref: str) -> None:
        """Checkout a detached HEAD (mutates internal state)."""
        # Detached HEAD means no branch is checked out (branch=None)
        self._current_branches[cwd] = None
        # Update worktree to show detached HEAD state
        for repo_root, worktrees in self._worktrees.items():
            for i, wt in enumerate(worktrees):
                if wt.path.resolve() == cwd.resolve():
                    self._worktrees[repo_root][i] = WorktreeInfo(path=wt.path, branch=None)
                    break

    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Track which branches were deleted (mutates internal state)."""
        self._deleted_branches.append(branch)

    def prune_worktrees(self, repo_root: Path) -> None:
        """Prune stale worktree metadata (no-op for in-memory fake)."""
        pass

    def is_branch_checked_out(self, repo_root: Path, branch: str) -> Path | None:
        """Check if a branch is already checked out in any worktree."""
        worktrees = self.list_worktrees(repo_root)
        for wt in worktrees:
            if wt.branch == branch:
                return wt.path
        return None

    def get_branch_head(self, repo_root: Path, branch: str) -> str | None:
        """Get the commit SHA at the head of a branch."""
        return self._branch_heads.get(branch)

    @property
    def deleted_branches(self) -> list[str]:
        """Get the list of branches that have been deleted.

        This property is for test assertions only.
        """
        return self._deleted_branches.copy()

    @property
    def added_worktrees(self) -> list[tuple[Path, str | None]]:
        """Get list of worktrees added during test.

        Returns list of (path, branch) tuples.
        This property is for test assertions only.
        """
        return self._added_worktrees.copy()

    @property
    def removed_worktrees(self) -> list[Path]:
        """Get list of worktrees removed during test.

        This property is for test assertions only.
        """
        return self._removed_worktrees.copy()

    @property
    def checked_out_branches(self) -> list[tuple[Path, str]]:
        """Get list of branches checked out during test.

        Returns list of (cwd, branch) tuples.
        This property is for test assertions only.
        """
        return self._checked_out_branches.copy()
