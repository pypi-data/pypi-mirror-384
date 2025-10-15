"""Algorithm subcommand cli."""

import sys

import click
import rich
import rich.table

import ikcli.net.api.exceptions
import ikcli.utils.rich
from ikcli.common.cli import role_choice, visibility_choice
from ikcli.namespaces.core import Namespaces
from ikcli.users.core import Users
from ikcli.utils.version import Version

from .core import LICENCES, Algo, Algos

# Click choice on licences
license_choice = click.Choice(list(LICENCES.keys()), case_sensitive=False)

# A decorator to give Algos object to commands
pass_algos = click.make_pass_decorator(Algos)


@click.group(name="algo")
@click.pass_context
def cli_algo(ctx):
    """Manage algorithms."""
    # Retrieve username and password from context
    ctx.obj = Algos(ctx.obj)


@cli_algo.command(name="ls")
@click.option("--name", help="Filter algos by name")
@click.option("-q", "--query", help="Filter algos with a web search engine query")
@click.option("--limit", type=int, default=20, help="Specify how many rows to display")
@pass_algos
def cli_algo_list(algos, name, query, limit):
    """List algos."""
    ikcli.utils.rich.table(
        algos.list(name=name, q=query).limit(limit),
        "Algos",
        ["name", "path", "short_description", "language", "algo_type", "algo_task", "visibility"],
    )


def algo_show(algo: Algo, title: str = "Algo"):
    """
    Display algo information using rich.

    Args:
        algo: Algo to display
        title: Panel title
    """
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
    extra.append(ikcli.utils.rich.table(algo["packages"], "Packages", ["tag", "platform"], display=False))

    # Render
    keys = [
        "name",
        "path",
        "visibility",
        "short_description",
        "keywords",
        "language",
        "algo_type",
        "algo_task",
        "description",
        "repository",
        "original_implementation_repository",
    ]
    ikcli.utils.rich.show(algo, title, keys, extra)


@cli_algo.command(name="show")
@click.argument("name")
@pass_algos
def cli_algo_show(algos, name):
    """Show algo NAME full information."""
    # Get algo
    try:
        algo = algos.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo '{name}'. May you have to add it first.")
        sys.exit(1)

    algo_show(algo)


@cli_algo.command(name="add")
@click.argument("namespace")
@click.argument("name")
@click.option("--visibility", type=visibility_choice, help="Algo visibility")
@pass_algos
def cli_algo_add(algos, namespace, name, visibility):
    """Add algo NAME on NAMESPACE."""
    # Get local information
    local_information = algos.get_local(name).info

    # Get namespace
    namespace = Namespaces(algos.get_http_request()).get(name=namespace)

    # Create algo
    algo = ikcli.utils.rich.create(
        f"Add Algo '{name}' to {namespace}",
        namespace.algos,
        visibility=visibility,
        **local_information,
    )

    console = rich.console.Console()
    request = algo.get_http_request()

    # Upload code
    with ikcli.utils.rich.HTTPTransferProgress("Package", request, download=False, upload=True):
        package = algo.upload()

    console.print(f" [green]{package} uploaded")

    # Upload demo workflow
    with ikcli.utils.rich.HTTPTransferProgress("Demo workflow", request, download=False, upload=True):
        workflow = algo.upload_workflow()

    console.print(f" [green]{workflow} uploaded")


@cli_algo.command(name="update")
@click.argument("name")
@pass_algos
def cli_algo_update(algos, name):
    """Update remote algo NAME with local information and upload local code."""
    # Get algo
    try:
        algo = algos.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo {name}. May you have to add it first.")
        sys.exit(1)

    # Update with local information and push to remote server
    for k, v in algos.get_local(name).info.items():
        algo[k] = v

    algo.update()

    # Upload data
    console = rich.console.Console()
    request = algo.get_http_request()

    # Upload code
    with ikcli.utils.rich.HTTPTransferProgress("Package", request, download=False, upload=True):
        package = algo.upload()

    console.print(f" [green]{package} updated")

    # Upload demo workflow
    with ikcli.utils.rich.HTTPTransferProgress("Demo workflow", request, download=False, upload=True):
        workflow = algo.upload_workflow()

    console.print(f" [green]{workflow} updated")


@cli_algo.command(name="publish")
@click.argument("name")
@click.option("--license", "license_identifier", type=license_choice, help="Published algo license")
@click.option("--version", type=Version, help="Published algo version")
@pass_algos
def cli_algo_publish(algos, name, license_identifier, version):
    """Publish algo NAME on public hub."""
    # Get algo
    try:
        algo = algos.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo {name}. May you have to add it first.")
        sys.exit(1)

    # Show algo and especially available packages
    algo_show(algo, title="Algo to publish")

    # Gather missing information about publication
    if license_identifier is None or version is None:

        # Get algo next publish information
        next_publish_information = algo.get_next_publish_information()

        # Choose license if missing
        if license_identifier is None:
            # Craft a pretty dict option and display license menu
            license_options = {v[0]: f"{k}: {v[1]}" for k, v in LICENCES.items()}
            license_name = ikcli.utils.rich.menu(
                "Choose a license", license_options, default=next_publish_information.get("license", None)
            )
            # Get license identifier from enum name
            license_identifiers = {v[0]: k for k, v in LICENCES.items()}
            license_identifier = license_identifiers[license_name]
        else:
            # Convert license pretty identifier to bare license enum name
            license_name = LICENCES[license_identifier][0]

        # Choose version if missing
        if version is None:
            # Get next version and parse value as Version object
            next_versions = {k: Version(v) for k, v in next_publish_information["next_versions"].items()}
            # Craft a pretty dict option to display menu
            version_options = {v: f"Next {k} = {v}" for k, v in next_versions.items()}
            # Special case if all next versions are equals, it's the first one, so create a special dict
            if len(version_options) == 1:
                first_version = next_versions["major"]
                version_options = {first_version: f"First version = {first_version}"}
            # Display version menu
            version = ikcli.utils.rich.menu("Choose a version", version_options, default=next_versions["minor"])

    # Warn user about available package and freshness
    console = rich.console.Console()
    rich.print(
        rich.panel.Panel(
            rich.padding.Padding(
                f"[orange3]:warning:[/orange3]  Before publish '{algo['name']}',"
                " ensure all packages are present and up to date",
                (1, 1),
                style="white",
            ),
            title="Warning",
            width=120,
            border_style="bold orange3",
        )
    )

    # Confirm before publish
    if not rich.prompt.Confirm.ask(
        f"Publish [bold]'{algo['name']}'[/bold] v[bold]{version}[/bold]"
        f" under [bold]{license_identifier}[/bold] license ?"
    ):
        console.print("[orange3]Aborted by user")
        return

    # Finally publish
    with console.status(f"[cyan]Publish {algo['name']} ..."):
        published_algo = algo.publish(license_name, version)
    console.print(f"[green] {published_algo} published")


@cli_algo.command(name="delete")
@click.argument("name")
@pass_algos
def cli_delete_delete(algos, name):
    """Delete algorithm NAME."""
    ikcli.utils.rich.delete(algos.get(name=name))


@cli_algo.group(name="local")
def cli_algo_local():
    """Manage local algo."""
    pass


@cli_algo_local.command(name="ls")
@pass_algos
def cli_algo_local_list(algos):
    """List algos."""
    ikcli.utils.rich.table(
        list(algos.list_local()),
        "Algos",
        ["name", "path", "short_description", "language"],
    )


@cli_algo_local.command(name="create")
@click.argument("name")
@click.option("--base_class", type=str, default="CWorkflowTask", help="Algorithm base class from Ikomia API")
@click.option("--widget_class", type=str, default="CWorkflowTaskWidget", help="Widget base class from Ikomia API")
@click.option(
    "--qt",
    type=click.Choice(["pyqt", "pyside"], case_sensitive=False),
    default="pyqt",
    help="Python Qt framework for widget",
)
@pass_algos
def cli_algo_local_create(algos, name, base_class, widget_class, qt):
    """Create local algo NAME."""
    console = rich.console.Console()
    with console.status(f"[cyan]Creating {name} ..."):
        algo = algos.create_local(name.lower(), base_class, widget_class, qt)

    console.print(f"[green] {name} successfully created.")
    console.print(f"[green]Source code stands here: {algo['path']}")


#
#   Members
#
@cli_algo.group(name="member")
def cli_algo_member():
    """Manage algo members."""
    pass


@cli_algo_member.command(name="ls")
@click.argument("algo_name")
@click.option("--username", help="Filter algo members by name")
@click.option("--role", type=role_choice, help="Filter algo members by role")
@pass_algos
def cli_algo_member_list(algos, algo_name, username, role):
    """List algo members."""
    # Get algo and members
    algo = algos.get(name=algo_name)
    members = algo.members.list(username=username, role=role)

    # Display on table
    ikcli.utils.rich.table(members, "Members", ["username", "role", "source"])


@cli_algo_member.command(name="add")
@click.argument("algo_name")
@click.argument("username")
@click.argument("role", type=role_choice)
@pass_algos
def cli_algo_member_add(algos, algo_name, username, role):
    """Add algo members."""
    # Get algo and user
    algo = algos.get(name=algo_name)
    user = Users(algos.get_http_request()).get(username=username)
    ikcli.utils.rich.create(
        f"Add '{username}' as {algo_name}'s {role}",
        algo.members,
        user=user,
        role=role,
    )


@cli_algo_member.command(name="delete")
@click.argument("algo_name")
@click.argument("username")
@pass_algos
def cli_algo_member_delete(algos, algo_name, username):
    """Remove algo member."""
    # Get algo and member
    algo = algos.get(name=algo_name)
    member = algo.members.get(username=username)
    ikcli.utils.rich.delete(member)


#
#   Packages
#
@cli_algo.group(name="package")
def cli_algo_package():
    """Manage algo package."""
    pass


@cli_algo_package.command(name="ls")
@click.argument("name")
@pass_algos
def cli_algo_package_list(algos, name):
    """List algo NAME packages."""
    # Get algo
    try:
        algo = algos.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find algo '{name}'. May you have to add it first.")
        sys.exit(1)

    # List packages
    ikcli.utils.rich.table(
        algo.packages.list(),
        "Packages",
        [
            "tag",
            "ikomia_min_version",
            "ikomia_max_version",
            "python_min_version",
            "python_max_version",
            "os",
            "architecture",
            "features",
        ],
    )
