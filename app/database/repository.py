from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from app.database.database import Base

# Створюємо змінну типу, яка прив'язана до нашого базового класу моделей
T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_all(self) -> List[T]:
        """Отримує всі записи з таблиці"""
        return self.session.query(self.model).all()

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Шукає запис за його ідентифікатором"""
        return self.session.query(self.model).filter(self.model.id == obj_id).first()

    def create(self, obj_in: dict) -> T:
        """Створює новий запис на основі словника з даними"""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def update(self, db_obj: T, obj_in: dict) -> T:
        """Оновлює існуючий об'єкт новими даними"""
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: T) -> None:
        """Видаляє об'єкт із бази"""
        self.session.delete(db_obj)
        self.session.commit()