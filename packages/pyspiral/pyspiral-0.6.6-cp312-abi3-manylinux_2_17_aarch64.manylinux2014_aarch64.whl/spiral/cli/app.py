import logging
import os
from importlib import metadata
from logging.handlers import RotatingFileHandler
from typing import Annotated

import typer

from spiral.cli import (
    AsyncTyper,
    admin,
    console,
    fs,
    iceberg,
    key_spaces,
    login,
    orgs,
    projects,
    state,
    tables,
    telemetry,
    text,
    workloads,
)
from spiral.settings import LOG_DIR, PACKAGE_NAME, Settings

app = AsyncTyper(name="spiral")


def version_callback(ctx: typer.Context, value: bool):
    """
    Display the version of the Spiral CLI.
    """
    # True when generating completion, we can just return
    if ctx.resilient_parsing:
        return

    if value:
        ver = metadata.version(PACKAGE_NAME)
        print(f"spiral {ver}")
        raise typer.Exit()


def verbose_callback(ctx: typer.Context, value: bool):
    """
    Use more verbose output.
    """
    # True when generating completion, we can just return
    if ctx.resilient_parsing:
        return

    if value:
        logging.getLogger().setLevel(level=logging.INFO)


@app.callback(invoke_without_command=True)
def _callback(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, help=version_callback.__doc__, is_eager=True),
    ] = None,
    verbose: Annotated[
        bool | None, typer.Option("--verbose", callback=verbose_callback, help=verbose_callback.__doc__)
    ] = None,
):
    # Load the settings (we reload in the callback to support testing under different env vars)
    state.settings = Settings()


app.add_typer(orgs.app, name="orgs")
app.add_typer(projects.app, name="projects")
app.add_typer(fs.app, name="fs")
app.add_typer(tables.app, name="tables")
app.add_typer(key_spaces.app, name="ks")
app.add_typer(text.app, name="text")
app.add_typer(telemetry.app, name="telemetry")
app.add_typer(iceberg.app, name="iceberg")
app.command("login")(login.command)
app.command("console")(console.command)


# Register unless we're building docs. Because Typer docs command does not skip hidden commands...
if not bool(os.environ.get("SPIRAL_DOCS", False)):
    app.add_typer(admin.app, name="admin", hidden=True)
    app.add_typer(workloads.app, name="workloads", hidden=True)
    app.command("whoami", hidden=True)(login.whoami)
    app.command("logout", hidden=True)(login.logout)


def main():
    # Setup rotating CLI logging.
    # NOTE(ngates): we should do the same for the Spiral client? Maybe move this logic elsewhere?
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RotatingFileHandler(LOG_DIR / "cli.log", maxBytes=2**20, backupCount=10)],
    )

    app()


if __name__ == "__main__":
    main()
