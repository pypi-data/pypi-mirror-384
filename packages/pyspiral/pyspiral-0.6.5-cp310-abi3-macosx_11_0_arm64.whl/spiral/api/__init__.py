import os
from typing import TYPE_CHECKING

import httpx

from .client import _Client

if TYPE_CHECKING:
    from spiral.core.client import Authn

    from .admin import AdminService
    from .filesystems import FileSystemService
    from .key_space_indexes import KeySpaceIndexesService
    from .organizations import OrganizationService
    from .projects import ProjectService
    from .telemetry import TelemetryService
    from .text_indexes import TextIndexesService
    from .workloads import WorkloadService


class SpiralAPI:
    def __init__(self, authn: "Authn", base_url: str | None = None):
        self.base_url = base_url or os.environ.get("SPIRAL_URL", "https://api.spiraldb.com")
        self.client = _Client(
            httpx.Client(
                base_url=self.base_url,
                timeout=None if ("PYTEST_VERSION" in os.environ or bool(os.environ.get("SPIRAL_DEV", None))) else 60,
            ),
            authn,
        )

    @property
    def _admin(self) -> "AdminService":
        from .admin import AdminService

        return AdminService(self.client)

    @property
    def organization(self) -> "OrganizationService":
        from .organizations import OrganizationService

        return OrganizationService(self.client)

    @property
    def project(self) -> "ProjectService":
        from .projects import ProjectService

        return ProjectService(self.client)

    @property
    def file_system(self) -> "FileSystemService":
        from .filesystems import FileSystemService

        return FileSystemService(self.client)

    @property
    def workload(self) -> "WorkloadService":
        from .workloads import WorkloadService

        return WorkloadService(self.client)

    @property
    def text_indexes(self) -> "TextIndexesService":
        from .text_indexes import TextIndexesService

        return TextIndexesService(self.client)

    @property
    def key_space_indexes(self) -> "KeySpaceIndexesService":
        from .key_space_indexes import KeySpaceIndexesService

        return KeySpaceIndexesService(self.client)

    @property
    def telemetry(self) -> "TelemetryService":
        from .telemetry import TelemetryService

        return TelemetryService(self.client)
