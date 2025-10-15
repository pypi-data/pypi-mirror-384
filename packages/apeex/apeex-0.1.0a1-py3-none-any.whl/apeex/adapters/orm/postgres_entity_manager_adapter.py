from apeex.adapters.orm import BaseEntityManagerAdapter
from typing import Optional, Mapping

class PostgresEntityManagerAdapter(BaseEntityManagerAdapter):
    def __init__(self, settings: Optional[Mapping[str, str]] = None):
        db_url = settings.get("db_url") if settings and "db_url" in settings else "postgresql+psycopg2://user:pass@localhost/db"
        super().__init__(db_url)