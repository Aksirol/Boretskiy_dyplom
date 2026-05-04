from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableView, QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer
from sqlalchemy.exc import IntegrityError
from app.views.models.generic_table_model import GenericTableModel
from app.views.dialogs.employee_dialog import EmployeeDialog


class EmployeesWidget(QWidget):
    def __init__(self, repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук за ПІБ, відділом, посадою...")
        self.search.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search, stretch=1)

        self.btn_add = QPushButton("+ Додати")
        self.btn_edit = QPushButton("Редагувати")
        self.btn_delete = QPushButton("Видалити")

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)

        for btn in (self.btn_add, self.btn_edit, self.btn_delete):
            top.addWidget(btn)
        root.addLayout(top)

        # Використовуємо наш GenericTableModel
        columns = [
            ("full_name", "ПІБ"),
            ("position", "Посада"),
            ("department", "Відділ"),
            ("phone", "Телефон"),
            ("email", "Email"),
        ]
        self.model = GenericTableModel(columns)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._edit)
        root.addWidget(self.table)

    def _setup_debounce(self):
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self.load_data)

    def _on_search_changed(self):
        self._timer.start()

    def load_data(self):
        items = self.repo.search(self.search.text().strip())
        self.model.refresh(items)

    def _selected(self):
        idx = self.table.currentIndex()
        return self.model.get_object(idx.row()) if idx.isValid() else None

    def _add(self):
        if EmployeeDialog(self.repo, parent=self).exec():
            self.load_data()

    def _edit(self):
        obj = self._selected()
        if not obj:
            return
        if EmployeeDialog(self.repo, employee=obj, parent=self).exec():
            self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj:
            return
        reply = QMessageBox.question(
            self, "Видалення",
            f"Видалити співробітника «{obj.full_name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError as e:
                # Опрацювання каскадного захисту RESTRICT
                if "FOREIGN KEY constraint failed" in str(e.orig):
                    QMessageBox.warning(
                        self, "Заборона видалення",
                        "Неможливо видалити цього співробітника, оскільки за ним закріплено робоче місце."
                    )
                else:
                    QMessageBox.critical(self, "Помилка бази даних", str(e.orig))