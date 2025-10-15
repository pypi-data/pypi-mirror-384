from apeex.contracts.orm.orm_engine_interface import OrmEngineInterface


class OrmAdapter(OrmEngineInterface):
    """
    Placeholder ORM adapter for MVP phase.
    Implements OrmEngineInterface (connect, is_connected).
    """

    def __init__(self):
        self._connected = False

    def connect(self, dsn: str) -> None:
        """Simulate database connection."""
        self._connected = True

    def is_connected(self) -> bool:
        """Return whether the ORM engine is connected."""
        return self._connected
