import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Визначаємо шлях до бази даних. Вона буде лежати в корені проекту.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "hardware.db"
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