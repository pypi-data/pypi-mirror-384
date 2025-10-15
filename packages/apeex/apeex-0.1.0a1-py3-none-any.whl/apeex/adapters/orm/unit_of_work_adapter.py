from sqlalchemy.orm import Session
from apeex.orm import UnitOfWorkInterface
from typing import Any

class UnitOfWorkAdapter(UnitOfWorkInterface):
    pass
    def __init__(self, session: Session):
        self.session = session

    def register_new(self, entity: Any) -> None:
        self.session.add(entity)

    def register_dirty(self, entity: Any) -> None:
        self.session.add(entity)

    def register_removed(self, entity: Any) -> None:
        self.session.delete(entity)

    def commit(self) -> None:
        self.session.commit()