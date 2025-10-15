from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _validate_root_uri(uri: str) -> str:
    if uri.endswith("/"):
        raise ValueError("Root URI must not end with a slash.")
    return uri


UserId = str
OrgId = str
ProjectId = str
RoleId = str
IndexId = str
WorkerId = str

RootUri = Annotated[str, AfterValidator(_validate_root_uri)]
DatasetName = Annotated[str, StringConstraints(max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_-]+$")]
TableName = Annotated[str, StringConstraints(max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_-]*$")]
IndexName = Annotated[str, StringConstraints(max_length=128, pattern=r"^[a-zA-Z_][a-zA-Z0-9_-]*$")]
