import click

from workstack.cli.shell_integration.handler import (
    PASSTHROUGH_MARKER,
    ShellIntegrationResult,
    handle_shell_request,
)


@click.command(
    "__shell",
    hidden=True,
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_interspersed_args": False},
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def hidden_shell_cmd(args: tuple[str, ...]) -> None:
    """Unified entry point for shell integration wrappers."""
    result: ShellIntegrationResult = handle_shell_request(args)

    if result.passthrough:
        click.echo(PASSTHROUGH_MARKER)
        raise SystemExit(result.exit_code)

    if result.script:
        click.echo(result.script, nl=False)

    raise SystemExit(result.exit_code)
