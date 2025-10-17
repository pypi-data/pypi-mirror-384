from typing import Literal

import questionary
from typer import Option

from spiral.api.filesystems import (
    BuiltinFileSystem,
    GCSFileSystem,
    S3FileSystem,
    UpstreamFileSystem,
)
from spiral.cli import CONSOLE, AsyncTyper, state
from spiral.cli.types import ProjectArg, ask_project

app = AsyncTyper(short_help="File Systems.")


@app.command(help="Show the file system configured for project.")
def show(project: ProjectArg):
    file_system = state.settings.api.file_system.get_file_system(project)
    CONSOLE.print(file_system)


def ask_provider():
    res = state.settings.api.file_system.list_providers()
    return questionary.select("Select a file system provider", choices=res).ask()


@app.command(help="Update a project's default file system.")
def update(
    project: ProjectArg,
    type_: Literal["builtin", "s3", "gcs", "upstream"] = Option(None, "--type", help="Type of the file system."),
    provider: str = Option(None, help="Provider, when using `builtin` type."),
    endpoint: str = Option(None, help="Endpoint, when using `s3` type."),
    region: str = Option(
        None, help="Region, when using `s3` or `gcs` type (defaults to `auto` for `s3` when `endpoint` is set)."
    ),
    bucket: str = Option(None, help="Bucket, when using `s3` or `gcs` type."),
    role_arn: str = Option(None, help="Role ARN to assume, when using `s3` type."),
):
    if type_ == "builtin":
        provider = provider or ask_provider()
        file_system = BuiltinFileSystem(provider=provider)

    elif type_ == "upstream":
        upstream_project = ask_project(title="Select a project to use as file system.")
        file_system = UpstreamFileSystem(project_id=upstream_project)

    elif type_ == "s3":
        if role_arn is None:
            raise ValueError("--role-arn is required for S3 provider.")
        if not role_arn.startswith("arn:aws:iam::") or ":role/" not in role_arn:
            raise ValueError("Invalid role ARN format. Expected `arn:aws:iam::<account>:role/<role_name>`")
        if bucket is None:
            raise ValueError("--bucket is required for S3 provider.")
        region = region or ("auto" if endpoint else None)
        file_system = S3FileSystem(bucket=bucket, role_arn=role_arn, region=region)
        if endpoint:
            file_system.endpoint = endpoint

    elif type_ == "gcs":
        if region is None or bucket is None:
            raise ValueError("--region and --bucket is required for GCS provider.")
        file_system = GCSFileSystem(bucket=bucket, region=region)

    else:
        raise ValueError(f"Unknown file system type: {type_}")

    fs = state.settings.api.file_system.update_file_system(project, file_system)
    CONSOLE.print(fs)


@app.command(help="Lists the available built-in file system providers.")
def list_providers():
    for provider in state.settings.api.file_system.list_providers():
        CONSOLE.print(provider)
