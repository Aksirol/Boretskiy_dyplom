import sys
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
        # Глобальний перехват помилок для запобігання тихому "вильоту"
        print(f"Критична помилка: {e}")
        # Тут можна вивести QMessageBox для користувача