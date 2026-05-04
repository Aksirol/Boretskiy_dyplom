from datetime import datetime, date
from sqlalchemy import Integer, String, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) # 'admin' або 'operator'
    full_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Зв'язок з журналом статусів
    status_logs = relationship("StatusLog", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    number: Mapped[str] = mapped_column(String(20))
    floor: Mapped[int] = mapped_column(Integer)
    building: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Зв'язок із робочими місцями. За замовчуванням в SQLite працює RESTRICT.
    workplaces = relationship("Workplace", back_populates="room", passive_deletes=True)

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)

    workplaces = relationship("Workplace", back_populates="employee")

class Workplace(Base):
    __tablename__ = "workplaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    room = relationship("Room", back_populates="workplaces")
    employee = relationship("Employee", back_populates="workplaces")
    computers = relationship("Computer", back_populates="workplace", passive_deletes=True)
    peripherals = relationship("Peripheral", back_populates="workplace", passive_deletes=True)

class ComputerType(Base):
    __tablename__ = "computer_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    computers = relationship("Computer", back_populates="computer_type", passive_deletes=True)

class Computer(Base):
    __tablename__ = "computers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    computer_type_id: Mapped[int] = mapped_column(ForeignKey("computer_types.id"), nullable=False)
    workplace_id: Mapped[int] = mapped_column(ForeignKey("workplaces.id"), nullable=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    processor: Mapped[str] = mapped_column(String(100))
    ram_gb: Mapped[int] = mapped_column(Integer)
    storage_gb: Mapped[int] = mapped_column(Integer)
    storage_type: Mapped[str] = mapped_column(String(20)) # HDD, SSD
    os: Mapped[str] = mapped_column(String(50))
    ip_address: Mapped[str] = mapped_column(String(15), nullable=True)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="В роботі")
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    computer_type = relationship("ComputerType", back_populates="computers")
    workplace = relationship("Workplace", back_populates="computers")

class PeripheralType(Base):
    __tablename__ = "peripheral_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    peripherals = relationship("Peripheral", back_populates="peripheral_type", passive_deletes=True)

class Peripheral(Base):
    __tablename__ = "peripherals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    peripheral_type_id: Mapped[int] = mapped_column(ForeignKey("peripheral_types.id"), nullable=False)
    workplace_id: Mapped[int] = mapped_column(ForeignKey("workplaces.id"), nullable=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    serial_number: Mapped[str] = mapped_column(String(100), nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="В роботі")
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    peripheral_type = relationship("PeripheralType", back_populates="peripherals")
    workplace = relationship("Workplace", back_populates="peripherals")

class StatusLog(Base):
    __tablename__ = "status_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False) # 'computer' або 'peripheral'
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_status: Mapped[str] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="status_logs")