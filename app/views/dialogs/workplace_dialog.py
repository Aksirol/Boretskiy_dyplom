from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QDialogButtonBox, QMessageBox


class WorkplaceDialog(QDialog):
    def __init__(self, repo, rooms, employees, workplace=None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.workplace = workplace
        self.setWindowTitle("Редагування робочого місця" if workplace else "Нове робоче місце")
        self.setMinimumWidth(350)

        self.rooms = rooms
        self.employees = employees

        self._build_form()
        if workplace:
            self._populate(workplace)

    def _build_form(self):
        layout = QFormLayout(self)
        self.f_name = QLineEdit()

        self.f_room = QComboBox()
        for r in self.rooms:
            self.f_room.addItem(f"{r.name} (Корпус: {r.building}, Пов: {r.floor})", r.id)

        self.f_employee = QComboBox()
        self.f_employee.addItem("— Не закріплено —", None)
        for e in self.employees:
            self.f_employee.addItem(f"{e.full_name} ({e.position})", e.id)

        self.f_desc = QTextEdit();
        self.f_desc.setFixedHeight(60)

        layout.addRow("Назва РМ *", self.f_name)
        layout.addRow("Приміщення *", self.f_room)
        layout.addRow("Співробітник", self.f_employee)
        layout.addRow("Опис", self.f_desc)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _populate(self, w):
        self.f_name.setText(w.name or "")
        self.f_desc.setPlainText(w.description or "")

        r_idx = self.f_room.findData(w.room_id)
        if r_idx >= 0: self.f_room.setCurrentIndex(r_idx)

        e_idx = self.f_employee.findData(w.employee_id)
        if e_idx >= 0: self.f_employee.setCurrentIndex(e_idx)

    def _save(self):
        if not self.f_name.text().strip():
            QMessageBox.warning(self, "Помилка", "Назва робочого місця є обов'язковою.")
            return

        data = {
            "name": self.f_name.text().strip(),
            "room_id": self.f_room.currentData(),
            "employee_id": self.f_employee.currentData(),
            "description": self.f_desc.toPlainText().strip()
        }

        try:
            if self.workplace:
                self.repo.update(self.workplace, **data)
            else:
                self.repo.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))