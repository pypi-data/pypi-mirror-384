from .client import Paged, PagedResponse, ServiceBase
from .organizations import OrgMembership
from .types import OrgId


class AdminService(ServiceBase):
    def sync_memberships(self, org_id: OrgId | None = None) -> Paged[OrgMembership]:
        params = {}
        if org_id:
            params["org_id"] = str(org_id)
        return self.client.paged("/v1/admin/sync-memberships", PagedResponse[OrgMembership], params=params)

    def sync_orgs(self) -> Paged[OrgId]:
        params = {}
        return self.client.paged("/v1/admin/sync-orgs", PagedResponse[OrgId], params=params)
