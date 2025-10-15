"""Common cli functions."""

import click

# Click choice on project visibilities
visibility_choice = click.Choice(["PUBLIC", "TEAM", "PRIVATE"], case_sensitive=False)

# Click choice on member roles
role_choice = click.Choice(["OWNER", "MANAGER", "MEMBER", "PARTNER"], case_sensitive=False)
