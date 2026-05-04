from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QDialogButtonBox, QMessageBox

class RoomDialog(QDialog):
    def __init__(self, repo, room=None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.room = room
        self.setWindowTitle("Редагування приміщення" if room else "Нове приміщення")
        self.setMinimumWidth(350)
        self._build_form()
        if room:
            self._populate(room)

    def _build_form(self):
        layout = QFormLayout(self)
        self.f_name = QLineEdit()
        self.f_number = QLineEdit()
        self.f_floor = QSpinBox(); self.f_floor.setRange(-5, 100)
        self.f_building = QLineEdit()
        self.f_desc = QTextEdit(); self.f_desc.setFixedHeight(60)

        layout.addRow("Назва *", self.f_name)
        layout.addRow("Номер кабінету", self.f_number)
        layout.addRow("Поверх", self.f_floor)
        layout.addRow("Корпус", self.f_building)
        layout.addRow("Опис", self.f_desc)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _populate(self, r):
        self.f_name.setText(r.name or "")
        self.f_number.setText(r.number or "")
        self.f_floor.setValue(r.floor or 1)
        self.f_building.setText(r.building or "")
        self.f_desc.setPlainText(r.description or "")

    def _save(self):
        if not self.f_name.text().strip():
            QMessageBox.warning(self, "Помилка", "Назва приміщення є обов'язковою.")
            return

        data = {
            "name": self.f_name.text().strip(),
            "number": self.f_number.text().strip(),
            "floor": self.f_floor.value(),
            "building": self.f_building.text().strip(),
            "description": self.f_desc.toPlainText().strip()
        }

        try:
            if self.room: self.repo.update(self.room, **data)
            else: self.repo.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))