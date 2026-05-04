# views/computers_widget.py
from repositories.computers import ComputersRepository

from app.views.models.computer_table_model import ComputerTableModel
from app.views.dialogs.computer_dialog import ComputerDialog

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableView, QPushButton, QComboBox, QLabel,
    QDateEdit, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QDate
from sqlalchemy.exc import IntegrityError

class ComputersWidget(QWidget):
    def __init__(self, repo: ComputersRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self._sort_col = "inventory_number"
        self._sort_asc = True
        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    # ── UI ──────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # Рядок пошуку + кнопки CRUD
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук за інв. номером, моделлю, IP, MAC...")
        self.search.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search, stretch=1)

        self.btn_add    = QPushButton("+ Додати")
        self.btn_edit   = QPushButton("Редагувати")
        self.btn_delete = QPushButton("Видалити")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        for btn in (self.btn_add, self.btn_edit, self.btn_delete):
            top.addWidget(btn)
        root.addLayout(top)

        # Панель фільтрів
        filters = QHBoxLayout()

        filters.addWidget(QLabel("Статус:"))
        self.f_status = QComboBox()
        self.f_status.addItem("Усі", None)
        for val, label in [("active","Активний"),("repair","Ремонт"),
                           ("decommissioned","Списаний"),("storage","На зберіганні")]:
            self.f_status.addItem(label, val)
        self.f_status.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_status)

        filters.addWidget(QLabel("Від:"))
        self.f_date_from = QDateEdit()
        self.f_date_from.setCalendarPopup(True)
        self.f_date_from.setSpecialValueText("—")     # порожнє значення
        self.f_date_from.setDate(QDate(2000, 1, 1))
        self.f_date_from.dateChanged.connect(self.load_data)
        filters.addWidget(self.f_date_from)

        filters.addWidget(QLabel("До:"))
        self.f_date_to = QDateEdit()
        self.f_date_to.setCalendarPopup(True)
        self.f_date_to.setDate(QDate.currentDate())
        self.f_date_to.dateChanged.connect(self.load_data)
        filters.addWidget(self.f_date_to)

        self.btn_reset = QPushButton("Скинути фільтри")
        self.btn_reset.clicked.connect(self._reset_filters)
        filters.addWidget(self.btn_reset)
        filters.addStretch()
        root.addLayout(filters)

        # Таблиця
        self.model = ComputerTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_click)
        self.table.doubleClicked.connect(self._edit)
        root.addWidget(self.table)

        self.status_bar = QLabel("Завантаження...")
        root.addWidget(self.status_bar)

    # ── Debounce для пошуку ─────────────────────────────────

    def _setup_debounce(self):
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self.load_data)

    def _on_search_changed(self):
        self._timer.start()   # перезапускає таймер при кожній літері

    # ── Сортування по кліку на заголовок ───────────────────

    def _on_header_click(self, section: int):
        attr, _ = ComputerTableModel.COLUMNS[section]
        if self._sort_col == attr:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = attr
            self._sort_asc = True
        self.load_data()

    # ── Завантаження даних ──────────────────────────────────

    def load_data(self):
        date_from = self.f_date_from.date().toPyDate()
        date_to   = self.f_date_to.date().toPyDate()

        items = self.repo.search_and_filter(
            search=self.search.text().strip(),
            status=self.f_status.currentData(),
            date_from=date_from,
            date_to=date_to,
            order_by=self._sort_col,
            ascending=self._sort_asc,
        )
        self.model.refresh(items)
        self.status_bar.setText(f"Знайдено записів: {len(items)}")

    def _reset_filters(self):
        self.search.clear()
        self.f_status.setCurrentIndex(0)
        self.f_date_from.setDate(QDate(2000, 1, 1))
        self.f_date_to.setDate(QDate.currentDate())
        self.load_data()

    # ── CRUD ────────────────────────────────────────────────

    def _selected(self):
        idx = self.table.currentIndex()
        return self.model.get_object(idx.row()) if idx.isValid() else None

    def _add(self):
        dlg = ComputerDialog(self.repo, parent=self)
        if dlg.exec():
            self.load_data()

    def _edit(self):
        obj = self._selected()
        if not obj:
            QMessageBox.information(self, "Увага", "Оберіть рядок для редагування")
            return
        dlg = ComputerDialog(self.repo, computer=obj, parent=self)
        if dlg.exec():
            self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj:
            return
        reply = QMessageBox.question(
            self, "Видалення",
            f"Видалити комп'ютер «{obj.inventory_number}»?\nЦю дію не можна скасувати.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError:
                QMessageBox.critical(self, "Помилка",
                    "Неможливо видалити: є пов'язані записи в інших таблицях.")