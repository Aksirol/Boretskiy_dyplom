from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QComboBox, QLabel, QDateEdit, QPushButton, QHeaderView
)
from PyQt6.QtCore import QDate
from app.views.models.generic_table_model import GenericTableModel


# 🌟 ДОДАНО: Клас-перекладач для головного журналу аудиту
class LogWrapper:
    def __init__(self, log):
        # 1. Форматуємо дату
        self.date_str = log.changed_at.strftime("%d.%m.%Y %H:%M") if log.changed_at else ""

        # 2. Перекладаємо тип пристрою
        device_map = {
            "computer": "Комп'ютер",
            "peripheral": "Периферія"
        }
        self.device_name = device_map.get(log.device_type, log.device_type)

        # 3. Перекладаємо статуси
        status_map = {
            "active": "Активний",
            "repair": "Ремонт",
            "decommissioned": "Списаний",
            "storage": "На зберіганні",
            "—": "—"
        }
        self.old_st_str = status_map.get(log.old_status, log.old_status)
        self.new_st_str = status_map.get(log.new_status, log.new_status)

        # 4. Витягуємо ім'я користувача
        self.user_name = log.user.full_name if getattr(log, 'user', None) else "Система"

        # 5. Коментар
        self.comment = log.comment or ""


class StatusLogsWidget(QWidget):
    def __init__(self, logs_repo, users_repo, parent=None):
        super().__init__(parent)
        self.repo = logs_repo
        self.users_repo = users_repo
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # Фільтри
        filters = QHBoxLayout()

        filters.addWidget(QLabel("Тип пристрою:"))
        self.f_device = QComboBox()
        self.f_device.addItems(["Усі", "Комп'ютери", "Периферія"])
        self.f_device.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_device)

        filters.addWidget(QLabel("Користувач:"))
        self.f_user = QComboBox()
        self.f_user.addItem("Усі", None)
        for u in self.users_repo.get_all():
            self.f_user.addItem(u.full_name or u.username, u.id)
        self.f_user.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_user)

        filters.addWidget(QLabel("Від:"))
        self.f_date_from = QDateEdit(calendarPopup=True)
        self.f_date_from.setDate(QDate.currentDate().addDays(-30))  # За останні 30 днів
        self.f_date_from.dateChanged.connect(self.load_data)
        filters.addWidget(self.f_date_from)

        filters.addWidget(QLabel("До:"))
        self.f_date_to = QDateEdit(calendarPopup=True)
        self.f_date_to.setDate(QDate.currentDate())
        self.f_date_to.dateChanged.connect(self.load_data)
        filters.addWidget(self.f_date_to)

        self.btn_reset = QPushButton("Скинути")
        self.btn_reset.clicked.connect(self._reset_filters)
        filters.addWidget(self.btn_reset)
        filters.addStretch()
        root.addLayout(filters)

        # Таблиця
        cols = [
            ("date_str", "Дата"),
            ("device_name", "Тип обладнання"),
            ("old_st_str", "Старий статус"),
            ("new_st_str", "Новий статус"),
            ("user_name", "Хто змінив"),
            ("comment", "Коментар")
        ]
        self.model = GenericTableModel(cols)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.table)

    def load_data(self):
        dev_map = {0: None, 1: "computer", 2: "peripheral"}

        # Отримуємо сирі дані з бази
        logs = self.repo.get_recent(
            limit=200,
            device_type=dev_map[self.f_device.currentIndex()],
            user_id=self.f_user.currentData(),
            date_from=self.f_date_from.date().toPyDate(),
            date_to=self.f_date_to.date().toPyDate()
        )

        # 🌟 ЗМІНЕНО: Огортаємо сирі дані у наш клас LogWrapper
        wrapped_logs = [LogWrapper(log) for log in logs]

        # Передаємо підготовлені дані в таблицю
        self.model.refresh(wrapped_logs)

    def _reset_filters(self):
        self.f_device.setCurrentIndex(0)
        self.f_user.setCurrentIndex(0)
        self.f_date_from.setDate(QDate.currentDate().addDays(-30))
        self.f_date_to.setDate(QDate.currentDate())
        self.load_data()