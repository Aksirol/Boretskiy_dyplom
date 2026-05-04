from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import QDate, Qt
from sqlalchemy.exc import IntegrityError


class PeripheralDialog(QDialog):
    def __init__(self, repo, peripheral_types, workplaces, peripheral=None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.peripheral_types = peripheral_types
        self.workplaces = workplaces
        self.peripheral = peripheral
        self.setWindowTitle("Редагування периферії" if peripheral else "Нова периферія")
        self.setMinimumWidth(400)
        self._build_form()
        if peripheral:
            self._populate(peripheral)

    def _build_form(self):
        layout = QFormLayout(self)

        self.f_inventory = QLineEdit()
        self.f_type = QComboBox()
        for pt in self.peripheral_types:
            self.f_type.addItem(pt.name, pt.id)

        # Розумний ComboBox із пошуком
        self.f_workplace = QComboBox()
        self.f_workplace.setEditable(True)
        self.f_workplace.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Забороняємо додавати нові
        # Налаштовуємо пошук по частині слова (не тільки з початку)
        self.f_workplace.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        self.f_workplace.addItem("— На складі (не закріплено) —", None)
        for wp in self.workplaces:
            room_info = f" ({wp.room.name})" if wp.room else ""
            self.f_workplace.addItem(f"{wp.name}{room_info}", wp.id)

        self.f_brand = QLineEdit()
        self.f_model = QLineEdit()
        self.f_serial = QLineEdit()

        self.f_date = QDateEdit(calendarPopup=True)
        self.f_date.setDate(QDate.currentDate())

        self.f_status = QComboBox()
        for val, label in [("active", "Активний"), ("repair", "Ремонт"),
                           ("decommissioned", "Списаний"), ("storage", "На зберіганні")]:
            self.f_status.addItem(label, val)

        self.f_notes = QTextEdit();
        self.f_notes.setFixedHeight(60)

        layout.addRow("Інв. номер *", self.f_inventory)
        layout.addRow("Тип *", self.f_type)
        layout.addRow("Робоче місце", self.f_workplace)
        layout.addRow("Виробник", self.f_brand)
        layout.addRow("Модель", self.f_model)
        layout.addRow("Серійний номер", self.f_serial)
        layout.addRow("Дата закупівлі", self.f_date)
        layout.addRow("Статус", self.f_status)
        layout.addRow("Примітки", self.f_notes)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _populate(self, p):
        self.f_inventory.setText(p.inventory_number or "")

        idx = self.f_type.findData(p.peripheral_type_id)
        if idx >= 0: self.f_type.setCurrentIndex(idx)

        w_idx = self.f_workplace.findData(p.workplace_id)
        if w_idx >= 0: self.f_workplace.setCurrentIndex(w_idx)

        self.f_brand.setText(p.brand or "")
        self.f_model.setText(p.model or "")
        self.f_serial.setText(p.serial_number or "")

        if p.purchase_date:
            self.f_date.setDate(QDate(p.purchase_date.year, p.purchase_date.month, p.purchase_date.day))

        status_idx = self.f_status.findData(p.status)
        if status_idx >= 0: self.f_status.setCurrentIndex(status_idx)
        self.f_notes.setPlainText(p.notes or "")

    def _validate(self) -> bool:
        if not self.f_inventory.text().strip():
            QMessageBox.warning(self, "Валідація", "Інвентарний номер є обов'язковим")
            self.f_inventory.setFocus()
            return False

        # Перевіряємо, чи користувач не ввів неіснуюче робоче місце в ComboBox
        if self.f_workplace.currentData() is None and self.f_workplace.currentIndex() != 0:
            QMessageBox.warning(self, "Валідація", "Оберіть робоче місце зі списку або залишіть 'На складі'")
            return False

        return True

    def _collect(self) -> dict:
        return {
            "inventory_number": self.f_inventory.text().strip(),
            "peripheral_type_id": self.f_type.currentData(),
            "workplace_id": self.f_workplace.currentData(),
            "brand": self.f_brand.text().strip(),
            "model": self.f_model.text().strip(),
            "serial_number": self.f_serial.text().strip(),
            "purchase_date": self.f_date.date().toPyDate(),
            "status": self.f_status.currentData(),
            "notes": self.f_notes.toPlainText().strip(),
        }

    def _save(self):
        if not self._validate(): return
        data = self._collect()

        if self.peripheral and self.peripheral.status != data["status"]:
            print(f"[STUB] Аудит-журнал: статус периферії {data['inventory_number']} змінено на {data['status']}.")

        try:
            if self.peripheral:
                self.repo.update(self.peripheral, **data)
            else:
                self.repo.create(**data)
            self.accept()
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e.orig):
                QMessageBox.warning(self, "Помилка", "Обладнання з таким інвентарним номером вже існує!")
                self.f_inventory.setFocus()
            else:
                QMessageBox.critical(self, "Помилка БД", str(e.orig))
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))