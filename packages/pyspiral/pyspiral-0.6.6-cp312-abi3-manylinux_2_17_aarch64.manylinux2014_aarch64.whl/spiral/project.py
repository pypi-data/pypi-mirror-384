from typing import TYPE_CHECKING, Any

import pyarrow as pa

from spiral.api.projects import KeySpaceIndexResource, TableResource, TextIndexResource
from spiral.core.table.spec import Schema
from spiral.expressions import ExprLike
from spiral.key_space_index import KeySpaceIndex
from spiral.table import Table
from spiral.text_index import TextIndex
from spiral.types_ import Uri

if TYPE_CHECKING:
    from spiral.client import Spiral


class Project:
    def __init__(self, spiral: "Spiral", project_id: str, name: str | None = None):
        self._spiral = spiral
        self._id = project_id
        self._name = name

    def __str__(self):
        return self._id

    def __repr__(self):
        return f"Project(id={self._id}{', name=' + self._name if self._name else ''})"

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name or self._id

    def list_tables(self) -> list[TableResource]:
        return list(self._spiral.api.project.list_tables(self._id))

    def list_text_indexes(self) -> list[TextIndexResource]:
        return list(self._spiral.api.project.list_text_indexes(self._id))

    def list_key_space_indexes(self) -> list[KeySpaceIndexResource]:
        return list(self._spiral.api.project.list_key_space_indexes(self._id))

    def table(self, identifier: str) -> Table:
        """Open a table with a `dataset.table` identifier, or `table` name using the `default` dataset."""
        dataset, table = self._parse_table_identifier(identifier)

        res = list(self._spiral.api.project.list_tables(project_id=self._id, dataset=dataset, table=table))
        if len(res) == 0:
            raise ValueError(f"Table not found: {self._id}.{dataset}.{table}")
        res = res[0]

        return Table(
            self._spiral, self._spiral._core.table(res.id), identifier=f"{res.project_id}.{res.dataset}.{res.table}"
        )

    def create_table(
        self,
        identifier: str,
        *,
        key_schema: pa.Schema | Any,
        root_uri: Uri | None = None,
        exist_ok: bool = False,
    ) -> Table:
        """Create a new table in the project.

        Args:
            identifier: The table identifier, in the form `dataset.table` or `table`.
            key_schema: The schema of the table's keys.
            root_uri: The root URI for the table.
            exist_ok: If True, do not raise an error if the table already exists.
        """
        dataset, table = self._parse_table_identifier(identifier)

        if not isinstance(key_schema, pa.Schema):
            key_schema = pa.schema(key_schema)
        key_schema = Schema.from_arrow(key_schema)

        core_table = self._spiral._core.create_table(
            project_id=self._id,
            dataset=dataset,
            table=table,
            key_schema=key_schema,
            root_uri=root_uri,
            exist_ok=exist_ok,
        )

        return Table(self._spiral, core_table, identifier=f"{self._id}.{dataset}.{table}")

    def _parse_table_identifier(self, identifier: str) -> tuple[str, str]:
        parts = identifier.split(".")
        if len(parts) == 1:
            return "default", parts[0]
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid table identifier: {self._id}.{identifier}")

    def text_index(self, name: str) -> TextIndex:
        """Returns the index with the given name."""
        res = list(self._spiral.api.project.list_text_indexes(project_id=self._id, name=name))
        if len(res) == 0:
            raise ValueError(f"Index not found: {name}")
        res = res[0]

        return TextIndex(self._spiral._core.text_index(res.id), name=name)

    def create_text_index(
        self,
        name: str,
        *projections: ExprLike,
        where: ExprLike | None = None,
        root_uri: Uri | None = None,
        exist_ok: bool = False,
    ) -> TextIndex:
        """Creates a text index over the table projection.

        See `se.text.field` for how to create and configure indexable fields.

        Args:
            name: The index name. Must be unique within the project.
            projections: At least one projection expression is required.
                All projections must reference the same table.
            where: An optional filter expression to apply to the index.
            root_uri: The root URI for the index.
            exist_ok: If True, do not raise an error if the index already exists.
        """
        from spiral import expressions as se

        if not projections:
            raise ValueError("At least one projection is required.")
        projection = se.merge(*projections)
        if where is not None:
            where = se.lift(where)

        core_index = self._spiral._core.create_text_index(
            project_id=self._id,
            name=name,
            projection=projection.__expr__,
            filter=where.__expr__ if where else None,
            root_uri=root_uri,
            # TODO(marko): Validate that if an index exists, it's the same?
            exist_ok=exist_ok,
        )

        return TextIndex(core_index, name=name)

    def key_space_index(self, name: str) -> KeySpaceIndex:
        """Returns the index with the given name."""
        res = list(self._spiral.api.project.list_key_space_indexes(project_id=self._id, name=name))
        if len(res) == 0:
            raise ValueError(f"Index not found: {name}")
        res = res[0]

        return KeySpaceIndex(self._spiral._core.key_space_index(res.id), name=name)

    def create_key_space_index(
        self,
        name: str,
        granularity: int,
        *projections: ExprLike,
        where: ExprLike | None = None,
        root_uri: Uri | None = None,
        exist_ok: bool = False,
    ) -> KeySpaceIndex:
        """Creates a key space index over the table projection.

        Args:
            name: The index name. Must be unique within the project.
            granularity: The granularity at which to store keys, i.e. the size of desired key ranges.
                The key ranges will not be greater than 2x the granularity, but may be smaller.
            projections: At least one projection expression is required.
                All projections must reference the same table.
            where: An optional filter expression to apply to the index.
            root_uri: The root URI for the index.
            exist_ok: If True, do not raise an error if the index already exists.
        """
        from spiral import expressions as se

        if not projections:
            raise ValueError("At least one projection is required.")
        projection = se.merge(*projections)
        if where is not None:
            where = se.lift(where)

        core_index = self._spiral._core.create_key_space_index(
            project_id=self._id,
            name=name,
            granularity=granularity,
            projection=projection.__expr__,
            filter=where.__expr__ if where else None,
            root_uri=root_uri,
            # TODO(marko): Validate that if an index exists, it's the same?
            exist_ok=exist_ok,
        )

        return KeySpaceIndex(core_index, name=name)
