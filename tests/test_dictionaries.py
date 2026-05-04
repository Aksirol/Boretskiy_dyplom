import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database.database import Base
from app.database.models import ComputerType, Employee, Room, Workplace, Computer
from app.repositories.dictionaries import ComputerTypesRepository, EmployeesRepository


# ─── ФІКСТУРА ─────────────────────────────────────────────────────────────

@pytest.fixture
def dict_env(tmp_path):
    """Налаштування ізольованої БД для тестування довідників."""
    test_db_path = tmp_path / "test_dicts.db"
    engine = create_engine(f"sqlite:///{test_db_path}")

    # Обов'язково вмикаємо перевірку зовнішніх ключів (FK) для SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    ct_repo = ComputerTypesRepository(SessionLocal)
    emp_repo = EmployeesRepository(SessionLocal)

    yield SessionLocal, ct_repo, emp_repo

    engine.dispose()


# ─── ТЕСТ 1: Повний CRUD для довідника (на прикладі Співробітників) ───────

def test_crud_employee(dict_env):
    _, _, emp_repo = dict_env

    # 1. Create (Створення)
    emp = emp_repo.create(
        full_name="Шевченко Тарас",
        position="Розробник",
        department="ІТ"
    )
    assert emp.id is not None

    # 2. Read (Читання)
    fetched = emp_repo.get_by_id(emp.id)
    assert fetched.full_name == "Шевченко Тарас"

    # 3. Update (Оновлення)
    emp_repo.update(fetched, position="Senior Розробник")
    updated = emp_repo.get_by_id(emp.id)
    assert updated.position == "Senior Розробник"

    # 4. Delete (Видалення)
    emp_repo.delete(updated)
    assert emp_repo.get_by_id(emp.id) is None


# ─── ТЕСТ 2: RESTRICT при видаленні ComputerType, який використовується ───

def test_delete_computer_type_restrict(dict_env):
    session_factory, ct_repo, _ = dict_env

    # Створюємо тип комп'ютера
    ct = ct_repo.create(name="Ноутбук")

    # Щоб створити комп'ютер, нам потрібні кімната і робоче місце (через обов'язкові зв'язки)
    with session_factory() as session:
        room = Room(name="Офіс", number="101", floor=1, building="Головний")
        session.add(room)
        session.commit()

        wp = Workplace(room_id=room.id, name="Стіл 1")
        session.add(wp)
        session.commit()

        # Створюємо комп'ютер і прив'язуємо до нього наш тип "Ноутбук"
        comp = Computer(
            inventory_number="INV-001",
            computer_type_id=ct.id,
            workplace_id=wp.id,
            brand="Dell", model="XPS", processor="i7",
            ram_gb=16, storage_gb=512, storage_type="SSD", os="Windows 11",
            status="active"
        )
        session.add(comp)
        session.commit()

    # Намагаємося видалити тип комп'ютера.
    # Оскільки існує комп'ютер цього типу, база даних має заблокувати дію.
    with pytest.raises(IntegrityError) as exc_info:
        ct_repo.delete(ct)

    assert "FOREIGN KEY constraint failed" in str(exc_info.value)


# ─── ТЕСТ 3: Підготовка даних для випадаючого списку Workplaces ───────────

def test_employees_for_combobox(dict_env):
    _, _, emp_repo = dict_env
    emp_repo.create(full_name="Григорович Іван", position="Менеджер", department="HR")
    emp_repo.create(full_name="Коваленко Олена", position="Аналітик", department="Фінанси")

    # Майбутній діалог Workplaces викликатиме get_all() для заповнення списку
    employees = emp_repo.get_all()

    assert len(employees) == 2
    # Перевіряємо, що у нас є об'єкти з потрібними полями для відображення
    assert hasattr(employees[0], "id")
    assert hasattr(employees[0], "full_name")


# ─── ТЕСТ 4: Пошук у Employees за прізвищем (і не тільки) ─────────────────

def test_employee_search(dict_env):
    _, _, emp_repo = dict_env
    emp_repo.create(full_name="Петров Петро", position="Системний адміністратор", department="ІТ")
    emp_repo.create(full_name="Іванов Іван", position="Тестувальник", department="QA")

    # Шукаємо за прізвищем
    results = emp_repo.search("Іванов")
    assert len(results) == 1
    assert results[0].full_name == "Іванов Іван"

    # Шукаємо за фрагментом посади (бо ми додали пошук і по посаді, і по відділу)
    results2 = emp_repo.search("адміністратор")
    assert len(results2) == 1
    assert results2[0].full_name == "Петров Петро"

    # Пошук, який не дає результатів
    results3 = emp_repo.search("Директор")
    assert len(results3) == 0