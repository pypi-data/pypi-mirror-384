from typing import Annotated

import questionary
import rich
import typer
from questionary import Choice
from typer import Option

from spiral.api.key_space_indexes import SyncIndexRequest
from spiral.api.projects import KeySpaceIndexResource
from spiral.api.types import IndexId
from spiral.api.workers import ResourceClass
from spiral.cli import CONSOLE, AsyncTyper, state
from spiral.cli.types import ProjectArg

app = AsyncTyper(short_help="Key Space Indexes.")


def ask_index(project_id, title="Select an index"):
    indexes: list[KeySpaceIndexResource] = list(state.spiral.project(project_id).list_key_space_indexes())

    if not indexes:
        CONSOLE.print("[red]No indexes found[/red]")
        raise typer.Exit(1)

    return questionary.select(
        title,
        choices=[Choice(title=index.name, value=index.id) for index in sorted(indexes, key=lambda t: (t.name, t.id))],
    ).ask()


def get_index_id(
    project: ProjectArg,
    name: Annotated[str | None, Option(help="Index name.")] = None,
) -> IndexId:
    if name is None:
        return ask_index(project)

    indexes: list[KeySpaceIndexResource] = list(state.spiral.project(project).list_key_space_indexes())
    for index in indexes:
        if index.name == name:
            return index.id
    raise ValueError(f"Index not found: {name}")


@app.command(help="List indexes.")
def ls(
    project: ProjectArg,
):
    """List indexes."""
    indexes = state.spiral.project(project).list_key_space_indexes()

    rich_table = rich.table.Table("id", "name", title="Key Space Indexes")
    for index in indexes:
        rich_table.add_row(index.id, index.name)
    CONSOLE.print(rich_table)


@app.command(help="Show index partitions.")
def show(
    project: ProjectArg,
    name: Annotated[str | None, Option(help="Index name.")] = None,
):
    """Show index partitions."""
    index_id = get_index_id(project, name)
    index = state.spiral.key_space_index(index_id)
    shards = state.spiral._ops().compute_shards(index.core)

    rich_table = rich.table.Table("Begin", "End", "Cardinality", title=f"Index {index.name} Partitions")
    for partition in shards:
        rich_table.add_row(
            # TODO(marko): This isn't really pretty...
            repr(partition.key_range.begin),
            repr(partition.key_range.end),
            str(partition.cardinality),
        )
    CONSOLE.print(rich_table)


@app.command(help="Trigger a sync job for an index.")
def sync(
    project: ProjectArg,
    name: Annotated[str | None, Option(help="Index name.")] = None,
    resources: Annotated[ResourceClass, Option(help="Resources to use for the sync job.")] = ResourceClass.SMALL,
):
    """Trigger a sync job."""
    index_id = get_index_id(project, name)
    response = state.spiral.api.key_space_indexes.sync_index(index_id, SyncIndexRequest(resources=resources))
    CONSOLE.print(f"Triggered sync job {response.worker_id} for index {index_id}.")
