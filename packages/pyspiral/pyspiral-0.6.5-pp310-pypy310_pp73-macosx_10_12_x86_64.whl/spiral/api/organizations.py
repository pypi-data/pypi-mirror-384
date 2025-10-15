from enum import Enum

from pydantic import BaseModel

from .client import Paged, PagedResponse, ServiceBase
from .types import OrgId


class OrgRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    GUEST = "guest"


class Org(BaseModel):
    id: OrgId
    name: str | None = None


class OrgMembership(BaseModel):
    user_id: str
    org: Org
    role: str


class CreateOrgRequest(BaseModel):
    name: str | None = None


class CreateOrgResponse(BaseModel):
    org: Org


class PortalLinkIntent(str, Enum):
    SSO = "sso"
    DIRECTORY_SYNC = "directory-sync"
    AUDIT_LOGS = "audit-logs"
    LOG_STREAMS = "log-streams"
    DOMAIN_VERIFICATION = "domain-verification"


class PortalLinkRequest(BaseModel):
    intent: PortalLinkIntent


class PortalLinkResponse(BaseModel):
    url: str


class InviteUserRequest(BaseModel):
    email: str
    role: OrgRole
    expires_in_days: int | None = 7


class InviteUserResponse(BaseModel):
    invite_id: str


class OrganizationService(ServiceBase):
    """Service for organization operations."""

    def create(self, request: CreateOrgRequest) -> CreateOrgResponse:
        """Create a new organization."""
        return self.client.post("/v1/organizations", request, CreateOrgResponse)

    def list_memberships(self) -> Paged[OrgMembership]:
        """List organization memberships."""
        return self.client.paged("/v1/organizations", PagedResponse[OrgMembership])

    def invite_user(self, request: InviteUserRequest) -> InviteUserResponse:
        """Invite a user to the organization."""
        return self.client.post("/v1/organizations/invite-user", request, InviteUserResponse)

    def portal_link(self, request: PortalLinkRequest) -> PortalLinkResponse:
        """Get configuration portal link for the organization."""
        return self.client.put("/v1/organizations/portal-link", request, PortalLinkResponse)
