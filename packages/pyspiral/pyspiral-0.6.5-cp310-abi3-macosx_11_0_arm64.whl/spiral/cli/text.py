from typing import Annotated

import questionary
import rich
import typer
from questionary import Choice
from typer import Option

from spiral.api.projects import TextIndexResource
from spiral.api.text_indexes import CreateWorkerRequest, SyncIndexRequest
from spiral.api.types import IndexId
from spiral.api.workers import CPU, GcpRegion, Memory, ResourceClass
from spiral.cli import CONSOLE, ERR_CONSOLE, AsyncTyper, state
from spiral.cli.types import ProjectArg

app = AsyncTyper(short_help="Text Indexes.")


def ask_index(project_id, title="Select an index"):
    indexes: list[TextIndexResource] = list(state.spiral.project(project_id).list_text_indexes())

    if not indexes:
        ERR_CONSOLE.print("No indexes found")
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

    indexes: list[TextIndexResource] = list(state.spiral.project(project).list_text_indexes())
    for index in indexes:
        if index.name == name:
            return index.id
    raise ValueError(f"Index not found: {name}")


@app.command(help="List indexes.")
def ls(
    project: ProjectArg,
):
    """List indexes."""
    indexes = state.spiral.project(project).list_text_indexes()

    rich_table = rich.table.Table("id", "name", title="Text Indexes")
    for index in indexes:
        rich_table.add_row(index.id, index.name)
    CONSOLE.print(rich_table)


@app.command(help="Trigger a sync job for an index.")
def sync(
    project: ProjectArg,
    name: Annotated[str | None, Option(help="Index name.")] = None,
    resources: Annotated[ResourceClass, Option(help="Resources to use for the sync job.")] = ResourceClass.SMALL,
):
    """Trigger a sync job."""
    index_id = get_index_id(project, name)
    response = state.spiral.api.text_indexes.sync_index(index_id, SyncIndexRequest(resources=resources))
    CONSOLE.print(f"Triggered sync job {response.worker_id} for index {index_id}.")


@app.command(name="serve", help="Spin up a worker to serve an index.")
def serve(
    project: ProjectArg,
    index: Annotated[str | None, Option(help="Index name.")] = None,
    region: Annotated[GcpRegion, Option(help="GCP region for the worker.")] = GcpRegion.US_EAST4,
    cpu: Annotated[CPU, Option(help="CPU resources for the worker.")] = CPU.ONE,
    memory: Annotated[Memory, Option(help="Memory resources for the worker in MB.")] = Memory.MB_512,
):
    """Spin up a worker."""
    index_id = get_index_id(project, index)
    request = CreateWorkerRequest(cpu=cpu, memory=memory, region=region)
    response = state.spiral.api.text_indexes.create_worker(index_id, request)
    CONSOLE.print(f"Created worker {response.worker_id} for {index_id}.")


@app.command(name="workers", help="List search workers.")
def workers(
    project: ProjectArg,
    index: Annotated[str | None, Option(help="Index name.")] = None,
):
    """List text search workers."""
    index_id = get_index_id(project, index)
    worker_ids = state.spiral.api.text_indexes.list_workers(index_id)

    rich_table = rich.table.Table("Worker ID", "URL", title=f"Text Search Workers for {index_id}")
    for worker_id in worker_ids:
        try:
            worker = state.spiral.api.text_indexes.get_worker(worker_id)
            rich_table.add_row(
                worker_id,
                worker.url,
            )
        except Exception:
            rich_table.add_row(
                worker_id,
                "Unavailable",
            )
    CONSOLE.print(rich_table)


@app.command(name="shutdown", help="Shutdown a search worker.")
def shutdown(worker_id: str):
    """Shutdown a worker."""
    state.spiral.api.text_indexes.shutdown_worker(worker_id)
    CONSOLE.print(f"Requested worker {worker_id} to shutdown.")
