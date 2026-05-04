import pytest
from datetime import date
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Room, Workplace, Computer, ComputerType
from app.repositories.computers import ComputersRepository
from app.repositories.locations import RoomsRepository, WorkplacesRepository
from app.repositories.dictionaries import ComputerTypesRepository
from app.views.dialogs.computer_dialog import ComputerDialog

# Ініціалізуємо QApplication для тестів PyQt6
app = QApplication.instance() or QApplication([])


# ─── ФІКСТУРА ─────────────────────────────────────────────────────────────

@pytest.fixture
def comp_env(tmp_path):
    """Налаштування середовища з усіма потрібними репозиторіями та базовими даними."""
    test_db_path = tmp_path / "test_computers.db"
    # Для перевірки SQL-запитів в консолі можна поставити echo=True,
    # але для чистих тестів залишаємо False
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # Ініціалізуємо репозиторії
    c_repo = ComputersRepository(SessionLocal)
    r_repo = RoomsRepository(SessionLocal)
    wp_repo = WorkplacesRepository(SessionLocal)
    ct_repo = ComputerTypesRepository(SessionLocal)

    # Створюємо базові дані для зв'язків
    room1 = r_repo.create(name="Офіс 1", number="101", floor=1, building="A")
    room2 = r_repo.create(name="Офіс 2", number="102", floor=1, building="A")

    wp1 = wp_repo.create(name="Стіл 1", room_id=room1.id)
    wp2 = wp_repo.create(name="Стіл 2", room_id=room2.id)

    ctype = ct_repo.create(name="Десктоп")

    yield c_repo, room1, room2, wp1, wp2, ctype

    engine.dispose()


# ─── ТЕСТ 1: Пошук за IP-адресою (ilike) ──────────────────────────────────

def test_search_by_ip(comp_env):
    c_repo, _, _, wp1, _, ctype = comp_env

    # Створюємо два ПК з різними IP
    c_repo.create(inventory_number="INV-01", computer_type_id=ctype.id, workplace_id=wp1.id,
                  brand="Dell", model="A", processor="i5", ram_gb=8, storage_gb=256,
                  storage_type="SSD", os="Win", ip_address="192.168.1.50", status="active")
    c_repo.create(inventory_number="INV-02", computer_type_id=ctype.id, workplace_id=wp1.id,
                  brand="HP", model="B", processor="i5", ram_gb=8, storage_gb=256,
                  storage_type="SSD", os="Win", ip_address="10.0.0.5", status="active")

    # Шукаємо "192.168"
    results = c_repo.search_and_filter(search="192.168")
    assert len(results) == 1
    assert results[0].inventory_number == "INV-01"


# ─── ТЕСТ 2: Фільтр по кімнаті (Подвійний JOIN) ───────────────────────────

def test_filter_by_room(comp_env):
    c_repo, room1, room2, wp1, wp2, ctype = comp_env

    # ПК 1 знаходиться на робочому місці 1 (яке в кімнаті 1)
    c_repo.create(inventory_number="PC-ROOM1", computer_type_id=ctype.id, workplace_id=wp1.id,
                  brand="X", model="Y", processor="Z", ram_gb=8, storage_gb=256,
                  storage_type="SSD", os="W", status="active")
    # ПК 2 знаходиться на робочому місці 2 (яке в кімнаті 2)
    c_repo.create(inventory_number="PC-ROOM2", computer_type_id=ctype.id, workplace_id=wp2.id,
                  brand="X", model="Y", processor="Z", ram_gb=8, storage_gb=256,
                  storage_type="SSD", os="W", status="active")

    # Фільтруємо за room1.id. SQLAlchemy має зробити правильні JOIN'и
    results = c_repo.search_and_filter(room_id=room1.id)
    assert len(results) == 1
    assert results[0].inventory_number == "PC-ROOM1"


# ─── ТЕСТ 3: Сортування по даті закупівлі (Найстарші знизу) ───────────────

def test_sort_by_purchase_date(comp_env):
    c_repo, _, _, wp1, _, ctype = comp_env

    c_repo.create(inventory_number="OLD-PC", computer_type_id=ctype.id, workplace_id=wp1.id,
                  brand="A", model="A", processor="A", ram_gb=4, storage_gb=128,
                  storage_type="HDD", os="Win7", status="active", purchase_date=date(2015, 5, 10))
    c_repo.create(inventory_number="NEW-PC", computer_type_id=ctype.id, workplace_id=wp1.id,
                  brand="B", model="B", processor="B", ram_gb=16, storage_gb=512,
                  storage_type="SSD", os="Win11", status="active", purchase_date=date(2023, 8, 20))

    # Сортуємо по даті за спаданням (descending) -> Нові зверху, старі знизу
    results = c_repo.search_and_filter(order_by="purchase_date", ascending=False)

    assert results[0].inventory_number == "NEW-PC"
    assert results[1].inventory_number == "OLD-PC"  # Найстарший опинився внизу (індекс 1)


# ─── ТЕСТ 4: Валідація форми (QMessageBox monkeypatch) ────────────────────

def test_computer_dialog_validation(comp_env, monkeypatch):
    c_repo, _, _, _, _, ctype = comp_env

    # ❗ ВАЖЛИВИЙ ТРЮК: Підміняємо виклик вікна з помилкою на "пустушку",
    # щоб тест не "завис", чекаючи поки хтось натисне "ОК" на спливаючому вікні.
    monkeypatch.setattr("app.views.dialogs.computer_dialog.QMessageBox.warning", lambda *args, **kwargs: None)

    dialog = ComputerDialog(c_repo, computer_types=[ctype], workplaces=[])

    # Залишаємо інвентарний номер порожнім
    dialog.f_inventory.setText("")

    # Валідація має провалитися
    assert dialog._validate() is False

    # Вводимо валідне значення
    dialog.f_inventory.setText("INV-TEST-VALID")
    assert dialog._validate() is True


# ─── ТЕСТ 5: Видалення комп'ютера ─────────────────────────────────────────

def test_delete_computer(comp_env):
    c_repo, _, _, wp1, _, ctype = comp_env

    comp = c_repo.create(inventory_number="TO-DELETE", computer_type_id=ctype.id, workplace_id=wp1.id,
                         brand="A", model="A", processor="A", ram_gb=8, storage_gb=256,
                         storage_type="SSD", os="A", status="active")

    # Перевіряємо, що він є
    assert c_repo.get_by_id(comp.id) is not None

    # Видаляємо
    c_repo.delete(comp)

    # Перевіряємо, що він зник
    assert c_repo.get_by_id(comp.id) is None


# ─── ТЕСТ 6: Стрес-тест на 50+ записів ────────────────────────────────────

def test_load_50_plus_records(comp_env):
    c_repo, _, _, wp1, _, ctype = comp_env

    # Генеруємо 55 комп'ютерів
    for i in range(55):
        c_repo.create(
            inventory_number=f"BULK-{i}", computer_type_id=ctype.id, workplace_id=wp1.id,
            brand="Lenovo", model="OptiPlex", processor="Ryzen 5", ram_gb=16, storage_gb=512,
            storage_type="NVMe", os="Ubuntu", status="active"
        )

    # Завантажуємо всі
    results = c_repo.search_and_filter()

    # Перевіряємо, що система не впала і дістала всі 55
    assert len(results) == 55