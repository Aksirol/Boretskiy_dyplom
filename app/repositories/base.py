from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import sessionmaker

T = TypeVar("T")

class BaseRepository(Generic[T]):
    # Тепер ми приймаємо фабрику сесій, а не саму сесію
    def __init__(self, session_factory: sessionmaker, model: Type[T]):
        self.session_factory = session_factory
        self.model = model

    def get_all(self) -> List[T]:
        # Відкриваємо коротку сесію
        with self.session_factory() as session:
            return session.query(self.model).all()

    def get_by_id(self, id: int) -> Optional[T]:
        with self.session_factory() as session:
            return session.get(self.model, id)

    def create(self, **kwargs) -> T:
        with self.session_factory() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            session.expunge(obj)  # Відв'язуємо об'єкт від сесії, щоб безпечно віддати у UI
            return obj

    def update(self, obj: T, **kwargs) -> T:
        with self.session_factory() as session:
            # Оскільки об'єкт прийшов з UI (відв'язаний), прикріплюємо його до поточної сесії
            local_obj = session.merge(obj)
            for key, val in kwargs.items():
                setattr(local_obj, key, val)
            session.commit()
            session.refresh(local_obj)
            session.expunge(local_obj)
            return local_obj

    def delete(self, obj: T) -> None:
        with self.session_factory() as session:
            local_obj = session.merge(obj)
            session.delete(local_obj)
            session.commit()