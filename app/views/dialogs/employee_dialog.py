from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)

class EmployeeDialog(QDialog):
    def __init__(self, repo, employee=None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.employee = employee
        self.setWindowTitle("Редагування співробітника" if employee else "Новий співробітник")
        self.setMinimumWidth(350)
        self._build_form()
        if employee:
            self._populate(employee)

    def _build_form(self):
        layout = QFormLayout(self)

        self.f_name = QLineEdit()
        self.f_position = QLineEdit()
        self.f_department = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_email = QLineEdit()

        layout.addRow("ПІБ *", self.f_name)
        layout.addRow("Посада", self.f_position)
        layout.addRow("Відділ", self.f_department)
        layout.addRow("Телефон", self.f_phone)
        layout.addRow("Email", self.f_email)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _populate(self, emp):
        self.f_name.setText(emp.full_name or "")
        self.f_position.setText(emp.position or "")
        self.f_department.setText(emp.department or "")
        self.f_phone.setText(emp.phone or "")
        self.f_email.setText(emp.email or "")

    def _save(self):
        full_name = self.f_name.text().strip()
        if not full_name:
            QMessageBox.warning(self, "Помилка", "ПІБ є обов'язковим полем.")
            self.f_name.setFocus()
            return

        data = {
            "full_name": full_name,
            "position": self.f_position.text().strip(),
            "department": self.f_department.text().strip(),
            "phone": self.f_phone.text().strip(),
            "email": self.f_email.text().strip(),
        }

        try:
            if self.employee:
                self.repo.update(self.employee, **data)
            else:
                self.repo.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Помилка збереження", str(e))