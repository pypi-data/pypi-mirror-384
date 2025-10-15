from pydantic import BaseModel

from .client import Paged, PagedResponse, ServiceBase
from .types import ProjectId


class Workload(BaseModel):
    id: str
    project_id: ProjectId
    name: str | None = None


class CreateWorkloadRequest(BaseModel):
    name: str | None = None


class CreateWorkloadResponse(BaseModel):
    workload: Workload


class IssueWorkloadCredentialsResponse(BaseModel):
    client_id: str
    client_secret: str
    revoked_client_id: str | None = None


class WorkloadService(ServiceBase):
    """Service for workload operations."""

    def create(self, project_id: ProjectId, request: CreateWorkloadRequest) -> CreateWorkloadResponse:
        """Create a new workload."""
        return self.client.post(f"/v1/projects/{project_id}/workloads", request, CreateWorkloadResponse)

    def list(self, project_id: ProjectId) -> Paged[Workload]:
        """List active project workloads."""
        return self.client.paged(f"/projects/{project_id}/workloads", PagedResponse[Workload])

    def get(self, workload_id: str) -> Workload:
        """Get a workload."""
        return self.client.get(f"/v1/workloads/{workload_id}", Workload)

    def deactivate(self, workload_id: str) -> None:
        """De-activate a workload."""
        return self.client.delete(f"/v1/workloads/{workload_id}", None)

    def issue_credentials(self, workload_id: str) -> IssueWorkloadCredentialsResponse:
        """Issue workload credentials."""
        return self.client.post(f"/v1/workloads/{workload_id}/credentials", None, IssueWorkloadCredentialsResponse)

    def revoke_credentials(self, client_id: str) -> None:
        """Revoke workload credentials."""
        return self.client.delete(f"/v1/credentials/{client_id}", None)
