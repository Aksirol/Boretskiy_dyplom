from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from app.database.models import Room, Workplace, Computer, Peripheral
from app.repositories.base import BaseRepository


class RoomsRepository(BaseRepository[Room]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Room)

    def search_and_filter(self, query: str = "", floor: int | None = None) -> list[Room]:
        with self.session_factory() as session:
            q = session.query(Room)
            if query:
                term = f"%{query}%"
                q = q.filter(or_(
                    Room.name.ilike(term),
                    Room.number.ilike(term),
                    Room.building.ilike(term)
                ))
            if floor is not None:
                q = q.filter(Room.floor == floor)
            return q.order_by(Room.building, Room.floor, Room.name).all()


class WorkplacesRepository(BaseRepository[Workplace]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Workplace)

    # Додаємо перевизначений метод get_all
    def get_all(self) -> list[Workplace]:
        """
        Отримує всі робочі місця, одразу завантажуючи пов'язані кімнати.
        Це запобігає помилці DetachedInstanceError при зверненні до wp.room.name
        """
        with self.session_factory() as session:
            # Використовуємо options(joinedload(...)), щоб підтягнути дані кімнати одним запитом
            return session.query(Workplace).options(joinedload(Workplace.room)).all()

    def search_and_filter(self, room_id: int | None = None, query: str = "") -> list[Workplace]:
        with self.session_factory() as session:
            # 1. Створюємо підзапити для підрахунку комп'ютерів та периферії
            c_count = session.query(
                Computer.workplace_id, func.count(Computer.id).label('c')
            ).group_by(Computer.workplace_id).subquery()

            p_count = session.query(
                Peripheral.workplace_id, func.count(Peripheral.id).label('p')
            ).group_by(Peripheral.workplace_id).subquery()

            # 2. Основний запит із приєднанням підзапитів (OUTER JOIN, бо техніки може не бути)
            q = session.query(Workplace, c_count.c.c, p_count.c.p).options(
                joinedload(Workplace.room),
                joinedload(Workplace.employee)
            ).outerjoin(c_count, Workplace.id == c_count.c.workplace_id) \
                .outerjoin(p_count, Workplace.id == p_count.c.workplace_id)

            if room_id:
                q = q.filter(Workplace.room_id == room_id)
            if query:
                q = q.filter(Workplace.name.ilike(f"%{query}%"))

            results = q.order_by(Workplace.name).all()

            # 3. Динамічно додаємо атрибути до об'єктів для зручного відображення в таблиці
            workplaces = []
            for wp, c, p in results:
                wp.computers_count = c or 0
                wp.peripherals_count = p or 0
                wp.room_name = wp.room.name if wp.room else "—"
                wp.employee_name = wp.employee.full_name if wp.employee else "—"
                workplaces.append(wp)

            return workplaces