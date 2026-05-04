from datetime import date
from sqlalchemy.orm import Session
from app.database.models import Computer, Peripheral, Room, Workplace


class ReportsService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_room_equipment(self, room_id: int):
        """Повертає всю техніку (ПК і периферію), що знаходиться в конкретній кімнаті."""
        with self.session_factory() as session:
            room = session.get(Room, room_id)
            if not room: return None, [], []

            # Знаходимо всі робочі місця в кімнаті
            wp_ids = [wp.id for wp in session.query(Workplace.id).filter(Workplace.room_id == room_id).all()]

            if not wp_ids: return room, [], []

            computers = session.query(Computer).filter(Computer.workplace_id.in_(wp_ids)).all()
            peripherals = session.query(Peripheral).filter(Peripheral.workplace_id.in_(wp_ids)).all()

            return room, computers, peripherals

    def get_obsolete_equipment(self, years_old: int = 5):
        """Повертає техніку, дата закупівлі якої старша за вказану кількість років."""
        cutoff_year = date.today().year - years_old
        # Обробка високосних років безпечним способом
        try:
            cutoff_date = date.today().replace(year=cutoff_year)
        except ValueError:
            cutoff_date = date.today().replace(year=cutoff_year, day=28)

        with self.session_factory() as session:
            obsolete_comps = session.query(Computer).filter(
                Computer.purchase_date <= cutoff_date,
                Computer.status != "decommissioned"  # Не беремо вже списані
            ).all()

            obsolete_periphs = session.query(Peripheral).filter(
                Peripheral.purchase_date <= cutoff_date,
                Peripheral.status != "decommissioned"
            ).all()

            return obsolete_comps, obsolete_periphs