import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

from app.database.database import SessionLocal, engine, Base
from app.repositories.users import UsersRepository
from app.repositories.dictionaries import ComputerTypesRepository, PeripheralTypesRepository, EmployeesRepository
from app.repositories.locations import RoomsRepository, WorkplacesRepository
from app.repositories.computers import ComputersRepository
from app.repositories.peripherals import PeripheralsRepository
from app.repositories.status_logs import StatusLogsRepository

from app.services.auth import AuthService
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow

def main():
    # 1. Переконуємось, що БД ініціалізована (таблиці існують)
    # Хоча ми використовуємо Alembic, цей крок корисний для першого запуску
    Base.metadata.create_all(bind=engine)

    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Стабільний вигляд на всіх ОС

    # 2. Ініціалізація репозиторіїв (Unit of Work фабрика)
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

    # 3. Авторизація
    auth_service = AuthService(repos['users'])
    login_dlg = LoginWindow(auth_service)

    if login_dlg.exec():
        # Вхід успішний
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
        # 1. Формуємо детальний текст помилки (допоможе при відладці зібраного .exe)
        error_details = traceback.format_exc()
        error_msg = f"Сталася критична помилка:\n{str(e)}\n\nДеталі:\n{error_details}"

        # Залишаємо вивід у консоль для зручності розробки
        print(error_msg)

        # 2. Безпечно отримуємо або створюємо QApplication
        # Якщо програма впала ДО створення app у функції main(), ми маємо створити його тут,
        # інакше вікно QMessageBox просто не з'явиться.
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # 3. Виводимо графічне повідомлення для користувача
        QMessageBox.critical(None, "Фатальна помилка програми", error_msg)

        # 4. Завершуємо роботу з кодом помилки
        sys.exit(1)