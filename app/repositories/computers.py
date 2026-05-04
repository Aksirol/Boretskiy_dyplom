from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from app.database.models import Computer, Workplace, Room
from app.repositories.base import BaseRepository

class ComputersRepository(BaseRepository[Computer]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Computer)

    def search_and_filter(
        self,
        search: str = "",
        status: str | None = None,
        computer_type_id: int | None = None,
        room_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        order_by: str = "inventory_number",
        ascending: bool = True,
    ) -> list[Computer]:

        with self.session_factory() as session:
            q = session.query(Computer).options(
                # Завантажуємо пов'язані дані заздалегідь, згідно з архітектурою
                joinedload(Computer.computer_type),
                joinedload(Computer.workplace).joinedload(Workplace.room)
            )

            if room_id is not None:
                q = q.join(Computer.workplace).join(Workplace.room).filter(Room.id == room_id)

            if search:
                term = f"%{search}%"
                q = q.filter(or_(
                    Computer.inventory_number.ilike(term),
                    Computer.brand.ilike(term),
                    Computer.model.ilike(term),
                    Computer.ip_address.ilike(term),
                    Computer.mac_address.ilike(term),
                ))

            if status:
                q = q.filter(Computer.status == status)
            if computer_type_id:
                q = q.filter(Computer.computer_type_id == computer_type_id)
            if date_from:
                q = q.filter(Computer.purchase_date >= date_from)
            if date_to:
                q = q.filter(Computer.purchase_date <= date_to)

            col = getattr(Computer, order_by, Computer.inventory_number)
            q = q.order_by(col.asc() if ascending else col.desc())

            return q.all()