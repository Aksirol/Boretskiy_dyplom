import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

def get_app_dir() -> Path:
    """
    Повертає директорію, де знаходиться .exe файл (для зібраної програми)
    або корінь проекту (під час розробки).
    Тут буде зберігатися наша база даних (щоб вона не видалялася після закриття програми).
    """
    if getattr(sys, 'frozen', False):
        # Програма зібрана через PyInstaller
        return Path(sys.executable).parent
    # Програма запущена з коду
    return Path(__file__).resolve().parent.parent.parent

def get_resource_dir() -> Path:
    """
    Повертає директорію з вшитими ресурсами (міграції, іконки).
    У PyInstaller це тимчасова папка sys._MEIPASS.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent

# Визначаємо шлях до бази даних (вона завжди лежатиме поруч із .exe)
APP_DIR = get_app_dir()
DB_PATH = APP_DIR / "hardware.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Створюємо "двигун" бази даних
engine = create_engine(DATABASE_URL, echo=False)

# Увімкнення зовнішніх ключів (RESTRICT) та WAL-режиму
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# Фабрика сесій для взаємодії з БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для всіх наших моделей
Base = declarative_base()