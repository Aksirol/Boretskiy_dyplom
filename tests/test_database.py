import pytest
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Імпортуємо Base та ВСІ моделі, щоб create_all() знав про них
from app.database.database import Base
from app.database.models import User, Room, Employee, Workplace, ComputerType, Computer, PeripheralType, Peripheral, \
    StatusLog


# ─── ФІКСТУРИ ─────────────────────────────────────────────────────────────

@pytest.fixture
def db_session(tmp_path):
    """
    Створює тимчасову базу даних для тесту, налаштовує WAL і FK,
    повертає сесію, а після тесту закриває її.
    """
    # tmp_path - це вбудована фікстура pytest, яка дає унікальну тимчасову папку
    test_db_path = tmp_path / "test_hardware.db"
    engine = create_engine(f"sqlite:///{test_db_path}")

    # Вмикаємо зовнішні ключі (FK) та WAL
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    # Створюємо всі таблиці
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Повертаємо сесію і шлях до БД у вигляді кортежу, щоб тести могли перевірити файл
    yield session, test_db_path

    # Після виконання тесту: закриваємо сесію і відключаємося
    session.close()
    engine.dispose()


# ─── ТЕСТИ ────────────────────────────────────────────────────────────────

def test_tables_created_successfully(db_session):
    """Тест 1: Перевірка, що всі таблиці створюються без помилок."""
    session, _ = db_session

    # Якщо таблиця Room не існує, цей запит кине помилку (OperationalError)
    rooms_count = session.query(Room).count()
    assert rooms_count == 0


def test_foreign_key_restrict(db_session):
    """Тест 2: Перевірка вставки даних та захисту RESTRICT (каскадне видалення)."""
    session, _ = db_session

    # 1. Створюємо приміщення
    room = Room(name="Серверна", number="101", floor=1, building="Головний корпус")
    session.add(room)
    session.commit()

    # 2. Створюємо робоче місце і прив'язуємо до приміщення
    workplace = Workplace(room_id=room.id, name="Місце сисадмина")
    session.add(workplace)
    session.commit()

    # 3. Спроба видалити приміщення
    # Оскільки до нього прив'язане робоче місце, SQLite має заблокувати це (RESTRICT)
    with pytest.raises(IntegrityError) as exc_info:
        session.delete(room)
        session.commit()

    # Переконуємось, що помилка сталася саме через Foreign Key
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)


def test_wal_file_creation(db_session):
    """Тест 3: Перевірка появи файлу .db-wal після запису даних."""
    session, db_path = db_session

    # Спочатку перевіримо, що wal-файлу ще немає (або він порожній/щойно створений)
    wal_path = Path(f"{db_path}-wal")

    # Робимо перший запис (транзакцію), щоб гарантовано ініціювати WAL
    session.add(Room(name="Аудиторія 1", number="1", floor=1, building="Корпус Б"))
    session.commit()

    # Перевіряємо, чи існує файл WAL на диску
    assert wal_path.exists(), "Файл .db-wal не був створений SQLite"
    assert wal_path.stat().st_size > 0, "Файл .db-wal порожній"