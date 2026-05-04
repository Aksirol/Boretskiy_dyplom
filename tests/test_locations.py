import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database.database import Base
from app.database.models import Room, Workplace, Computer, ComputerType, Peripheral, PeripheralType
from app.repositories.locations import RoomsRepository, WorkplacesRepository


# ─── ФІКСТУРА ─────────────────────────────────────────────────────────────

@pytest.fixture
def loc_env(tmp_path):
    """Ізольована БД для тестування Приміщень та Робочих місць."""
    test_db_path = tmp_path / "test_locations.db"
    engine = create_engine(f"sqlite:///{test_db_path}")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    rooms_repo = RoomsRepository(SessionLocal)
    wp_repo = WorkplacesRepository(SessionLocal)

    yield SessionLocal, rooms_repo, wp_repo

    engine.dispose()


# ─── ТЕСТ 1: Сортування та фільтр по поверху ──────────────────────────────

def test_rooms_filter_and_sort(loc_env):
    _, rooms_repo, _ = loc_env

    # Створюємо кімнати врозкид
    rooms_repo.create(name="Серверна", number="201", floor=2, building="Головний")
    rooms_repo.create(name="Аудиторія Б", number="102", floor=1, building="Головний")
    rooms_repo.create(name="Аудиторія А", number="101", floor=1, building="Головний")

    # 1. Перевірка фільтру: шукаємо тільки перший поверх
    floor_1_rooms = rooms_repo.search_and_filter(floor=1)
    assert len(floor_1_rooms) == 2

    # 2. Перевірка сортування: репозиторій має сортувати за (Корпус -> Поверх -> Назва)
    all_rooms = rooms_repo.search_and_filter()
    assert all_rooms[0].name == "Аудиторія А"
    assert all_rooms[1].name == "Аудиторія Б"
    assert all_rooms[2].name == "Серверна"


# ─── ТЕСТ 2: Захист RESTRICT при видаленні кімнати ────────────────────────

def test_room_delete_restrict(loc_env):
    _, rooms_repo, wp_repo = loc_env

    room = rooms_repo.create(name="Офіс", number="1", floor=1, building="А")

    # Створюємо робоче місце і прив'язуємо до кімнати
    wp_repo.create(name="Робоче місце 1", room_id=room.id)

    # Спроба видалити кімнату має бути заблокована базою даних
    with pytest.raises(IntegrityError) as exc_info:
        rooms_repo.delete(room)

    assert "FOREIGN KEY constraint failed" in str(exc_info.value)


# ─── ТЕСТ 3: Перевірка лічильників техніки (Subquery Count) ───────────────

def test_workplace_counters(loc_env):
    session_factory, rooms_repo, wp_repo = loc_env

    # 1. Підготовка базових даних
    room = rooms_repo.create(name="Кабінет IT", number="1", floor=1, building="А")
    wp = wp_repo.create(name="Стіл сисадмина", room_id=room.id)

    # 2. Перевіряємо, що лічильники спочатку порожні
    wp_initial = wp_repo.search_and_filter(room_id=room.id)[0]
    assert wp_initial.computers_count == 0
    assert wp_initial.peripherals_count == 0

    # 3. Додаємо техніку безпосередньо через сесію
    with session_factory() as session:
        # Спочатку створюємо обов'язкові типи для зовнішніх ключів
        c_type = ComputerType(name="PC")
        p_type = PeripheralType(name="Monitor")
        session.add_all([c_type, p_type])
        session.commit()

        # Додаємо комп'ютер та монітор на це робоче місце
        comp = Computer(
            inventory_number="C001", computer_type_id=c_type.id, workplace_id=wp.id,
            brand="HP", model="Pro", processor="i5", ram_gb=8, storage_gb=256,
            storage_type="SSD", os="Win10", status="active"
        )
        periph = Peripheral(
            inventory_number="P001", peripheral_type_id=p_type.id, workplace_id=wp.id,
            brand="Dell", model="U2419H", status="active"
        )
        session.add_all([comp, periph])
        session.commit()

    # 4. Отримуємо робоче місце знову і перевіряємо, чи спрацював SQL-підзапит
    wp_updated = wp_repo.search_and_filter(room_id=room.id)[0]
    assert wp_updated.computers_count == 1
    assert wp_updated.peripherals_count == 1