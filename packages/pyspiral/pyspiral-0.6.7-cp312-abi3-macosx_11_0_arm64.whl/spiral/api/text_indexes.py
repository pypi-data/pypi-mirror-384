from pydantic import BaseModel

from .client import Paged, PagedResponse, ServiceBase
from .types import IndexId, ProjectId, WorkerId
from .workers import CPU, GcpRegion, Memory, ResourceClass


class TextSearchWorker(BaseModel):
    worker_id: WorkerId
    project_id: ProjectId
    index_id: IndexId
    url: str | None


class CreateWorkerRequest(BaseModel):
    cpu: CPU
    memory: Memory
    region: GcpRegion


class CreateWorkerResponse(BaseModel):
    worker_id: WorkerId


class SyncIndexRequest(BaseModel):
    """Request to sync a text index."""

    resources: ResourceClass


class SyncIndexResponse(BaseModel):
    worker_id: WorkerId


class TextIndexesService(ServiceBase):
    """Service for text index operations."""

    def create_worker(self, index_id: IndexId, request: CreateWorkerRequest) -> CreateWorkerResponse:
        """Create a new search worker."""
        return self.client.post(f"/v1/text-indexes/{index_id}/workers", request, CreateWorkerResponse)

    def list_workers(self, index_id: IndexId) -> Paged[WorkerId]:
        """List text index workers for the given index."""
        return self.client.paged(f"/v1/text-indexes/{index_id}/workers", PagedResponse[WorkerId])

    def get_worker(self, worker_id: WorkerId) -> TextSearchWorker:
        """Get a text index worker."""
        return self.client.get(f"/v1/text-index-workers/{worker_id}", TextSearchWorker)

    def shutdown_worker(self, worker_id: WorkerId) -> None:
        """Shutdown a text index worker."""
        return self.client.delete(f"/v1/text-index-workers/{worker_id}", type[None])

    def sync_index(self, index_id: IndexId, request: SyncIndexRequest) -> SyncIndexResponse:
        """Start a job to sync an index."""
        return self.client.post(f"/v1/text-indexes/{index_id}/sync", request, SyncIndexResponse)
