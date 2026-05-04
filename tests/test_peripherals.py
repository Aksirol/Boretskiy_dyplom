import pytest
from datetime import date
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Room, Workplace, Peripheral, PeripheralType
from app.repositories.peripherals import PeripheralsRepository
from app.repositories.locations import RoomsRepository, WorkplacesRepository
from app.repositories.dictionaries import PeripheralTypesRepository
from app.views.dialogs.peripheral_dialog import PeripheralDialog

# Ініціалізуємо QApplication для тестів PyQt6
app = QApplication.instance() or QApplication([])


# ─── ФІКСТУРА ─────────────────────────────────────────────────────────────

@pytest.fixture
def periph_env(tmp_path):
    """Налаштування середовища з репозиторіями та базовими даними."""
    test_db_path = tmp_path / "test_peripherals_full.db"
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    p_repo = PeripheralsRepository(SessionLocal)
    r_repo = RoomsRepository(SessionLocal)
    wp_repo = WorkplacesRepository(SessionLocal)
    pt_repo = PeripheralTypesRepository(SessionLocal)

    # Створюємо базові дані
    room1 = r_repo.create(name="Офіс 1", number="101", floor=1, building="A")
    wp1 = wp_repo.create(name="Стіл 1", room_id=room1.id)

    type_mon = pt_repo.create(name="Монітор")
    type_print = pt_repo.create(name="Принтер")

    yield p_repo, room1, wp1, type_mon, type_print

    engine.dispose()


# ─── ТЕСТ 1: Фільтр "Принтер" показує лише принтери ───────────────────────

def test_filter_by_type_printer(periph_env):
    p_repo, _, wp1, type_mon, type_print = periph_env

    # ДОДАНО: brand та model
    p_repo.create(inventory_number="MON-1", peripheral_type_id=type_mon.id, workplace_id=wp1.id, brand="Dell",
                  model="X")
    p_repo.create(inventory_number="PRN-1", peripheral_type_id=type_print.id, workplace_id=wp1.id, brand="HP",
                  model="Y")
    p_repo.create(inventory_number="PRN-2", peripheral_type_id=type_print.id, workplace_id=wp1.id, brand="Canon",
                  model="Z")

    results = p_repo.search_and_filter(peripheral_type_id=type_print.id)

    assert len(results) == 2
    assert all(p.peripheral_type.name == "Принтер" for p in results)


# ─── ТЕСТ 2: Одне робоче місце має декілька одиниць периферії ─────────────

def test_multiple_peripherals_per_workplace(periph_env):
    p_repo, _, wp1, type_mon, type_print = periph_env

    # ДОДАНО: brand та model
    p_repo.create(inventory_number="SET-MON-1", peripheral_type_id=type_mon.id, workplace_id=wp1.id, brand="LG",
                  model="1")
    p_repo.create(inventory_number="SET-MON-2", peripheral_type_id=type_mon.id, workplace_id=wp1.id, brand="LG",
                  model="2")
    p_repo.create(inventory_number="SET-PRN-1", peripheral_type_id=type_print.id, workplace_id=wp1.id, brand="HP",
                  model="3")

    results = p_repo.search_and_filter(room_id=wp1.room_id)

    assert len(results) == 3
    assert all(p.workplace_id == wp1.id for p in results)


# ─── ТЕСТ 3: Пошук за серійним номером (ilike) ────────────────────────────

def test_search_by_serial_number(periph_env):
    p_repo, _, wp1, type_mon, _ = periph_env

    p_repo.create(inventory_number="INV-1", peripheral_type_id=type_mon.id, workplace_id=wp1.id,
                  brand="X", model="Y", serial_number="SN-XYZ-999")
    p_repo.create(inventory_number="INV-2", peripheral_type_id=type_mon.id, workplace_id=wp1.id,
                  brand="A", model="B", serial_number="SN-ABC-111")

    results = p_repo.search_and_filter(search="XYZ")
    assert len(results) == 1
    assert results[0].inventory_number == "INV-1"


# ─── ТЕСТ 4: Сортування по даті закупівлі (Найстарші знизу) ───────────────

def test_sort_by_purchase_date(periph_env):
    p_repo, _, wp1, type_mon, _ = periph_env

    p_repo.create(inventory_number="OLD", peripheral_type_id=type_mon.id, workplace_id=wp1.id,
                  brand="A", model="B", purchase_date=date(2018, 5, 10))
    p_repo.create(inventory_number="NEW", peripheral_type_id=type_mon.id, workplace_id=wp1.id,
                  brand="C", model="D", purchase_date=date(2024, 8, 20))

    results = p_repo.search_and_filter(order_by="purchase_date", ascending=False)

    assert results[0].inventory_number == "NEW"
    assert results[1].inventory_number == "OLD"


# ─── ТЕСТ 5: Валідація форми (QMessageBox monkeypatch) ────────────────────

def test_peripheral_dialog_validation(periph_env, monkeypatch):
    p_repo, _, _, type_mon, _ = periph_env

    monkeypatch.setattr("app.views.dialogs.peripheral_dialog.QMessageBox.warning", lambda *args, **kwargs: None)

    dialog = PeripheralDialog(p_repo, peripheral_types=[type_mon], workplaces=[])

    dialog.f_inventory.setText("")
    assert dialog._validate() is False

    dialog.f_inventory.setText("VALID-INV")
    dialog.f_workplace.setCurrentIndex(0)
    assert dialog._validate() is True


# ─── ТЕСТ 6: Видалення периферії ──────────────────────────────────────────

def test_delete_peripheral(periph_env):
    p_repo, _, wp1, type_mon, _ = periph_env

    p = p_repo.create(inventory_number="TO-DELETE", peripheral_type_id=type_mon.id, workplace_id=wp1.id, brand="A",
                      model="B")

    assert p_repo.get_by_id(p.id) is not None
    p_repo.delete(p)
    assert p_repo.get_by_id(p.id) is None


# ─── ТЕСТ 7: Стрес-тест на 50+ записів ────────────────────────────────────

def test_load_50_plus_peripherals(periph_env):
    p_repo, _, wp1, type_mon, _ = periph_env

    for i in range(55):
        p_repo.create(
            inventory_number=f"BULK-PRN-{i}",
            peripheral_type_id=type_mon.id,
            workplace_id=wp1.id,
            brand="Lenovo",
            model="Mouse",
            status="active"
        )

    results = p_repo.search_and_filter()
    assert len(results) == 55