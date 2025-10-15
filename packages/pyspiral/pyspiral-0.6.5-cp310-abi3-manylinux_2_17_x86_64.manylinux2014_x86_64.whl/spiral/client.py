from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import jwt
import pyarrow as pa

from spiral.api import SpiralAPI
from spiral.api.projects import CreateProjectRequest, CreateProjectResponse
from spiral.core.client import Operations
from spiral.core.client import Spiral as CoreSpiral
from spiral.datetime_ import timestamp_micros
from spiral.expressions import ExprLike
from spiral.scan import Scan
from spiral.settings import Settings, settings

if TYPE_CHECKING:
    from spiral.iceberg import Iceberg
    from spiral.key_space_index import KeySpaceIndex
    from spiral.project import Project
    from spiral.table import Table
    from spiral.text_index import TextIndex


class Spiral:
    def __init__(self, config: Settings | None = None):
        self._config = config or settings()
        self._org = None

    @property
    def config(self) -> Settings:
        return self._config

    @property
    def api(self) -> SpiralAPI:
        return self._config.api

    @property
    def _core(self) -> CoreSpiral:
        return self._config.core

    @property
    def organization(self) -> str:
        if self._org is None:
            token = self._config.authn.token()
            if token is None:
                raise ValueError("Authentication failed.")
            token_payload = jwt.decode(token.expose_secret(), options={"verify_signature": False})
            if "org_id" not in token_payload:
                raise ValueError("Please create an organization.")
            self._org = token_payload["org_id"]
        return self._org

    def list_projects(self) -> list["Project"]:
        """List project IDs."""
        from .project import Project

        return [Project(self, project_id=p.id, name=p.name) for p in self.api.project.list()]

    def create_project(
        self,
        id_prefix: str | None = None,
        *,
        name: str | None = None,
    ) -> "Project":
        """Create a project in the current, or given, organization."""
        from .project import Project

        res: CreateProjectResponse = self.api.project.create(CreateProjectRequest(id_prefix=id_prefix, name=name))
        return Project(self, res.project.id, name=res.project.name)

    def project(self, project_id: str) -> "Project":
        """Open an existing project."""
        from spiral.project import Project

        # We avoid an API call since we'd just be fetching a human-readable name. Seems a waste in most cases.
        return Project(self, project_id=project_id, name=project_id)

    def table(self, table_id: str) -> "Table":
        """Open a table using an ID."""
        from spiral.table import Table

        return Table(self, self._core.table(table_id))

    def text_index(self, index_id: str) -> "TextIndex":
        """Open a text index using an ID."""
        from spiral.text_index import TextIndex

        return TextIndex(self._core.text_index(index_id))

    def key_space_index(self, index_id: str) -> "KeySpaceIndex":
        """Open a key space index using an ID."""
        from spiral.key_space_index import KeySpaceIndex

        return KeySpaceIndex(self._core.key_space_index(index_id))

    def scan(
        self,
        *projections: ExprLike,
        where: ExprLike | None = None,
        asof: datetime | int | None = None,
        exclude_keys: bool | None = None,
    ) -> Scan:
        """Starts a read transaction on the Spiral.

        Args:
            projections: a set of expressions that return struct arrays.
            where: a query expression to apply to the data.
            asof: only data written before the given timestamp will be returned, caveats around compaction.
            exclude_keys: whether to exclude the key columns in the scan result, defaults to False.
                Note that if a projection includes a key column, it will be included in the result.
        """
        from spiral import expressions as se

        if isinstance(asof, datetime):
            asof = timestamp_micros(asof)

        # Combine all projections into a single struct.
        projection = se.merge(*projections)
        if where is not None:
            where = se.lift(where)

        return Scan(
            self._core.scan(
                projection.__expr__,
                filter=where.__expr__ if where else None,
                asof=asof,
                exclude_keys=exclude_keys,
            ),
        )

    # TODO(marko): This should be query, and search should be query + scan.
    def search(
        self,
        top_k: int,
        *rank_by: ExprLike,
        filters: ExprLike | None = None,
        freshness_window: timedelta | None = None,
    ) -> pa.RecordBatchReader:
        """Queries the index with the given rank by and filters clauses. Returns a stream of scored keys.

        Args:
            top_k: The number of top results to return.
            rank_by: Rank by expressions are combined for scoring.
                See `se.text.find` and `se.text.boost` for scoring expressions.
            filters: The `filters` expression is used to filter the results.
                It must return a boolean value and use only conjunctions (ANDs). Expressions in filters
                statement are considered either a `must` or `must_not` clause in search terminology.
            freshness_window: If provided, the index will not be refreshed if its freshness does not exceed this window.
        """
        from spiral import expressions as se

        if not rank_by:
            raise ValueError("At least one rank by expression is required.")
        rank_by = se.or_(*rank_by)
        if filters is not None:
            filters = se.lift(filters)

        if freshness_window is None:
            freshness_window = timedelta(seconds=0)
        freshness_window_s = int(freshness_window.total_seconds())

        return self._core.search(
            top_k=top_k,
            rank_by=rank_by.__expr__,
            filters=filters.__expr__ if filters else None,
            freshness_window_s=freshness_window_s,
        )

    def _ops(self) -> Operations:
        """Access maintenance operations."""
        return self._core._ops(format=settings().file_format)

    @property
    def iceberg(self) -> "Iceberg":
        """
        Apache Iceberg is a powerful open-source table format designed for high-performance data lakes.
        Iceberg brings reliability, scalability, and advanced features like time travel, schema evolution,
        and ACID transactions to your warehouse.
        """
        from spiral.iceberg import Iceberg

        return Iceberg(self)
