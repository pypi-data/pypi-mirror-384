from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from apeex.orm import EntityManagerInterface, UnitOfWorkInterface
from typing import Any, Type
from apeex.adapters.orm import UnitOfWorkAdapter

class BaseEntityManagerAdapter(EntityManagerInterface):
    """
    Base adapter EntityManager.
    OCP: changeable for different DBMS.
    """
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self._session = self.Session()
        self.unit_of_work = UnitOfWorkAdapter(self._session)

    def persist(self, entity: Any) -> None:
        self.unit_of_work.register_new(entity)

    def remove(self, entity: Any) -> None:
        self.unit_of_work.register_removed(entity)

    def find(self, entity_class: Type, id: Any) -> Any:
        return self._session.get(entity_class, id)

    def flush(self) -> None:
        self.unit_of_work.commit()

    def clear(self) -> None:
        self._session.expunge_all()