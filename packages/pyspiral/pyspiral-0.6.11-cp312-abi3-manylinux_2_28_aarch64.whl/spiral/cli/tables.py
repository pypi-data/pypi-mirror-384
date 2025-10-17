import datetime
from typing import Annotated, Literal

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


@app.command(help="Fetch Write-Ahead-Log.")
def wal(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
):
    _, t = get_table(project, table, dataset)
    wal_ = t.core.get_wal(asof=None)
    # Don't use CONSOLE.print here so that it can be piped.
    print(wal_)


@app.command(help="Flush Write-Ahead-Log.")
def flush(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    keep: Annotated[
        Literal["1h", "2h", "4h"] | None,
        Option(help="Duration string that indicates how much WAL to keep. Defaults to 24h."),
    ] = None,
    full: Annotated[bool, Option(help="Flush full Write-Ahead-Log.")] = False,
):
    # TODO(marko): Use some human-readable duration parsing library.
    duration = None
    if keep is not None:
        if full:
            raise ValueError("Cannot specify both --keep and --full")
        match keep:
            case "1h":
                duration = datetime.timedelta(hours=1)
            case "2h":
                duration = datetime.timedelta(hours=2)
            case "4h":
                duration = datetime.timedelta(hours=4)
            case _:
                raise ValueError(f"Invalid duration string: {keep}")

    if full:
        # Warn and wait for confirmation.
        ERR_CONSOLE.print("[bold yellow]Warning: All currently open transaction will fail to commit.[/bold yellow]")
        if not questionary.confirm("Are you sure you want to continue?", default=False).ask():  # pyright: ignore[reportAny]
            ERR_CONSOLE.print("Aborting.")
            raise typer.Exit(1)

        duration = datetime.timedelta(hours=0)

    keep_latest_s = int(duration.total_seconds()) if duration is not None else None

    identifier, t = get_table(project, table, dataset)
    state.spiral._ops().flush_wal(t.core, keep_latest_s=keep_latest_s)  # pyright: ignore[reportPrivateUsage]
    CONSOLE.print(f"Flushed WAL for table {identifier} in project {project}.")


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


@app.command(help="Visualize the scan of a given column group.")
def debug_scan(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    column_group: Annotated[str, Argument(help="Dot-separated column group path.")] = ".",
):
    _, t = get_table(project, table, dataset)
    scan = state.spiral.scan(t[column_group] if column_group != "." else t)
    scan._debug()  # pyright: ignore[reportPrivateUsage]


@app.command(help="Display the manifests for a scan of a given column group.")
def dump_scan(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    column_group: Annotated[str, Argument(help="Dot-separated column group path.")] = ".",
):
    _, t = get_table(project, table, dataset)
    scan = state.spiral.scan(t[column_group] if column_group != "." else t)
    scan._dump_manifests()  # pyright: ignore[reportPrivateUsage]
