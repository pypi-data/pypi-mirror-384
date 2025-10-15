from apeex.adapters.orm import BaseEntityManagerAdapter
from typing import Optional, Mapping

class SQLiteEntityManagerAdapter(BaseEntityManagerAdapter):
    def __init__(self, settings: Optional[Mapping[str, str]] = None):
        db_url = settings.get("db_url") if settings and "db_url" in settings else "sqlite:///:memory:"
        super().__init__(db_url)

