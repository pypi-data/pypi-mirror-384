import abc
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import pyarrow as pa
import pyarrow.compute as pc
import sqlglot
import sqlglot.expressions as exp
from pyarrow.flight import (
    Action,
    FlightDescriptor,
    FlightEndpoint,
    FlightError,
    FlightInfo,
    FlightMetadataWriter,
    FlightServerBase,
    MetadataRecordBatchReader,
    RecordBatchStream,
    ServerCallContext,
    Ticket,
)

from spiral import Spiral
from spiral.api.projects import TableResource
from spiral.protogen._.arrow.flight.protocol import sql as rpc
from spiral.protogen._.arrow.flight.protocol.sql import (
    CommandGetCatalogs,
    CommandGetDbSchemas,
    CommandGetSqlInfo,
    CommandGetTables,
    CommandStatementQuery,
    SqlInfo,
    SqlSupportedTransaction,
)
from spiral.protogen._.google.protobuf import Any
from spiral.snapshot import Snapshot

log = logging.getLogger(__name__)
logging.getLogger("sqlx").setLevel(logging.WARNING)


def debuggable(func):
    """A decorator to enable GUI (i.e. PyCharm) debugging in the
    decorated Arrow Flight RPC Server function.

    See: https://github.com/apache/arrow/issues/36844
    for more details...
    """

    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        try:
            import pydevd

            pydevd.connected = True
            pydevd.settrace(suspend=False)
        except ImportError:
            # Not running in debugger
            pass
        value = func(*args, **kwargs)
        return value

    return wrapper_decorator


class ADBCServerBase:
    def get_sql_info(self, _req: CommandGetSqlInfo) -> pa.RecordBatchReader:
        """Default implementation that reports no support for any complex features."""
        info = {
            SqlInfo.FLIGHT_SQL_SERVER_NAME: "Spiral ADBC Server",
            SqlInfo.FLIGHT_SQL_SERVER_VERSION: "0.0.1",
            SqlInfo.FLIGHT_SQL_SERVER_ARROW_VERSION: pa.__version__,
            SqlInfo.FLIGHT_SQL_SERVER_READ_ONLY: True,
            SqlInfo.FLIGHT_SQL_SERVER_TRANSACTION: SqlSupportedTransaction.NONE.value,
        }

        # See https://github.com/apache/arrow-adbc/blob/38c21c2311a59803559cb0091b3f34180c28b25f/rust/core/src/schemas.rs#L35
        union_fields = [
            pa.field("string_value", pa.string()),
            pa.field("bool_value", pa.bool_()),
            pa.field("int64_value", pa.int64()),
            pa.field("int32_bitmask", pa.int32()),
            pa.field("string_list", pa.list_(pa.string())),
            pa.field(
                "int32_to_int32_list_map",
                pa.map_(pa.int32(), pa.list_(pa.int32()), keys_sorted=False),
            ),
        ]
        schema = pa.schema(
            [
                pa.field("info_name", pa.uint32(), nullable=False),
                pa.field("info_value", pa.dense_union(union_fields), nullable=False),
            ]
        )

        # PyArrow doesn't support creating a dense union for us :(
        types = []
        offsets = []
        ints = []
        bools = []
        strs = []
        for value in info.values():
            if isinstance(value, str):
                types.append(0)
                offsets.append(len(strs))
                strs.append(value)
            elif isinstance(value, bool):
                types.append(1)
                offsets.append(len(bools))
                bools.append(value)
            else:
                types.append(1)
                offsets.append(len(ints))
                ints.append(value)

        values = pa.UnionArray.from_dense(
            pa.array(types, type=pa.int8()),
            pa.array(offsets, type=pa.int32()),
            [pa.array(data, type=f.type) for data, f in zip([strs, bools, ints, [], [], []], union_fields)],
            [f.name for f in union_fields],
        )

        return pa.table(data=[pa.array(list(info.keys()), type=pa.uint32()), values], schema=schema).to_reader()

    @abc.abstractmethod
    def get_catalogs(self, req: CommandGetCatalogs) -> pa.RecordBatchReader: ...

    @abc.abstractmethod
    def get_db_schemas(self, req: CommandGetDbSchemas) -> pa.RecordBatchReader: ...

    @abc.abstractmethod
    def get_tables(self, req: CommandGetTables) -> pa.RecordBatchReader: ...

    @abc.abstractmethod
    def statement_query(self, req: CommandStatementQuery, limit: int | None = None) -> pa.RecordBatchReader: ...


class SpiralADBCServer(ADBCServerBase):
    def __init__(self, spiral: Spiral):
        self.sp = spiral

        self.pool = ThreadPoolExecutor()

    def open_snapshot(self, tbl) -> Snapshot:
        """Open a table in the Spiral project and return it as a PyArrow Dataset."""
        if tbl.catalog is None or tbl.catalog == "":
            raise FlightError("Project (Data Catalog) must be specified to open a table.")

        project = tbl.catalog
        dataset = tbl.db or "default"
        table = tbl.name

        return self.sp.project(project).table(f"{dataset}.{table}").snapshot()

    def get_catalogs(self, req: CommandGetCatalogs) -> pa.RecordBatchReader:
        schema = pa.schema([pa.field("catalog_name", pa.string(), nullable=False)])

        @debuggable
        def batches():
            yield pa.RecordBatch.from_arrays(
                [[p.id for p in self.sp.list_projects()]],
                schema=schema,
            )

        return pa.RecordBatchReader.from_batches(schema, batches())

    def get_db_schemas(self, req: CommandGetDbSchemas) -> pa.RecordBatchReader:
        """Get the schemas from the database."""

        schema = pa.schema(
            [
                pa.field("catalog_name", pa.string()),
                pa.field("db_schema_name", pa.string(), nullable=False),
            ]
        )

        @debuggable
        def batches():
            if req.catalog == "":
                # Empty string means databases _without_ a catalog, which we don't support
                return
            catalog = req.catalog

            # Otherwise, catalog is either the project ID, or None.
            if catalog is None:
                projects = self.sp.list_projects()
            else:
                projects = [self.sp.project(req.catalog)]

            for project in projects:
                datasets = {tbl.dataset for tbl in project.list_tables()}

                batch = pa.RecordBatch.from_arrays(
                    [
                        [project.id] * len(datasets),
                        list(datasets),
                    ],
                    schema=schema,
                )

                if req.db_schema_filter_pattern:
                    mask = pc.match_like(batch["db_schema_name"], req.db_schema_filter_pattern)
                    batch = batch.filter(mask)

                yield batch

        return pa.RecordBatchReader.from_batches(schema, batches())

    def get_tables(self, req: CommandGetTables) -> pa.RecordBatchReader:
        schema = pa.schema(
            [
                pa.field("catalog_name", pa.string()),
                pa.field("db_schema_name", pa.string()),
                pa.field("table_name", pa.string(), nullable=False),
                pa.field("table_type", pa.string(), nullable=False),
            ]
            + [pa.field("table_schema", pa.binary(), nullable=False)]
            if req.include_schema
            else []
        )

        @debuggable
        def batches():
            if req.catalog == "":
                # Empty string means databases _without_ a catalog, which we don't support
                return

            if req.catalog is None:
                projects = list(self.sp.list_projects())
            else:
                projects = [self.sp.project(req.catalog)]
            projects = sorted(projects, key=lambda p: p.id)

            def _process_project(project):
                tables: list[TableResource] = project.list_tables()

                rows = []
                for table in tables:
                    row = {
                        "catalog_name": project.id,
                        "db_schema_name": table.dataset,
                        "table_name": table.table,
                        "table_type": "TABLE",
                    }

                    if req.include_schema:
                        open_table = project.table(f"{table.dataset}.{table.table}")
                        row["table_schema"] = open_table.snapshot().to_dataset().schema.serialize().to_pybytes()

                    rows.append(row)

                return pa.RecordBatch.from_pylist(rows, schema=schema)

            yield from self.pool.map(_process_project, projects)

        return pa.RecordBatchReader.from_batches(schema, batches())

    @debuggable
    def statement_query(self, req: CommandStatementQuery, limit: int | None = None) -> pa.RecordBatchReader:
        # Extract the tables from the query, and bring them into the Python locals scope.
        expr = sqlglot.parse_one(req.query, dialect="duckdb")
        datasets = {}
        for tbl in expr.find_all(exp.Table):
            # We swap the three-part identifier out for a single identifier
            # This lets us register a PyArrow Dataset with DuckDB for the query.
            snapshot = self.open_snapshot(tbl)
            name = snapshot.table.table_id
            datasets[name] = snapshot.to_dataset()
            tbl.replace(exp.table_(table=name))

        try:
            import duckdb
        except ImportError:
            raise FlightError("DuckDB is required for SQL queries.")

        try:
            # Create a DuckDB connection and register the datasets
            conn = duckdb.connect()
            for name, dataset in datasets.items():
                conn.register(name, dataset)
            sql = conn.sql(expr.sql(dialect="duckdb"))
        except Exception as e:
            raise FlightError(str(e))

        if limit is not None:
            sql = sql.limit(limit)

        return sql.fetch_arrow_reader(batch_size=1_000)


class ADBCFlightServer(FlightServerBase):
    """An implementation of a FlightSQL ADBC server."""

    def __init__(self, abdc: ADBCServerBase, *, location=None, **kwargs):
        super().__init__(location=location, **kwargs)
        self.location = location
        self.adbc = abdc

        self.host = "localhost"
        self.tls = False
        if location:
            parts = urlparse(location)
            self.host = parts.hostname
            self.tls = parts.scheme.endswith("s")

    @debuggable
    def do_action(self, context: ServerCallContext, action: Action):
        log.info("DoAction %s: %s", context.peer(), action)
        super().do_action(context, action)

    @debuggable
    def do_exchange(self, context: ServerCallContext, descriptor: FlightDescriptor, reader, writer):
        log.info("DoExchange %s: %s", context.peer(), descriptor)
        super().do_exchange(context, descriptor, reader, writer)

    @debuggable
    def do_get(self, context: ServerCallContext, ticket: Ticket):
        log.info("DoGet %s: %s", context.peer(), ticket)
        req = self.parse_command(ticket.ticket)
        match req:
            case CommandGetSqlInfo():
                return RecordBatchStream(self.adbc.get_sql_info(req))
            case CommandGetCatalogs():
                return RecordBatchStream(self.adbc.get_catalogs(req))
            case CommandGetDbSchemas():
                return RecordBatchStream(self.adbc.get_db_schemas(req))
            case CommandGetTables():
                return RecordBatchStream(self.adbc.get_tables(req))
            case CommandStatementQuery():
                return RecordBatchStream(self.adbc.statement_query(req))
            case _:
                raise NotImplementedError(f"Unsupported do_Get: {req}")

    @debuggable
    def do_put(
        self,
        context: ServerCallContext,
        descriptor: FlightDescriptor,
        reader: MetadataRecordBatchReader,
        writer: FlightMetadataWriter,
    ):
        log.info("DoPut %s: %s", context.peer(), descriptor)
        super().do_put(context, descriptor, reader, writer)

    @debuggable
    def get_flight_info(self, context: ServerCallContext, descriptor: FlightDescriptor) -> FlightInfo:
        log.info("GetFlightInfo %s: %s", context.peer(), descriptor)
        req = self.parse_command(descriptor.command)
        match req:
            case CommandGetSqlInfo():
                # Each metadata type contributes to the schema.
                schema = self.adbc.get_sql_info(req).schema
            case CommandGetCatalogs():
                schema = self.adbc.get_catalogs(req).schema
            case CommandGetDbSchemas():
                schema = self.adbc.get_db_schemas(req).schema
            case CommandGetTables():
                schema = self.adbc.get_tables(req).schema
            case CommandStatementQuery():
                schema = self.adbc.statement_query(req, limit=0).schema
            case _:
                raise NotImplementedError(f"Unsupported command: {req}")

        return self._make_flight_info(self.descriptor_to_key(descriptor), descriptor, schema)

    @staticmethod
    def parse_command(command: bytes):
        command = Any().parse(command)

        if not command.type_url.startswith("type.googleapis.com/arrow.flight.protocol.sql."):
            raise NotImplementedError(f"Unsupported command: {command.type_url}")

        proto_cls_name = command.type_url[len("type.googleapis.com/arrow.flight.protocol.sql.") :]
        proto_cls = getattr(rpc, proto_cls_name)
        return proto_cls().parse(command.value)

    @staticmethod
    def descriptor_to_key(descriptor):
        return descriptor.command

    @debuggable
    def get_schema(self, context: ServerCallContext, descriptor: FlightDescriptor):
        log.info("GetSchema %s: %s", context.peer(), descriptor)
        return super().get_schema(context, descriptor)

    @debuggable
    def list_actions(self, context: ServerCallContext):
        log.info("ListActions %s", context.peer())
        super().list_actions(context)

    @debuggable
    def list_flights(self, context: ServerCallContext, criteria):
        log.info("ListFlights %s: %s", context.peer(), criteria)
        super().list_flights(context, criteria)

    def _make_flight_info(self, key, descriptor, schema: pa.Schema):
        # If we pass zero locations, the FlightSQL client should attempt to use the original connection.
        endpoints = [FlightEndpoint(key, [])]
        return FlightInfo(schema, descriptor, endpoints, -1, -1)


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger("spiral").setLevel(logging.DEBUG)

    server = ADBCFlightServer(SpiralADBCServer(Spiral()), location="grpc://localhost:5005")
    server.serve()
