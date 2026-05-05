from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox,
    QTabWidget, QWidget, QVBoxLayout, QTableView, QHeaderView
)
from PyQt6.QtCore import QDate
from sqlalchemy.exc import IntegrityError
from app.services.auth import session_manager
from app.views.models.generic_table_model import GenericTableModel


# 🌟 ДОДАНО: Клас-обгортка для підготовки даних перед відображенням у таблиці
class LogWrapper:
    def __init__(self, log):
        # Форматуємо дату в зручний формат
        self.date_str = log.changed_at.strftime("%d.%m.%Y %H:%M") if log.changed_at else ""

        # Словник для перекладу системних статусів на зрозумілі слова
        status_map = {
            "active": "Активний",
            "repair": "Ремонт",
            "decommissioned": "Списаний",
            "storage": "На зберіганні",
            "—": "—"
        }

        self.old_st_str = status_map.get(log.old_status, log.old_status)
        self.new_st_str = status_map.get(log.new_status, log.new_status)

        # Витягуємо ім'я користувача або ставимо заглушку
        self.user_name = log.user.full_name if getattr(log, 'user', None) else "Система"


class ComputerDialog(QDialog):
    def __init__(self, repo, computer_types, workplaces, status_logs_repo=None, computer=None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.computer_types = computer_types
        self.workplaces = workplaces
        self.status_logs_repo = status_logs_repo
        self.computer = computer

        self.setWindowTitle("Редагування комп'ютера" if computer else "Новий комп'ютер")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        self._build_ui()
        if computer:
            self._populate(computer)
            self._load_logs()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # --- ВКЛАДКА 1: Основні дані ---
        self.tab_form = QWidget()
        layout = QFormLayout(self.tab_form)

        self.f_inventory = QLineEdit()
        self.f_type = QComboBox()
        for ct in self.computer_types: self.f_type.addItem(ct.name, ct.id)

        self.f_workplace = QComboBox()
        self.f_workplace.addItem("— На складі (не закріплено) —", None)
        for wp in self.workplaces:
            room_info = f" ({wp.room.name})" if wp.room else ""
            self.f_workplace.addItem(f"{wp.name}{room_info}", wp.id)

        self.f_brand = QLineEdit()
        self.f_model = QLineEdit()
        self.f_processor = QLineEdit()
        self.f_ram = QSpinBox()
        self.f_ram.setRange(1, 512)
        self.f_ram.setSuffix(" ГБ")
        self.f_storage = QSpinBox()
        self.f_storage.setRange(1, 10000)
        self.f_storage.setSuffix(" ГБ")
        self.f_storage_type = QComboBox()
        self.f_storage_type.addItems(["SSD", "HDD", "NVMe", "Інше"])
        self.f_os = QLineEdit()
        self.f_ip = QLineEdit()
        self.f_ip.setPlaceholderText("192.168.1.1")
        self.f_mac = QLineEdit()
        self.f_mac.setPlaceholderText("AA:BB:CC:DD:EE:FF")
        self.f_date = QDateEdit(calendarPopup=True)
        self.f_date.setDate(QDate.currentDate())

        self.f_status = QComboBox()
        for val, label in [("active", "Активний"), ("repair", "Ремонт"),
                           ("decommissioned", "Списаний"), ("storage", "На зберіганні")]:
            self.f_status.addItem(label, val)
        self.f_notes = QTextEdit()
        self.f_notes.setFixedHeight(60)

        layout.addRow("Інв. номер *", self.f_inventory)
        layout.addRow("Тип ПК *", self.f_type)
        layout.addRow("Робоче місце", self.f_workplace)
        layout.addRow("Виробник", self.f_brand)
        layout.addRow("Модель", self.f_model)
        layout.addRow("Процесор", self.f_processor)
        layout.addRow("RAM", self.f_ram)
        layout.addRow("Об'єм диску", self.f_storage)
        layout.addRow("Тип диску", self.f_storage_type)
        layout.addRow("ОС", self.f_os)
        layout.addRow("IP-адреса", self.f_ip)
        layout.addRow("MAC-адреса", self.f_mac)
        layout.addRow("Дата закупівлі", self.f_date)
        layout.addRow("Статус", self.f_status)
        layout.addRow("Примітки", self.f_notes)

        self.tabs.addTab(self.tab_form, "Основні дані")

        # --- ВКЛАДКА 2: Історія змін ---
        self.tab_logs = QWidget()
        logs_layout = QVBoxLayout(self.tab_logs)
        cols = [("date_str", "Дата"), ("old_st_str", "Було"), ("new_st_str", "Стало"), ("user_name", "Користувач")]
        self.logs_model = GenericTableModel(cols)
        self.logs_table = QTableView()
        self.logs_table.setModel(self.logs_model)
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        logs_layout.addWidget(self.logs_table)
        self.tabs.addTab(self.tab_logs, "Історія змін")

        if not self.computer: self.tabs.setTabEnabled(1, False)

        main_layout.addWidget(self.tabs)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def _load_logs(self):
        # 🌟 ЗМІНЕНО: Використовуємо обгортку LogWrapper перед передачею даних у таблицю
        if self.status_logs_repo and self.computer:
            logs = self.status_logs_repo.get_by_device("computer", self.computer.id)
            wrapped_logs = [LogWrapper(log) for log in logs]
            self.logs_model.refresh(wrapped_logs)

    def _populate(self, c):
        self.f_inventory.setText(c.inventory_number or "")

        idx = self.f_type.findData(c.computer_type_id)
        if idx >= 0: self.f_type.setCurrentIndex(idx)

        w_idx = self.f_workplace.findData(c.workplace_id)
        if w_idx >= 0: self.f_workplace.setCurrentIndex(w_idx)

        self.f_brand.setText(c.brand or "")
        self.f_model.setText(c.model or "")
        self.f_processor.setText(c.processor or "")
        self.f_ram.setValue(c.ram_gb or 8)
        self.f_storage.setValue(c.storage_gb or 256)
        self.f_storage_type.setCurrentText(c.storage_type or "SSD")
        self.f_os.setText(c.os or "")
        self.f_ip.setText(c.ip_address or "")
        self.f_mac.setText(c.mac_address or "")

        if c.purchase_date:
            self.f_date.setDate(QDate(c.purchase_date.year, c.purchase_date.month, c.purchase_date.day))

        status_idx = self.f_status.findData(c.status)
        if status_idx >= 0: self.f_status.setCurrentIndex(status_idx)
        self.f_notes.setPlainText(c.notes or "")

    def _validate(self) -> bool:
        if not self.f_inventory.text().strip():
            QMessageBox.warning(self, "Валідація", "Інвентарний номер є обов'язковим")
            self.f_inventory.setFocus()
            return False
        return True

    def _collect(self) -> dict:
        return {
            "inventory_number": self.f_inventory.text().strip(),
            "computer_type_id": self.f_type.currentData(),
            "workplace_id": self.f_workplace.currentData(),
            "brand": self.f_brand.text().strip(),
            "model": self.f_model.text().strip(),
            "processor": self.f_processor.text().strip(),
            "ram_gb": self.f_ram.value(),
            "storage_gb": self.f_storage.value(),
            "storage_type": self.f_storage_type.currentText(),
            "os": self.f_os.text().strip(),
            "ip_address": self.f_ip.text().strip(),
            "mac_address": self.f_mac.text().strip(),
            "purchase_date": self.f_date.date().toPyDate(),
            "status": self.f_status.currentData(),
            "notes": self.f_notes.toPlainText().strip(),
        }

    def _save(self):
        if not self._validate(): return

        old_status = self.computer.status if self.computer else "—"
        new_status = self.f_status.currentData()
        data = self._collect()

        try:
            if self.computer:
                self.repo.update(self.computer, **data)
                comp_id = self.computer.id
            else:
                new_comp = self.repo.create(**data)
                comp_id = new_comp.id

            if old_status != new_status and self.status_logs_repo:
                user = session_manager.get_user()
                self.status_logs_repo.create(
                    device_type="computer",
                    device_id=comp_id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=user.id if user else 1,
                    comment="Зміна статусу через картку пристрою."
                )
            self.accept()
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e.orig):
                QMessageBox.warning(self, "Помилка", "ПК з таким інвентарним номером вже існує!")
                self.f_inventory.setFocus()
            else:
                QMessageBox.critical(self, "Помилка БД", str(e.orig))