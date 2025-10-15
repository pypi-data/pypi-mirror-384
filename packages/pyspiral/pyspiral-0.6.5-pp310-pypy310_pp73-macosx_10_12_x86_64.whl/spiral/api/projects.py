from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .client import Paged, PagedResponse, ServiceBase
from .types import OrgId, ProjectId, RoleId


class Project(BaseModel):
    id: ProjectId
    org_id: OrgId
    name: str | None = None


class CreateProjectRequest(BaseModel):
    id_prefix: str | None = None
    name: str | None = None


class CreateProjectResponse(BaseModel):
    project: Project


class Grant(BaseModel):
    id: str
    project_id: ProjectId
    role_id: RoleId
    principal: str
    conditions: dict | None = None


class OrgRolePrincipalConditions(BaseModel):
    type: Literal["org_role"] = "org_role"
    org_id: OrgId
    role: str


class OrgUserPrincipalConditions(BaseModel):
    type: Literal["org_user"] = "org_user"
    org_id: OrgId
    user_id: str


class WorkloadPrincipalConditions(BaseModel):
    type: Literal["workload"] = "workload"
    workload_id: str


class GitHubConditions(BaseModel):
    environment: str | None = None
    ref: str | None = None
    ref_type: str | None = None
    sha: str | None = None
    repository: str | None = None
    repository_owner: str | None = None
    repository_visibility: str | None = None
    repository_id: str | None = None
    repository_owner_id: str | None = None
    run_id: str | None = None
    run_number: str | None = None
    run_attempt: str | None = None
    runner_environment: str | None = None
    actor_id: str | None = None
    actor: str | None = None
    workflow: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None
    job_workflow_ref: str | None = None
    event_name: str | None = None


class GitHubPrincipalConditions(BaseModel):
    type: Literal["github"] = "github"
    org: str
    repo: str
    conditions: GitHubConditions | None = None


class ModalConditions(BaseModel):
    app_id: str | None = None
    app_name: str | None = None
    function_id: str | None = None
    function_name: str | None = None
    container_id: str | None = None


class ModalPrincipalConditions(BaseModel):
    type: Literal["modal"] = "modal"

    # A Modal App is a group of functions and classes that are deployed together.
    # See https://modal.com/docs/guide/apps. Nick and Marko discussed having an app_name
    # here as well and decided to leave it out for now with the assumption that people
    # will want to authorize the whole Modal environment to access Spiral (their data).
    workspace_id: str
    # Environments are sub-divisions of workspaces. Name is unique within a workspace.
    # See https://modal.com/docs/guide/environments
    environment_name: str

    conditions: ModalConditions | None = None


class GcpServiceAccountPrincipalConditions(BaseModel):
    type: Literal["gcp"] = "gcp"
    service_account: str
    unique_id: str


class AwsAssumedRolePrincipalConditions(BaseModel):
    type: Literal["aws"] = "aws"
    account_id: str
    role_name: str


PrincipalConditions = Annotated[
    OrgRolePrincipalConditions
    | OrgUserPrincipalConditions
    | WorkloadPrincipalConditions
    | GitHubPrincipalConditions
    | ModalPrincipalConditions
    | GcpServiceAccountPrincipalConditions
    | AwsAssumedRolePrincipalConditions,
    Field(discriminator="type"),
]


class GrantRoleRequest(BaseModel):
    role_id: RoleId
    principal: PrincipalConditions


class GrantRoleResponse(BaseModel):
    grant: Grant


class TableResource(BaseModel):
    id: str
    project_id: ProjectId
    dataset: str
    table: str


class TextIndexResource(BaseModel):
    id: str
    project_id: ProjectId
    name: str


class KeySpaceIndexResource(BaseModel):
    id: str
    project_id: ProjectId
    name: str


class ProjectService(ServiceBase):
    """Service for project operations."""

    def create(self, request: CreateProjectRequest) -> CreateProjectResponse:
        """Create a new project."""
        return self.client.post("/v1/projects", request, CreateProjectResponse)

    def list(self) -> Paged[Project]:
        """List projects."""
        return self.client.paged("/v1/projects", PagedResponse[Project])

    def list_tables(
        self, project_id: ProjectId, dataset: str | None = None, table: str | None = None
    ) -> Paged[TableResource]:
        """List tables in a project."""
        params = {}
        if dataset:
            params["dataset"] = dataset
        if table:
            params["table"] = table
        return self.client.paged(f"/v1/projects/{project_id}/tables", PagedResponse[TableResource], params=params)

    def list_text_indexes(self, project_id: ProjectId, name: str | None = None) -> Paged[TextIndexResource]:
        """List text indexes in a project."""
        params = {}
        if name:
            params["name"] = name
        return self.client.paged(
            f"/v1/projects/{project_id}/text-indexes", PagedResponse[TextIndexResource], params=params
        )

    def list_key_space_indexes(self, project_id: ProjectId, name: str | None = None) -> Paged[KeySpaceIndexResource]:
        """List key space indexes in a project."""
        params = {}
        if name:
            params["name"] = name
        return self.client.paged(
            f"/v1/projects/{project_id}/key-space-indexes", PagedResponse[KeySpaceIndexResource], params=params
        )

    def get(self, project_id: ProjectId) -> Project:
        """Get a project."""
        return self.client.get(f"/v1/projects/{project_id}", Project)

    def grant_role(self, project_id: ProjectId, request: GrantRoleRequest) -> GrantRoleResponse:
        """Grant a role to a principal."""
        return self.client.post(f"/v1/projects/{project_id}/grants", request, GrantRoleResponse)

    def list_grants(
        self,
        project_id: ProjectId,
        principal: str | None = None,
    ) -> Paged[Grant]:
        """List active project grants."""
        params = {}
        if principal:
            params["principal"] = principal
        return self.client.paged(f"/v1/projects/{project_id}/grants", PagedResponse[Grant], params=params)

    def get_grant(self, grant_id: str) -> Grant:
        """Get a grant."""
        return self.client.get(f"/v1/grants/{grant_id}", Grant)

    def revoke_grant(self, grant_id: str):
        """Revoke a grant."""
        return self.client.delete(f"/v1/grants/{grant_id}", type[None])
