from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from app.database.models import Peripheral, Workplace, Room
from app.repositories.base import BaseRepository

class PeripheralsRepository(BaseRepository[Peripheral]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Peripheral)

    def search_and_filter(
        self,
        search: str = "",
        status: str | None = None,
        peripheral_type_id: int | None = None,
        room_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        order_by: str = "inventory_number",
        ascending: bool = True,
    ) -> list[Peripheral]:

        with self.session_factory() as session:
            q = session.query(Peripheral).options(
                joinedload(Peripheral.peripheral_type),
                joinedload(Peripheral.workplace).joinedload(Workplace.room)
            )

            if room_id is not None:
                q = q.join(Peripheral.workplace).join(Workplace.room).filter(Room.id == room_id)

            if search:
                term = f"%{search}%"
                q = q.filter(or_(
                    Peripheral.inventory_number.ilike(term),
                    Peripheral.brand.ilike(term),
                    Peripheral.model.ilike(term),
                    Peripheral.serial_number.ilike(term),
                ))

            if status: q = q.filter(Peripheral.status == status)
            if peripheral_type_id: q = q.filter(Peripheral.peripheral_type_id == peripheral_type_id)
            if date_from: q = q.filter(Peripheral.purchase_date >= date_from)
            if date_to: q = q.filter(Peripheral.purchase_date <= date_to)

            col = getattr(Peripheral, order_by, Peripheral.inventory_number)
            q = q.order_by(col.asc() if ascending else col.desc())

            return q.all()