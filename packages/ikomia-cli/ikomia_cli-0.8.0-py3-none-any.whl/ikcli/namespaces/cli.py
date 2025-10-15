"""Namespace subcommand cli."""

import sys

import click
import rich

import ikcli.utils.rich
from ikcli.common.cli import role_choice, visibility_choice
from ikcli.users.core import Users

from .core import Namespaces

# A decorator to give Namespaces object to commands
pass_namespaces = click.make_pass_decorator(Namespaces)


@click.group(name="namespace")
@click.pass_context
def cli_namespace(ctx):
    """Manage namespaces."""
    ctx.obj = Namespaces(ctx.obj)


@cli_namespace.command(name="ls")
@click.option("--name", help="Filter namespaces by name")
@click.option("--limit", type=int, default=20, help="Specify how many rows to display")
@pass_namespaces
def cli_namespace_list(namespaces, name, limit):
    """List namespaces."""
    ikcli.utils.rich.table(
        namespaces.list(name=name).limit(limit),
        "Namespaces",
        ["name", "path", "visibility"],
    )


@cli_namespace.command(name="show")
@click.argument("name")
@pass_namespaces
def cli_namespace_show(namespaces, name):
    """Show namespace NAME."""
    try:
        namespace = namespaces.get(name=name)
    except ikcli.net.api.exceptions.ObjectNotFoundException:
        rich.print(f"[orange3]Unable to find namespace {name}.")
        sys.exit(1)

    # Get member list
    extra = None
    try:
        members = namespace.members.list()
        extra = [ikcli.utils.rich.table(members, "Members", ["username", "role", "source"], display=False)]
    except ikcli.net.http.exceptions.HTTPBadCodeError as e:
        # Member list doesn't works with organization (due to conflict with 'organization member' command, for now)
        #  or personal namespaces (because no membership supported)
        # So if 404, don't bother, display nothing
        if e.code != 404:
            raise

    # Display namespace
    ikcli.utils.rich.show(namespace, "Namespace", ["name", "path", "visibility"], extra=extra)


@cli_namespace.command(name="add")
@click.argument("namespace")
@click.argument("name")
@click.option("--visibility", type=visibility_choice, help="Filter organizations by visibility")
@pass_namespaces
def cli_namespace_add(namespaces, namespace, name, visibility):
    """Add namespaces NAME to NAMESPACE."""
    # Get parent namespace
    ns = namespaces.get(name=namespace)

    # Add sub namespace
    subns = ns.namespaces.create(name=name, visibility=visibility)
    rich.print(subns)


@cli_namespace.command(name="delete")
@click.argument("name")
@pass_namespaces
def cli_namespace_delete(namespaces, name):
    """Delete namespace NAME."""
    ikcli.utils.rich.delete(namespaces.get(name=name))


#
#   Members
#
@cli_namespace.group(name="member")
def cli_namespace_member():
    """Manage namespace members."""
    pass


@cli_namespace_member.command(name="ls")
@click.argument("namespace_name")
@click.option("--username", help="Filter namespace members by name")
@click.option("--role", type=role_choice, help="Filter namespace members by role")
@pass_namespaces
def cli_namespace_member_list(namespaces, namespace_name, username, role):
    """List namespace members."""
    # Get namespace and members
    namespace = namespaces.get(name=namespace_name)
    members = namespace.members.list(username=username, role=role)

    # Display on table
    ikcli.utils.rich.table(members, "Members", ["username", "role", "source"])


@cli_namespace_member.command(name="add")
@click.argument("namespace_name")
@click.argument("username")
@click.argument("role", type=role_choice)
@pass_namespaces
def cli_namespace_member_add(namespaces, namespace_name, username, role):
    """Add namespace members."""
    # Get namespace and user
    namespace = namespaces.get(name=namespace_name)
    user = Users(namespaces.get_http_request()).get(username=username)
    ikcli.utils.rich.create(
        f"Add '{username}' as {namespace_name}'s {role}",
        namespace.members,
        user=user,
        role=role,
    )


@cli_namespace_member.command(name="delete")
@click.argument("namespace_name")
@click.argument("username")
@pass_namespaces
def cli_namespace_member_delete(namespaces, namespace_name, username):
    """Remove namespace member."""
    # Get namespace and member
    namespace = namespaces.get(name=namespace_name)
    member = namespace.members.get(username=username)
    ikcli.utils.rich.delete(member)
