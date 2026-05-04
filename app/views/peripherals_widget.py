from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView, QPushButton,
    QComboBox, QLabel, QDateEdit, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSortFilterProxyModel
from sqlalchemy.exc import IntegrityError

from app.views.models.peripheral_table_model import PeripheralTableModel
from app.views.dialogs.peripheral_dialog import PeripheralDialog


class PeripheralsWidget(QWidget):
    def __init__(self, repo, periph_types_repo, rooms_repo, workplaces_repo, status_logs_repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.periph_types_repo = periph_types_repo
        self.rooms_repo = rooms_repo
        self.workplaces_repo = workplaces_repo
        self.status_logs_repo = status_logs_repo # Тепер змінна знайдеться!

        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # 1. Пошук та кнопки
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук: інв. номер, модель, серійний номер...")
        self.search.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search, stretch=1)

        self.btn_add = QPushButton("+ Додати")
        self.btn_edit = QPushButton("Редагувати")
        self.btn_delete = QPushButton("Видалити")
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        for btn in (self.btn_add, self.btn_edit, self.btn_delete): top.addWidget(btn)
        root.addLayout(top)

        # 2. Фільтри
        filters = QHBoxLayout()

        filters.addWidget(QLabel("Тип:"))
        self.f_type = QComboBox()
        self.f_type.addItem("Усі типи", None)
        for pt in self.periph_types_repo.get_all():
            self.f_type.addItem(pt.name, pt.id)
        self.f_type.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_type)

        filters.addWidget(QLabel("Кімната:"))
        self.f_room = QComboBox()
        self.f_room.addItem("Усі кімнати", None)
        for r in self.rooms_repo.get_all():
            self.f_room.addItem(f"{r.name} ({r.number})", r.id)
        self.f_room.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_room)

        filters.addWidget(QLabel("Статус:"))
        self.f_status = QComboBox()
        self.f_status.addItem("Усі", None)
        for val, label in [("active", "Активний"), ("repair", "Ремонт"), ("decommissioned", "Списаний"),
                           ("storage", "На зберіганні")]:
            self.f_status.addItem(label, val)
        self.f_status.currentIndexChanged.connect(self.load_data)
        filters.addWidget(self.f_status)

        filters.addWidget(QLabel("Від:"))
        self.f_date_from = QDateEdit(calendarPopup=True)
        self.f_date_from.setDate(QDate(2000, 1, 1))
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

        # 3. Таблиця з ProxyModel
        self.model = PeripheralTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._edit)
        root.addWidget(self.table)

        self.status_bar = QLabel("Завантаження...")
        root.addWidget(self.status_bar)

    def _setup_debounce(self):
        self._timer = QTimer(singleShot=True, interval=300)
        self._timer.timeout.connect(self.load_data)

    def _on_search_changed(self):
        self._timer.start()

    def load_data(self):
        items = self.repo.search_and_filter(
            search=self.search.text().strip(),
            status=self.f_status.currentData(),
            peripheral_type_id=self.f_type.currentData(),
            room_id=self.f_room.currentData(),
            date_from=self.f_date_from.date().toPyDate(),
            date_to=self.f_date_to.date().toPyDate(),
            order_by="inventory_number"
        )
        self.model.refresh(items)
        self.status_bar.setText(f"Знайдено записів: {len(items)}")

    def _reset_filters(self):
        self.search.clear()
        self.f_type.setCurrentIndex(0)
        self.f_room.setCurrentIndex(0)
        self.f_status.setCurrentIndex(0)
        self.f_date_from.setDate(QDate(2000, 1, 1))
        self.f_date_to.setDate(QDate.currentDate())
        self.load_data()

    def _selected(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return None
        source_idx = self.proxy_model.mapToSource(idx)
        return self.model.get_object(source_idx.row())

    def _add(self):
        dlg = PeripheralDialog(self.repo, self.periph_types_repo.get_all(), self.workplaces_repo.get_all(), self.status_logs_repo, parent=self)
        if dlg.exec(): self.load_data()

    def _edit(self):
        obj = self._selected()
        if not obj:
            QMessageBox.information(self, "Увага", "Оберіть рядок для редагування")
            return
        dlg = PeripheralDialog(self.repo, self.periph_types_repo.get_all(), self.workplaces_repo.get_all(),
                               self.status_logs_repo, peripheral=obj, parent=self)
        if dlg.exec(): self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj: return
        reply = QMessageBox.question(self, "Видалення", f"Видалити {obj.brand} {obj.model}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError:
                QMessageBox.critical(self, "Помилка", "Неможливо видалити: є пов'язані записи.")