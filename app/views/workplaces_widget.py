from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView, QPushButton, QMessageBox, QLabel, \
    QComboBox, QHeaderView
from PyQt6.QtCore import QTimer
from sqlalchemy.exc import IntegrityError
from app.views.models.generic_table_model import GenericTableModel
from app.views.dialogs.workplace_dialog import WorkplaceDialog


class WorkplacesWidget(QWidget):
    def __init__(self, wp_repo, rooms_repo, emp_repo, parent=None):
        super().__init__(parent)
        self.repo = wp_repo
        self.rooms_repo = rooms_repo
        self.emp_repo = emp_repo
        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        top = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук за назвою...")
        self.search.textChanged.connect(self._on_filter_changed)
        top.addWidget(self.search, stretch=1)

        top.addWidget(QLabel("Приміщення:"))
        self.f_room = QComboBox()
        self.f_room.addItem("Усі приміщення", None)
        for r in self.rooms_repo.get_all():
            self.f_room.addItem(r.name, r.id)
        self.f_room.currentIndexChanged.connect(self.load_data)
        top.addWidget(self.f_room)

        self.btn_add = QPushButton("+ Додати")
        self.btn_edit = QPushButton("Редагувати")
        self.btn_delete = QPushButton("Видалити")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        for btn in (self.btn_add, self.btn_edit, self.btn_delete): top.addWidget(btn)
        root.addLayout(top)

        # Використовуємо динамічні атрибути, які ми підготували у WorkplacesRepository
        cols = [
            ("name", "Робоче місце"),
            ("room_name", "Приміщення"),
            ("employee_name", "Співробітник"),
            ("computers_count", "К-ть ПК"),
            ("peripherals_count", "К-ть Периферії")
        ]
        self.model = GenericTableModel(cols)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._edit)
        root.addWidget(self.table)

    def _setup_debounce(self):
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self.load_data)

    def _on_filter_changed(self):
        self._timer.start()

    def load_data(self):
        room_id = self.f_room.currentData()
        items = self.repo.search_and_filter(room_id=room_id, query=self.search.text().strip())
        self.model.refresh(items)

    def _selected(self):
        idx = self.table.currentIndex()
        return self.model.get_object(idx.row()) if idx.isValid() else None

    def _add(self):
        dlg = WorkplaceDialog(self.repo, self.rooms_repo.get_all(), self.emp_repo.get_all(), parent=self)
        if dlg.exec(): self.load_data()

    def _edit(self):
        obj = self._selected()
        if obj:
            dlg = WorkplaceDialog(self.repo, self.rooms_repo.get_all(), self.emp_repo.get_all(), workplace=obj,
                                  parent=self)
            if dlg.exec(): self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj: return
        reply = QMessageBox.question(self, "Видалення", f"Видалити робоче місце «{obj.name}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError:
                QMessageBox.warning(self, "Помилка",
                                    "Неможливо видалити: за робочим місцем закріплено техніку (RESTRICT).")