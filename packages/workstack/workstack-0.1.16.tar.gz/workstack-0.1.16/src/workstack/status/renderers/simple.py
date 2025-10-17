"""Simple text-based status renderer."""

import click

from workstack.status.models.status_data import StatusData


class SimpleRenderer:
    """Renders status information as simple formatted text."""

    def render(self, status: StatusData) -> None:
        """Render status data to console.

        Args:
            status: Status data to render
        """
        self._render_header(status)
        self._render_plan(status)
        self._render_stack(status)
        self._render_pr_status(status)
        self._render_git_status(status)
        self._render_related_worktrees(status)

    def _render_file_list(self, files: list[str], *, max_files: int = 3) -> None:
        """Render a list of files with truncation.

        Args:
            files: List of file paths
            max_files: Maximum number of files to display
        """
        for file in files[:max_files]:
            click.echo(f"      {file}")

        if len(files) > max_files:
            remaining = len(files) - max_files
            click.echo(
                click.style(
                    f"      ... and {remaining} more",
                    fg="white",
                    dim=True,
                )
            )

    def _render_header(self, status: StatusData) -> None:
        """Render worktree header section.

        Args:
            status: Status data
        """
        wt = status.worktree_info

        # Title
        name_color = "green" if wt.is_root else "cyan"
        click.echo(click.style(f"Worktree: {wt.name}", fg=name_color, bold=True))

        # Location
        click.echo(click.style(f"Location: {wt.path}", fg="white", dim=True))

        # Branch
        if wt.branch:
            click.echo(click.style(f"Branch:   {wt.branch}", fg="yellow"))
        else:
            click.echo(click.style("Branch:   (detached HEAD)", fg="red", dim=True))

        click.echo()

    def _render_plan(self, status: StatusData) -> None:
        """Render plan file section if available.

        Args:
            status: Status data
        """
        if status.plan is None or not status.plan.exists:
            return

        click.echo(click.style("Plan:", fg="bright_magenta", bold=True))

        if status.plan.first_lines:
            for line in status.plan.first_lines:
                click.echo(f"  {line}")

        click.echo(
            click.style(
                f"  ({status.plan.line_count} lines in .PLAN.md)",
                fg="white",
                dim=True,
            )
        )
        click.echo()

    def _render_stack(self, status: StatusData) -> None:
        """Render Graphite stack section if available.

        Args:
            status: Status data
        """
        if status.stack_position is None:
            return

        stack = status.stack_position

        click.echo(click.style("Stack Position:", fg="blue", bold=True))

        # Show position in stack
        if stack.is_trunk:
            click.echo("  This is a trunk branch")
        else:
            if stack.parent_branch:
                parent = click.style(stack.parent_branch, fg="yellow")
                click.echo(f"  Parent: {parent}")

            if stack.children_branches:
                children = ", ".join(click.style(c, fg="yellow") for c in stack.children_branches)
                click.echo(f"  Children: {children}")

        # Show stack visualization
        if len(stack.stack) > 1:
            click.echo()
            click.echo(click.style("  Stack:", fg="white", dim=True))
            for branch in reversed(stack.stack):
                is_current = branch == stack.current_branch

                if is_current:
                    marker = click.style("◉", fg="bright_green")
                    branch_text = click.style(branch, fg="bright_green", bold=True)
                else:
                    marker = click.style("◯", fg="bright_black")
                    branch_text = branch

                click.echo(f"    {marker}  {branch_text}")

        click.echo()

    def _render_pr_status(self, status: StatusData) -> None:
        """Render PR status section if available.

        Args:
            status: Status data
        """
        if status.pr_status is None:
            return

        pr = status.pr_status

        click.echo(click.style("Pull Request:", fg="blue", bold=True))

        # PR number and state
        pr_link = click.style(f"#{pr.number}", fg="cyan")
        state_color = (
            "green" if pr.state == "OPEN" else "red" if pr.state == "CLOSED" else "magenta"
        )
        state_text = click.style(pr.state, fg=state_color)
        click.echo(f"  {pr_link} {state_text}")

        # Draft status
        if pr.is_draft:
            click.echo(click.style("  Draft PR", fg="yellow"))

        # Checks status
        if pr.checks_passing is not None:
            if pr.checks_passing:
                click.echo(click.style("  Checks: passing", fg="green"))
            else:
                click.echo(click.style("  Checks: failing", fg="red"))

        # Ready to merge
        if pr.ready_to_merge:
            click.echo(click.style("  ✓ Ready to merge", fg="green", bold=True))

        # URL
        click.echo(click.style(f"  {pr.url}", fg="white", dim=True))

        click.echo()

    def _render_git_status(self, status: StatusData) -> None:
        """Render git status section.

        Args:
            status: Status data
        """
        if status.git_status is None:
            return

        git = status.git_status

        click.echo(click.style("Git Status:", fg="blue", bold=True))

        # Clean/dirty status
        if git.clean:
            click.echo(click.style("  Working tree clean", fg="green"))
        else:
            click.echo(click.style("  Working tree has changes:", fg="yellow"))

            if git.staged_files:
                click.echo(click.style("    Staged:", fg="green"))
                self._render_file_list(git.staged_files, max_files=3)

            if git.modified_files:
                click.echo(click.style("    Modified:", fg="yellow"))
                self._render_file_list(git.modified_files, max_files=3)

            if git.untracked_files:
                click.echo(click.style("    Untracked:", fg="red"))
                self._render_file_list(git.untracked_files, max_files=3)

        # Ahead/behind
        if git.ahead > 0 or git.behind > 0:
            parts = []
            if git.ahead > 0:
                parts.append(click.style(f"{git.ahead} ahead", fg="green"))
            if git.behind > 0:
                parts.append(click.style(f"{git.behind} behind", fg="red"))

            click.echo(f"  Branch: {', '.join(parts)}")

        # Recent commits
        if git.recent_commits:
            click.echo()
            click.echo(click.style("  Recent commits:", fg="white", dim=True))
            for commit in git.recent_commits[:3]:
                sha = click.style(commit.sha, fg="yellow")
                message = commit.message[:60]
                if len(commit.message) > 60:
                    message += "..."
                click.echo(f"    {sha} {message}")

        click.echo()

    def _render_related_worktrees(self, status: StatusData) -> None:
        """Render related worktrees section.

        Args:
            status: Status data
        """
        if not status.related_worktrees:
            return

        click.echo(click.style("Related Worktrees:", fg="blue", bold=True))

        for wt in status.related_worktrees[:5]:
            name_color = "green" if wt.is_root else "cyan"
            name_part = click.style(wt.name, fg=name_color)

            if wt.branch:
                branch_part = click.style(f"[{wt.branch}]", fg="yellow", dim=True)
                click.echo(f"  {name_part} {branch_part}")
            else:
                click.echo(f"  {name_part}")

        if len(status.related_worktrees) > 5:
            remaining = len(status.related_worktrees) - 5
            click.echo(
                click.style(
                    f"  ... and {remaining} more",
                    fg="white",
                    dim=True,
                )
            )

        click.echo()
