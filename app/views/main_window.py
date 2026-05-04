from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from app.services.auth import session_manager
from app.views.computers_widget import ComputersWidget
from app.views.peripherals_widget import PeripheralsWidget
from app.views.rooms_widget import RoomsWidget
from app.views.workplaces_widget import WorkplacesWidget
from app.views.employees_widget import EmployeesWidget
from app.views.dictionary_widget import DictionaryWidget
from app.views.status_logs_widget import StatusLogsWidget


class MainWindow(QMainWindow):
    def __init__(self, repos, parent=None):
        super().__init__(parent)
        self.repos = repos  # Словник з усіма репозиторіями
        self.user = session_manager.get_user()

        self.setWindowTitle(f"Облік апаратного забезпечення — [{self.user.full_name}]")
        self.setMinimumSize(1100, 700)

        self._setup_ui()
        self._init_modules()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- БІЧНА ПАНЕЛЬ НАВІГАЦІЇ ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)

        logo = QLabel("Hardware AIS")
        logo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("margin: 20px 0;")
        sidebar_layout.addWidget(logo)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; color: white; font-size: 14px; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #34495e; }
            QListWidget::item:selected { background-color: #3498db; }
        """)

        # Визначаємо пункти меню
        self.menu_items = [
            ("Комп'ютери", "comps"),
            ("Периферія", "periph"),
            ("Робочі місця", "workplaces"),
            ("Приміщення", "rooms"),
            ("Співробітники", "employees"),
            ("Типи ПК", "dict_comp"),
            ("Типи периферії", "dict_periph")
        ]

        # Додаємо адмін-розділи
        if self.user.role == "admin":
            self.menu_items.append(("Журнал аудиту", "logs"))

        for label, _ in self.menu_items:
            self.nav_list.addItem(label)

        self.nav_list.currentRowChanged.connect(self._change_page)
        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        # Кнопка виходу
        btn_logout = QPushButton("Вихід")
        btn_logout.setStyleSheet("background-color: #c0392b; color: white; padding: 10px; border: none; margin: 10px;")
        btn_logout.clicked.connect(self.close)
        sidebar_layout.addWidget(btn_logout)

        main_layout.addWidget(self.sidebar)

        # --- ОСНОВНИЙ КОНТЕНТ (Stack) ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

    def _init_modules(self):
        """Ініціалізація віджетів для кожної сторінки."""
        # 1. Комп'ютери
        self.comps_view = ComputersWidget(
            self.repos['computers'],  # 1. repo
            self.repos['comp_types'],  # 2. comp_types_repo
            self.repos['rooms'],  # 3. rooms_repo
            self.repos['workplaces'],  # 4. workplaces_repo
            self.repos['logs']  # 5. status_logs_repo
        )
        self.stack.addWidget(self.comps_view)

        self.periph_view = PeripheralsWidget(
            self.repos['peripherals'],
            self.repos['periph_types'],
            self.repos['rooms'],
            self.repos['workplaces'],
            self.repos['logs']
        )
        self.stack.addWidget(self.periph_view)

        # 3. Робочі місця
        self.wp_view = WorkplacesWidget(
            self.repos['workplaces'], self.repos['rooms'], self.repos['employees']
        )
        self.stack.addWidget(self.wp_view)

        # 4. Приміщення
        self.rooms_view = RoomsWidget(self.repos['rooms'])
        self.stack.addWidget(self.rooms_view)

        # 5. Співробітники
        self.emp_view = EmployeesWidget(self.repos['employees'])
        self.stack.addWidget(self.emp_view)

        # 6. Довідники
        self.dict_comp_view = DictionaryWidget(
            self.repos['comp_types'], "Тип комп'ютера",
            "Не можна видалити: існують ПК цього типу."
        )
        self.stack.addWidget(self.dict_comp_view)

        self.dict_periph_view = DictionaryWidget(
            self.repos['periph_types'], "Тип периферії",
            "Не можна видалити: існує обладнання цього типу."
        )
        self.stack.addWidget(self.dict_periph_view)

        # 7. Аудит (тільки для адміна)
        if self.user.role == "admin":
            self.logs_view = StatusLogsWidget(self.repos['logs'], self.repos['users'])
            self.stack.addWidget(self.logs_view)

        self.nav_list.setCurrentRow(0)

    def _change_page(self, index):
        self.stack.setCurrentIndex(index)