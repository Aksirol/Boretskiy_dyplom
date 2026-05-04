from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableView, QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer
from sqlalchemy.exc import IntegrityError
from app.views.models.generic_table_model import GenericTableModel
from app.views.dialogs.simple_type_dialog import SimpleTypeDialog


class DictionaryWidget(QWidget):
    """Універсальний віджет для простих довідників (Типи ПК, Типи периферії)"""

    def __init__(self, repo, entity_name: str, fk_error_msg: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.entity_name = entity_name
        self.fk_error_msg = fk_error_msg  # Повідомлення при спробі видалити зайнятий тип
        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # Панель інструментів
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук за назвою...")
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

        # Таблиця
        self.model = GenericTableModel([("name", "Назва")])
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
        dlg = SimpleTypeDialog(self.repo, entity_name=self.entity_name, parent=self)
        if dlg.exec():
            self.load_data()

    def _edit(self):
        obj = self._selected()
        if not obj:
            return
        dlg = SimpleTypeDialog(self.repo, obj=obj, entity_name=self.entity_name, parent=self)
        if dlg.exec():
            self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj:
            return
        reply = QMessageBox.question(
            self, "Видалення",
            f"Видалити {self.entity_name.lower()} «{obj.name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError as e:
                # Каскадний захист: не даємо видалити тип, якщо він використовується
                if "FOREIGN KEY constraint failed" in str(e.orig):
                    QMessageBox.warning(self, "Заборона видалення", self.fk_error_msg)
                else:
                    QMessageBox.critical(self, "Помилка бази даних", str(e.orig))