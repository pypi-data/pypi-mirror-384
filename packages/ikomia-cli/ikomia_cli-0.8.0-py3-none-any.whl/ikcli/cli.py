"""Root cli."""

import logging
import sys

import click
import rich
import rich.padding
import rich.panel
import rich.traceback
from rich.logging import RichHandler

import ikcli.utils.rich

from .algos.cli import cli_algo
from .hub.cli import cli_hub
from .namespaces.cli import cli_namespace
from .net.http import http
from .organizations.cli import cli_organization
from .projects.cli import cli_project
from .users.core import Account

# Click context settings
CONTEXT_SETTINGS = {"help_option_names": ["--help", "-h"]}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="ikomia-cli")
@click.option(
    "--url",
    envvar="IKOMIA_URL",
    default="https://scale.ikomia.ai",
    help="Ikomia HUB url.",
)
@click.option(
    "--token",
    envvar="IKOMIA_TOKEN",
    help="Ikomia API Token.",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli_cli(ctx, url, token, debug=False):
    """Ikomia command line interface."""
    # Configure logger
    level = logging.INFO
    if debug:
        level = logging.DEBUG
        rich.traceback.install(show_locals=True, suppress=[click])
    logging.basicConfig(level=level, datefmt="[%X]", handlers=[RichHandler()])

    # Setup HTTP request
    ctx.obj = http(url, token=token)


@cli_cli.command(name="signup")
@click.option("--username", prompt="Username")
@click.option("--email", prompt="Email")
@click.password_option()
@click.pass_context
def cli_signup(ctx, username, email, password):
    """Signup a new user."""
    rich.print(f"Signup user {username}")
    user = Account(ctx.obj).signup(username, email, password)
    rich.print(f"[green] {user}")


@cli_cli.command(name="login")
@click.option("--username", prompt="Username")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
)
@click.option("--token-name", default="Short live token from ikcli", help="Name for token")
@click.option("--token-ttl", type=int, default=3600, help="Token time to live")
@click.pass_context
def cli_login(ctx, username, password, token_name, token_ttl):
    """Create a new API Token and display it."""
    try:
        token = Account(ctx.obj).create_token(username, password, name=token_name, ttl=token_ttl)
        print(
            f"# This token will be only visible once and will be valid for next {token_ttl} seconds.\n"
            f"export IKOMIA_TOKEN={token}"
        )
    except ikcli.net.http.exceptions.HTTPBadCodeError as e:
        if e.code != 401:
            raise
        rich.print("[red]Invalid credentials")


@cli_cli.command(name="whoami")
@click.pass_context
def cli_whoami(ctx):
    """Get information about current user."""
    try:
        # Get user info
        me = Account(ctx.obj).me()

        # Get user profile fields
        profile = list(
            ikcli.utils.rich.show_api_object_format(me["profile"], ["job", "company", "location", "url", "biography"])
        )

        # Render
        ikcli.utils.rich.show(
            me,
            f"Logged in as '{me['username']}' on '{ctx.obj.url}'",
            ["username", "email", "first_name", "last_name"],
            extra=profile,
        )

    except ikcli.net.http.exceptions.HTTPBadCodeError as e:
        if e.code != 401:
            raise
        rich.print(f"[orange3]Not logged in on '{ctx.obj.url}'")


def cli():
    """
    Call click and catch all Exceptions to display them properly.

    Raises:
        Exception: If debug is enabled and something wrong happen
    """
    try:
        # Call click
        cli_cli()  # pylint: disable=E1120
    except Exception as e:  # pylint: disable=W0703
        # If debug enable, let exception raise (and rich display traceback)
        if logging.root.level == logging.DEBUG:
            raise

        # Otherwise try to display it properly
        ikcli.utils.rich.exception(e)
        sys.exit(1)


cli_cli.add_command(cli_algo)
cli_cli.add_command(cli_hub)
cli_cli.add_command(cli_namespace)
cli_cli.add_command(cli_organization)
cli_cli.add_command(cli_project)

if __name__ == "__main__":
    cli()
