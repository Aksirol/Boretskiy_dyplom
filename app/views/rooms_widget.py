from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView, QPushButton, QMessageBox, QLabel, \
    QHeaderView
from PyQt6.QtCore import QTimer
from sqlalchemy.exc import IntegrityError
from app.views.models.generic_table_model import GenericTableModel
from app.views.dialogs.room_dialog import RoomDialog


class RoomsWidget(QWidget):
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
        self.search.setPlaceholderText("Пошук за назвою, номером, корпусом...")
        self.search.textChanged.connect(self._on_filter_changed)
        top.addWidget(self.search, stretch=1)

        top.addWidget(QLabel("Поверх:"))
        self.f_floor = QLineEdit()
        self.f_floor.setFixedWidth(50)
        self.f_floor.textChanged.connect(self._on_filter_changed)
        top.addWidget(self.f_floor)

        self.btn_add = QPushButton("+ Додати")
        self.btn_edit = QPushButton("Редагувати")
        self.btn_delete = QPushButton("Видалити")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        for btn in (self.btn_add, self.btn_edit, self.btn_delete): top.addWidget(btn)
        root.addLayout(top)

        cols = [("name", "Назва"), ("number", "Номер"), ("floor", "Поверх"), ("building", "Корпус")]
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
        floor_text = self.f_floor.text().strip()
        floor_val = int(floor_text) if floor_text.lstrip('-').isdigit() else None

        items = self.repo.search_and_filter(query=self.search.text().strip(), floor=floor_val)
        self.model.refresh(items)

    def _selected(self):
        idx = self.table.currentIndex()
        return self.model.get_object(idx.row()) if idx.isValid() else None

    def _add(self):
        if RoomDialog(self.repo, parent=self).exec(): self.load_data()

    def _edit(self):
        obj = self._selected()
        if obj and RoomDialog(self.repo, room=obj, parent=self).exec(): self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj: return
        reply = QMessageBox.question(self, "Видалення", f"Видалити приміщення «{obj.name}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError:
                QMessageBox.warning(self, "Помилка",
                                    "Неможливо видалити приміщення: у ньому є робочі місця (RESTRICT).")