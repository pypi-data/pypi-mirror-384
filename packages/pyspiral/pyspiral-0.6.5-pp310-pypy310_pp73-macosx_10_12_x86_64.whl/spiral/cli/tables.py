from typing import Annotated

import questionary
import rich
import rich.table
import typer
from questionary import Choice
from typer import Argument, Option

from spiral import Spiral
from spiral.api.projects import TableResource
from spiral.cli import CONSOLE, ERR_CONSOLE, AsyncTyper, state
from spiral.cli.types import ProjectArg
from spiral.debug.manifests import display_manifests
from spiral.table import Table

app = AsyncTyper(short_help="Spiral Tables.")


def ask_table(project_id: str, title: str = "Select a table") -> str:
    tables: list[TableResource] = list(state.spiral.project(project_id).list_tables())

    if not tables:
        ERR_CONSOLE.print("No tables found")
        raise typer.Exit(1)

    return questionary.select(  # pyright: ignore[reportAny]
        title,
        choices=[
            Choice(title=f"{table.dataset}.{table.table}", value=f"{table.dataset}.{table.table}")
            for table in sorted(tables, key=lambda t: (t.dataset, t.table))
        ],
    ).ask()


def get_table(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
) -> tuple[str, Table]:
    if table is None:
        identifier = ask_table(project)
    else:
        identifier = table
        if dataset is not None:
            identifier = f"{dataset}.{table}"
    return identifier, state.spiral.project(project).table(identifier)


@app.command(help="List tables.")
def ls(
    project: ProjectArg,
):
    tables = Spiral().project(project).list_tables()

    rich_table = rich.table.Table("id", "dataset", "name", title="Spiral tables")
    for table in tables:
        rich_table.add_row(table.id, table.dataset, table.table)
    CONSOLE.print(rich_table)


@app.command(help="Show the table key schema.")
def key_schema(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
):
    _, t = get_table(project, table, dataset)
    CONSOLE.print(t.key_schema)


@app.command(help="Compute the full table schema.")
def schema(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
):
    _, t = get_table(project, table, dataset)
    CONSOLE.print(t.schema())


@app.command(help="Flush Write-Ahead-Log.")
def flush(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
):
    identifier, t = get_table(project, table, dataset)
    state.spiral._ops().flush_wal(t.core)  # pyright: ignore[reportPrivateUsage]
    CONSOLE.print(f"Flushed WAL for table {identifier} in project {project}.")


@app.command(help="Display scan.")
def debug(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    column_group: Annotated[str, Argument(help="Dot-separated column group path.")] = ".",
):
    _, t = get_table(project, table, dataset)
    scan = state.spiral.scan(t[column_group] if column_group != "." else t)
    scan._debug()  # pyright: ignore[reportPrivateUsage]


@app.command(help="Display all manifests.")
def manifests(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
):
    _, t = get_table(project, table, dataset)
    s = t.snapshot()

    key_space_state = state.spiral._ops().key_space_state(s.core)  # pyright: ignore[reportPrivateUsage]
    key_space_manifest = key_space_state.manifest

    column_groups_states = state.spiral._ops().column_groups_states(s.core, key_space_state)  # pyright: ignore[reportPrivateUsage]

    display_manifests(key_space_manifest, [(x.column_group, x.manifest) for x in column_groups_states])


@app.command(help="Display the manifests which would be read by a scan of the given column group.")
def scan_manifests(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    column_group: Annotated[str, Argument(help="Dot-separated column group path.")] = ".",
):
    _, t = get_table(project, table, dataset)
    scan = state.spiral.scan(t[column_group] if column_group != "." else t)
    scan._dump_manifests()  # pyright: ignore[reportPrivateUsage]
