import pytest
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import User, Computer, ComputerType, StatusLog
from app.repositories.status_logs import StatusLogsRepository
from app.repositories.computers import ComputersRepository
from app.repositories.dictionaries import ComputerTypesRepository
from app.repositories.users import UsersRepository
from app.services.auth import session_manager
from app.views.dialogs.computer_dialog import ComputerDialog

# Ініціалізуємо QApplication для тестів вікон (QDialog)
app = QApplication.instance() or QApplication([])


# ─── ФІКСТУРА ─────────────────────────────────────────────────────────────

@pytest.fixture
def logs_env(tmp_path):
    """Налаштування БД для тестування журналу статусів."""
    test_db_path = tmp_path / "test_logs.db"
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    logs_repo = StatusLogsRepository(SessionLocal)
    c_repo = ComputersRepository(SessionLocal)
    ct_repo = ComputerTypesRepository(SessionLocal)
    u_repo = UsersRepository(SessionLocal)

    # Створюємо користувачів для перевірки, хто саме зробив зміну
    admin = u_repo.create(username="admin", password_hash="hash", role="admin", full_name="Admin User")
    oper = u_repo.create(username="oper", password_hash="hash", role="operator", full_name="Operator User")

    ctype = ct_repo.create(name="Ноутбук")

    yield logs_repo, c_repo, admin, oper, ctype

    # Після тесту обов'язково розлогінюємось
    session_manager.logout()
    engine.dispose()


# ─── ТЕСТ 1: Зміна статусу в діалозі створює запис у журналі ──────────────

def test_status_change_creates_log(logs_env, monkeypatch):
    logs_repo, c_repo, admin, _, ctype = logs_env

    # Імітуємо, що в систему зайшов адміністратор
    session_manager.login(admin)

    # 1. Створюємо комп'ютер зі статусом "Активний" (Додано ВСІ обов'язкові поля)
    comp = c_repo.create(
        inventory_number="PC-TEST-LOG", computer_type_id=ctype.id,
        brand="Apple", model="MacBook", processor="M1", ram_gb=16,
        storage_gb=512, storage_type="SSD", os="macOS", status="active"
    )

    # Заглушка для вікон підтвердження
    monkeypatch.setattr("app.views.dialogs.computer_dialog.QMessageBox.warning", lambda *args, **kwargs: None)

    # 2. Відкриваємо картку комп'ютера і передаємо їй logs_repo
    dialog = ComputerDialog(c_repo, [ctype], [], status_logs_repo=logs_repo, computer=comp)

    # Змінюємо статус на "Ремонт"
    status_idx = dialog.f_status.findData("repair")
    dialog.f_status.setCurrentIndex(status_idx)

    # Натискаємо "Зберегти"
    dialog._save()

    # 3. Перевіряємо журнал!
    logs = logs_repo.get_by_device("computer", comp.id)

    assert len(logs) == 1
    assert logs[0].old_status == "active"
    assert logs[0].new_status == "repair"
    assert logs[0].changed_by == admin.id
    assert "через картку" in logs[0].comment


# ─── ТЕСТ 2: Фільтр по user_id показує лише дії цього оператора ───────────

def test_filter_by_user(logs_env):
    logs_repo, _, admin, oper, _ = logs_env

    # Пишемо історію напряму в репозиторій
    logs_repo.create(device_type="computer", device_id=1, old_status="active", new_status="repair", changed_by=admin.id)
    logs_repo.create(device_type="computer", device_id=2, old_status="active", new_status="storage", changed_by=oper.id)
    logs_repo.create(device_type="peripheral", device_id=1, old_status="storage", new_status="decommissioned",
                     changed_by=admin.id)

    # Запитуємо дії тільки Оператора
    oper_logs = logs_repo.get_recent(user_id=oper.id)
    assert len(oper_logs) == 1
    assert oper_logs[0].changed_by == oper.id

    # Запитуємо дії Адміна
    admin_logs = logs_repo.get_recent(user_id=admin.id)
    assert len(admin_logs) == 2


# ─── ТЕСТ 3: Видалення комп'ютера НЕ видаляє його записи у журналі ────────

def test_computer_deletion_keeps_logs(logs_env):
    logs_repo, c_repo, admin, _, ctype = logs_env

    # Додано ВСІ обов'язкові поля
    comp = c_repo.create(
        inventory_number="PC-TO-DEL", computer_type_id=ctype.id,
        brand="A", model="B", processor="C", ram_gb=8,
        storage_gb=256, storage_type="SSD", os="D", status="active"
    )

    # Створюємо лог списання
    logs_repo.create(device_type="computer", device_id=comp.id, old_status="active", new_status="decommissioned",
                     changed_by=admin.id)

    # ФІЗИЧНО видаляємо комп'ютер з бази
    comp_id_saved = comp.id
    c_repo.delete(comp)
    assert c_repo.get_by_id(comp_id_saved) is None

    # Перевіряємо, що запис в історії зберігся
    logs = logs_repo.get_recent()
    assert len(logs) == 1
    assert logs[0].device_id == comp_id_saved


# ─── ТЕСТ 4: 100 змін статусів без втрат ──────────────────────────────────

def test_100_status_changes(logs_env):
    logs_repo, _, admin, _, _ = logs_env

    # Генеруємо 100 записів про зміну статусів
    for i in range(100):
        logs_repo.create(
            device_type="computer", device_id=1,
            old_status="active", new_status="repair", changed_by=admin.id
        )

    # Запитуємо останні 150 логів
    logs = logs_repo.get_recent(limit=150)

    # Маємо отримати рівно 100 (жоден не загубився)
    assert len(logs) == 100