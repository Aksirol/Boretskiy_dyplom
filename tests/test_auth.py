import pytest
import bcrypt
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import User
from app.repositories.users import UsersRepository
from app.services.auth import AuthService, session_manager, require_role
from app.views.login_window import LoginWindow

# Створюємо глобальний екземпляр QApplication для тестів PyQt6
# (PyQt вимагає, щоб додаток існував до створення будь-яких віджетів)
app = QApplication.instance() or QApplication([])


@pytest.fixture
def auth_env(tmp_path):
    """Фікстура для налаштування тестової БД, репозиторію та сервісу авторизації."""
    # 1. Налаштовуємо БД у пам'яті
    test_db_path = tmp_path / "test_auth.db"
    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # 2. Створюємо двох користувачів: адміна та оператора
    with SessionLocal() as session:
        admin_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
        oper_pw = bcrypt.hashpw(b"oper123", bcrypt.gensalt()).decode('utf-8')

        session.add_all([
            User(username="admin", password_hash=admin_pw, role="admin", full_name="Admin"),
            User(username="operator", password_hash=oper_pw, role="operator", full_name="Oper")
        ])
        session.commit()

    # 3. Ініціалізуємо компоненти
    repo = UsersRepository(SessionLocal)
    service = AuthService(repo)

    yield service, SessionLocal

    # 4. Очищаємо глобальну сесію після кожного тесту, щоб вони не впливали один на одного
    session_manager.logout()


# ─── ТЕСТ 1: Правильний пароль → вхід, user у Session ──────────────────────

def test_login_success(auth_env):
    service, _ = auth_env

    # Перевіряємо логіку сервісу
    is_valid = service.authenticate("admin", "admin123")
    assert is_valid is True

    # Перевіряємо, чи зберігся користувач у глобальному стані
    current_user = session_manager.get_user()
    assert current_user is not None
    assert current_user.username == "admin"
    assert current_user.role == "admin"


# ─── ТЕСТ 2: Неправильний пароль → помилка у вікні, повторна спроба ────────

def test_login_fail_ui(auth_env):
    service, _ = auth_env
    window = LoginWindow(service)

    # Симулюємо введення неправильних даних
    window.f_username.setText("admin")
    window.f_password.setText("wrong_password")
    window.btn_login.click()

    # Перевіряємо, що вхід не відбувся і сесія порожня
    assert session_manager.get_user() is None

    # Перевіряємо, що вікно показало помилку і очистило поле пароля для повторної спроби
    assert window.error_label.text() == "Невірний логін або пароль"
    assert window.f_password.text() == ""  # Поле пароля має бути очищене


# ─── ТЕСТ 3: @require_role('admin') від operator → відмова ─────────────────

def test_require_role_denied(auth_env):
    service, _ = auth_env

    # Успішно логінимося як оператор
    service.authenticate("operator", "oper123")

    # Створюємо тестову функцію, захищену декоратором
    @require_role("admin")
    def protected_admin_action():
        return "Таємні дані"

    # Перевіряємо, що виклик генерує PermissionError
    # (У реальному додатку (UI) ми обгорнемо виклики таких функцій у try...except,
    # щоб замість падіння програми показати вікно QMessageBox з текстом помилки).
    with pytest.raises(PermissionError) as exc:
        protected_admin_action()

    assert "доступна лише адміністраторам" in str(exc.value)


# ─── ТЕСТ 4: Logout очищає Session ─────────────────────────────────────────

def test_logout_clears_session(auth_env):
    service, _ = auth_env

    # Логінимося
    service.authenticate("admin", "admin123")
    assert session_manager.get_user() is not None

    # Робимо вихід
    session_manager.logout()

    # Перевіряємо, що сесія очистилась
    assert session_manager.get_user() is None