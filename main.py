import sys
import traceback
import bcrypt
from PyQt6.QtWidgets import QApplication, QMessageBox

from app.database.database import SessionLocal, engine, Base, get_resource_dir
from alembic.config import Config
from alembic import command
from app.repositories.users import UsersRepository
from app.repositories.dictionaries import ComputerTypesRepository, PeripheralTypesRepository, EmployeesRepository
from app.repositories.locations import RoomsRepository, WorkplacesRepository
from app.repositories.computers import ComputersRepository
from app.repositories.peripherals import PeripheralsRepository
from app.repositories.status_logs import StatusLogsRepository

from app.services.auth import AuthService
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow

# 🌟 ДОДАНО: Імпортуємо твій скрипт для наповнення бази даними
import seed_data


def run_migrations():
    """Автоматично застосовує міграції бази даних (upgrade head)."""
    resource_dir = get_resource_dir()

    alembic_cfg = Config(str(resource_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(resource_dir / "alembic"))

    command.upgrade(alembic_cfg, "head")


def ensure_initial_data(users_repo):
    """
    Перевіряє, чи порожня база.
    Якщо так — запускає повне наповнення бази з файлу seed_data.py.
    """
    users = users_repo.get_all()

    # Якщо користувачів немає, значить база абсолютно нова
    if len(users) == 0:
        print("База порожня. Запускаємо автоматичне наповнення...")
        try:
            # Викликаємо функцію seed() з твого файлу seed_data.py
            seed_data.seed(clear=False)
            print("✅ Базу успішно наповнено тестовими даними!")
        except Exception as e:
            QMessageBox.critical(None, "Помилка наповнення", f"Не вдалося заповнити базу даними:\n{e}")
    else:
        print("✅ База вже містить дані. Пропускаємо наповнення.")


def main():
    # 1. Створюємо структуру таблиць
    run_migrations()

    # 2. Ініціалізуємо графічний додаток
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 3. Ініціалізація репозиторіїв
    repos = {
        'users': UsersRepository(SessionLocal),
        'comp_types': ComputerTypesRepository(SessionLocal),
        'periph_types': PeripheralTypesRepository(SessionLocal),
        'employees': EmployeesRepository(SessionLocal),
        'rooms': RoomsRepository(SessionLocal),
        'workplaces': WorkplacesRepository(SessionLocal),
        'computers': ComputersRepository(SessionLocal),
        'peripherals': PeripheralsRepository(SessionLocal),
        'logs': StatusLogsRepository(SessionLocal)
    }

    # 4. Авторизація
    auth_service = AuthService(repos['users'])

    # 5. 🌟 Запускаємо перевірку і наповнення бази
    ensure_initial_data(repos['users'])

    # 6. Запускаємо вікно входу
    login_dlg = LoginWindow(auth_service)

    if login_dlg.exec():
        # Вхід успішний, відкриваємо головне вікно
        window = MainWindow(repos)
        window.show()
        sys.exit(app.exec())
    else:
        # Користувач закрив вікно входу
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"Сталася критична помилка:\n{str(e)}\n\nДеталі:\n{error_details}"

        print(error_msg)

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        QMessageBox.critical(None, "Фатальна помилка програми", error_msg)
        sys.exit(1)