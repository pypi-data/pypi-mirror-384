from typing import Annotated

import questionary
import typer
from questionary import Choice
from typer import Argument

from spiral.api.types import OrgId, ProjectId
from spiral.cli import ERR_CONSOLE, state


def ask_project(title="Select a project"):
    projects = list(state.settings.api.project.list())

    if not projects:
        ERR_CONSOLE.print("No projects found")
        raise typer.Exit(1)

    return questionary.select(
        title,
        choices=[
            Choice(title=f"{project.id} - {project.name}" if project.name else project.id, value=project.id)
            for project in projects
        ],
    ).ask()


ProjectArg = Annotated[ProjectId, Argument(help="Project ID", show_default=False, default_factory=ask_project)]


def _org_default():
    memberships = list(state.settings.api.organization.list_memberships())

    if not memberships:
        ERR_CONSOLE.print("No organizations found")
        raise typer.Exit(1)

    return questionary.select(
        "Select an organization",
        choices=[
            Choice(
                title=f"{m.org.id} - {m.org.name}" if m.org.name else m.org.id,
                value=m.org.id,
            )
            for m in memberships
        ],
    ).ask()


OrganizationArg = Annotated[OrgId, Argument(help="Organization ID", show_default=False, default_factory=_org_default)]
