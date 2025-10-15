"""Hub subcommand cli."""

import sys

import click
import rich
import rich.table

import ikcli.net.api.exceptions
import ikcli.utils.rich

from .core import Hub

# A decorator to give Hub object to commands
pass_hub = click.make_pass_decorator(Hub)


@click.group(name="hub")
@click.pass_context
def cli_hub(ctx):
    """Manage hub."""
    ctx.obj = Hub(ctx.obj)


@cli_hub.command(name="ls")
@click.option("--name", help="Filter hub algos by name")
@click.option("-q", "--query", help="Filter hub algos with a web search engine query")
@click.option("--limit", type=int, default=20, help="Specify how many rows to display")
@pass_hub
def cli_hub_list(hub, name, query, limit):
    """List algos from hub."""
    ikcli.utils.rich.table(
        hub.list(name=name, q=query).limit(limit),
        "Algos",
        ["name", "short_description", "version", "license", "algo_type", "algo_task", "certification"],
    )


@cli_hub.command(name="show")
@click.argument("name")
@pass_hub
def cli_hub_show(hub, name):
    """Show algo NAME full information."""
    # Get algo
    try:
        algo = hub.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo '{name}'.")
        sys.exit(1)

    # Reload algo to get all information
    algo.reload()

    # Paper
    extra = [
        f"[b]Paper[/b]: '{algo['paper']['title']}' - {algo['paper']['authors']}, "
        f"{algo['paper']['journal']}, {algo['paper']['year']}"
    ]
    if algo["paper"]["link"] is not None:
        extra.append(f"       {algo['paper']['link']}")
    extra.append("")

    # Packages
    extra.append(ikcli.utils.rich.table(algo["packages"], "Packages", ["version", "platform"], display=False))

    # Render
    keys = [
        "name",
        "short_description",
        "keywords",
        "license",
        "certification",
        "language",
        "algo_type",
        "algo_task",
        "description",
        "repository",
        "original_implementation_repository",
    ]
    ikcli.utils.rich.show(algo, "Algo", keys, extra)


@cli_hub.group(name="package")
def cli_hub_package():
    """Manage algo package."""
    pass


@cli_hub_package.command(name="ls")
@click.argument("name")
@click.option("--version", help="Package version to list")
@pass_hub
def cli_hub_package_list(hub, name, version):
    """List algo NAME packages."""
    # Get algo
    try:
        algo = hub.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo '{name}'.")
        sys.exit(1)

    # List packages
    ikcli.utils.rich.table(
        algo.packages.list(version=version),
        "Packages",
        [
            "version",
            "license",
            "ikomia_min_version",
            "ikomia_max_version",
            "python_min_version",
            "python_max_version",
            "os",
            "architecture",
            "features",
        ],
    )
