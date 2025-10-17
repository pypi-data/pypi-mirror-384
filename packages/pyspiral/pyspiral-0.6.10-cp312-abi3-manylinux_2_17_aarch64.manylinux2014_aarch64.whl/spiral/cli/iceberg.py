import sys
from typing import Annotated

import rich
import typer
from typer import Argument

from spiral.cli import CONSOLE, ERR_CONSOLE, AsyncTyper, state
from spiral.cli.types import ProjectArg

app = AsyncTyper(short_help="Apache Iceberg Catalog")


@app.command(help="List namespaces.")
def namespaces(
    project: ProjectArg,
    namespace: Annotated[str | None, Argument(help="List only namespaces under this namespace.")] = None,
):
    """List Iceberg namespaces."""
    import pyiceberg.exceptions

    catalog = state.spiral.iceberg.catalog()

    if namespace is None:
        try:
            namespaces = catalog.list_namespaces(project)
        except pyiceberg.exceptions.ForbiddenError:
            ERR_CONSOLE.print(
                f"The project, {repr(project)}, does not exist or you lack the "
                f"`iceberg:view` permission to list namespaces in it.",
            )
            raise typer.Exit(code=1)
    else:
        try:
            namespaces = catalog.list_namespaces((project, namespace))
        except pyiceberg.exceptions.ForbiddenError:
            ERR_CONSOLE.print(
                f"The namespace, {repr(project)}.{repr(namespace)}, does not exist or you lack the "
                f"`iceberg:view` permission to list namespaces in it.",
            )
            raise typer.Exit(code=1)

    table = CONSOLE.table.Table("Namespace ID", title="Iceberg namespaces")
    for ns in namespaces:
        table.add_row(".".join(ns))
    CONSOLE.print(table)


@app.command(help="List tables.")
def tables(
    project: ProjectArg,
    namespace: Annotated[str | None, Argument(help="Show only tables in the given namespace.")] = None,
):
    import pyiceberg.exceptions

    catalog = state.spiral.iceberg.catalog()

    try:
        if namespace is None:
            tables = catalog.list_tables(project)
        else:
            tables = catalog.list_tables((project, namespace))
    except pyiceberg.exceptions.ForbiddenError:
        ERR_CONSOLE.print(
            f"The namespace, {repr(project)}.{repr(namespace)}, does not exist or you lack the "
            f"`iceberg:view` permission to list tables in it.",
        )
        raise typer.Exit(code=1)

    rich_table = rich.table.Table("table id", title="Iceberg tables")
    for table in tables:
        rich_table.add_row(".".join(table))
    CONSOLE.print(rich_table)


@app.command(help="Show the table schema.")
def schema(
    project: ProjectArg,
    namespace: Annotated[str, Argument(help="Table namespace.")],
    table: Annotated[str, Argument(help="Table name.")],
):
    import pyiceberg.exceptions

    catalog = state.spiral.iceberg.catalog()

    try:
        tbl = catalog.load_table((project, namespace, table))
    except pyiceberg.exceptions.NoSuchTableError:
        ERR_CONSOLE.print(f"No table {repr(table)} found in {repr(project)}.{repr(namespace)}", file=sys.stderr)
        raise typer.Exit(code=1)

    rich_table = rich.table.Table(
        "Field ID", "Field name", "Type", "Required", "Doc", title=f"{project}.{namespace}.{table}"
    )
    for col in tbl.schema().columns:
        rich_table.add_row(str(col.field_id), col.name, str(col.field_type), str(col.required), col.doc)
    CONSOLE.print(rich_table)
