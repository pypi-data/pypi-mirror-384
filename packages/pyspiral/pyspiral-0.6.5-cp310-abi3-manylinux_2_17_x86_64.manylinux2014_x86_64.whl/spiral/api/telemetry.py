from pydantic import BaseModel

from .client import ServiceBase


class IssueExportTokenRequest(BaseModel):
    pass


class IssueExportTokenResponse(BaseModel):
    token: str


class TelemetryService(ServiceBase):
    """Service for telemetry operations."""

    def issue_export_token(self) -> IssueExportTokenResponse:
        """Issue telemetry export token."""
        return self.client.put("/v1/telemetry/token", IssueExportTokenRequest(), IssueExportTokenResponse)
