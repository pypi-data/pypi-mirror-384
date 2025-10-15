from pydantic import BaseModel

from .client import ServiceBase
from .types import IndexId, WorkerId
from .workers import ResourceClass


class SyncIndexRequest(BaseModel):
    """Request to sync a text index."""

    resources: ResourceClass


class SyncIndexResponse(BaseModel):
    worker_id: WorkerId


class KeySpaceIndexesService(ServiceBase):
    """Service for key space index operations."""

    def sync_index(self, index_id: IndexId, request: SyncIndexRequest) -> SyncIndexResponse:
        """Start a job to sync an index."""
        return self.client.post(f"/v1/key-space-indexes/{index_id}/sync", request, SyncIndexResponse)
