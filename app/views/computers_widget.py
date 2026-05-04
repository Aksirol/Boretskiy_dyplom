from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView, QPushButton,
    QComboBox, QLabel, QDateEdit, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSortFilterProxyModel
from sqlalchemy.exc import IntegrityError

from app.views.models.computer_table_model import ComputerTableModel
from app.views.dialogs.computer_dialog import ComputerDialog

from PyQt6.QtWidgets import QMenu, QFileDialog
from app.services.exporter import Exporter


class ComputersWidget(QWidget):
    def __init__(self, repo, comp_types_repo, rooms_repo, workplaces_repo, status_logs_repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.comp_types_repo = comp_types_repo
        self.rooms_repo = rooms_repo
        self.workplaces_repo = workplaces_repo
        self.status_logs_repo = status_logs_repo

        self._setup_ui()
        self._setup_debounce()
        self.load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # 1. Рядок пошуку + Кнопки CRUD
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук: інв. номер, модель, IP, MAC...")
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

        # 2. Панель потужних фільтрів
        filters = QHBoxLayout()

        filters.addWidget(QLabel("Тип:"))
        self.f_type = QComboBox()
        self.f_type.addItem("Усі типи", None)
        for ct in self.comp_types_repo.get_all():
            self.f_type.addItem(ct.name, ct.id)
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
        self.f_date_from = QDateEdit()
        self.f_date_from.setCalendarPopup(True)
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

        self.btn_export = QPushButton("Експорт ▼")
        export_menu = QMenu(self.btn_export)
        export_menu.addAction("в Excel (.xlsx)", self._export_excel)
        export_menu.addAction("в PDF (.pdf)", self._export_pdf)
        self.btn_export.setMenu(export_menu)
        filters.addWidget(self.btn_export)

        # 3. Таблиця з QSortFilterProxyModel
        self.model = ComputerTableModel()

        # Обгортка для сортування кліком по заголовку
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)  # Вмикаємо сортування в UI
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
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
            computer_type_id=self.f_type.currentData(),
            room_id=self.f_room.currentData(),
            date_from=self.f_date_from.date().toPyDate(),
            date_to=self.f_date_to.date().toPyDate(),
            # Сортуванням тепер керує ProxyModel, тому з бази віддаємо по замовчуванню
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
        # Важливо: мапимо індекс ProxyModel на оригінальний індекс SourceModel
        source_idx = self.proxy_model.mapToSource(idx)
        return self.model.get_object(source_idx.row())

    def _add(self):
        # Додаємо self.status_logs_repo перед parent=self
        dlg = ComputerDialog(self.repo, self.comp_types_repo.get_all(), self.workplaces_repo.get_all(), self.status_logs_repo, parent=self)
        if dlg.exec(): self.load_data()

    def _edit(self):
        obj = self._selected()
        if not obj:
            QMessageBox.information(self, "Увага", "Оберіть рядок для редагування")
            return
        # Додаємо self.status_logs_repo перед computer=obj
        dlg = ComputerDialog(self.repo, self.comp_types_repo.get_all(), self.workplaces_repo.get_all(), self.status_logs_repo, computer=obj, parent=self)
        if dlg.exec(): self.load_data()

    def _delete(self):
        obj = self._selected()
        if not obj: return
        reply = QMessageBox.question(self, "Видалення", f"Видалити комп'ютер «{obj.inventory_number}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete(obj)
                self.load_data()
            except IntegrityError:
                QMessageBox.critical(self, "Помилка", "Неможливо видалити: є пов'язані записи.")

    # ─── ЕКСПОРТ  ───

    def _prepare_export_data(self):
        """Готує дані з поточної моделі таблиці для експорту."""
        headers = [col[1] for col in ComputerTableModel.COLUMNS]
        data = []
        # Проходимося по всіх відфільтрованих рядках у ProxyModel
        for row in range(self.proxy_model.rowCount()):
            row_data = []
            for col in range(self.proxy_model.columnCount()):
                idx = self.proxy_model.index(row, col)
                # Беремо текст, який бачить користувач
                val = self.proxy_model.data(idx, Qt.ItemDataRole.DisplayRole)
                row_data.append(val)
            data.append(row_data)
        return headers, data

    def _export_excel(self):
        headers, data = self._prepare_export_data()
        if not data:
            QMessageBox.warning(self, "Помилка", "Немає даних для експорту!")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Зберегти Excel", "", "Excel Files (*.xlsx)")
        if filepath:
            try:
                Exporter.to_excel(filepath, headers, data, "Реєстр комп'ютерів")
                QMessageBox.information(self, "Успіх", "Файл успішно збережено!")
            except Exception as e:
                QMessageBox.critical(self, "Помилка експорту", str(e))

    def _export_pdf(self):
        headers, data = self._prepare_export_data()
        if not data:
            QMessageBox.warning(self, "Помилка", "Немає даних для експорту!")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Зберегти PDF", "", "PDF Files (*.pdf)")
        if filepath:
            try:
                Exporter.to_pdf(filepath, headers, data, "Реєстр комп'ютерів")
                QMessageBox.information(self, "Успіх", "Файл успішно збережено!")
            except Exception as e:
                QMessageBox.critical(self, "Помилка експорту", str(e))