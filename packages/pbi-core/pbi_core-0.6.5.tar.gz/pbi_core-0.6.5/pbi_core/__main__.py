import click

from pbi_core.misc import remove_workspaces
from pbi_core.ssas.setup import interactive_setup


@click.group()
def pbi_core_commands() -> None:
    pass


@pbi_core_commands.command()
@click.option(
    "--plan",
    is_flag=True,
    show_default=True,
    default=False,
    help="If set, displays the workspaces to be deleted",
)
def clean(*, plan: bool) -> None:
    """Removes all workspaces left over by the library."""
    if plan:
        remove_workspaces.list_workspaces()
    else:
        remove_workspaces.clear_workspaces()


@pbi_core_commands.command()
def setup() -> None:
    """Interactive setup for package dependencies.

    Note: msmdsrv.ini auto-find requires PowerBI Desktop to be running.
    """
    interactive_setup()


if __name__ == "__main__":
    pbi_core_commands()
