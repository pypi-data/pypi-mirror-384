from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

    from spiral.client import Spiral


class Iceberg:
    """
    Apache Iceberg is a powerful open-source table format designed for high-performance data lakes.
    Iceberg brings reliability, scalability, and advanced features like time travel, schema evolution,
    and ACID transactions to your warehouse.
    """

    def __init__(self, spiral: "Spiral"):
        self._spiral = spiral
        self._api = self._spiral.config.api

    def catalog(self) -> "Catalog":
        """Open the Iceberg catalog."""
        from pyiceberg.catalog import load_catalog

        return load_catalog(
            "default",
            **{
                "type": "rest",
                "uri": self._spiral.config.spiraldb.uri + "/iceberg",
                "token": self._spiral.config.authn.token().expose_secret(),
            },
        )
