import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Room, Workplace, Computer, ComputerType
from app.services.reports import ReportsService


@pytest.fixture
def reports_env(tmp_path):
    test_db_path = tmp_path / "test_reports.db"
    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # Заповнюємо тестовими даними з усіма обов'язковими полями!
    with SessionLocal() as session:
        room = Room(name="Серверна", number="100", floor=1, building="Головний")
        session.add(room)
        session.commit()

        saved_room_id = room.id  # <--- ЗБЕРІГАЄМО ID ТУТ, ПОКИ СЕСІЯ ВІДКРИТА

        wp = Workplace(name="Стіл", room_id=saved_room_id)
        session.add(wp)
        session.commit()

        ctype = ComputerType(name="PC")
        session.add(ctype)
        session.commit()

        base_pc_data = {
            "computer_type_id": ctype.id,
            "workplace_id": wp.id,
            "brand": "Dell",
            "model": "OptiPlex",
            "processor": "i5",
            "ram_gb": 16,
            "storage_gb": 512,
            "storage_type": "SSD",
            "os": "Windows 11"
        }

        # 1. Застарілий ПК (6 років тому)
        old_pc = Computer(inventory_number="OLD-1", purchase_date=date(date.today().year - 6, 1, 1), status="active",
                          **base_pc_data)

        # 2. Новий ПК (1 рік тому)
        new_pc = Computer(inventory_number="NEW-1", purchase_date=date(date.today().year - 1, 1, 1), status="active",
                          **base_pc_data)

        # 3. Застарілий, але вже списаний (не має потрапити у звіт)
        dec_pc = Computer(inventory_number="DEC-1", purchase_date=date(date.today().year - 7, 1, 1),
                          status="decommissioned", **base_pc_data)

        session.add_all([old_pc, new_pc, dec_pc])
        session.commit()

    service = ReportsService(SessionLocal)
    yield service, saved_room_id  # <--- ПЕРЕДАЄМО ЗБЕРЕЖЕНЕ ЧИСЛО
    engine.dispose()


def test_obsolete_equipment_report(reports_env):
    service, _ = reports_env

    comps, periphs = service.get_obsolete_equipment(years_old=5)

    assert len(comps) == 1
    assert comps[0].inventory_number == "OLD-1"
    assert len(periphs) == 0


def test_room_equipment_report(reports_env):
    service, room_id = reports_env

    room, comps, periphs = service.get_room_equipment(room_id)

    assert room.name == "Серверна"
    assert len(comps) == 3
    assert len(periphs) == 0