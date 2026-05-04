from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)
from sqlalchemy.exc import IntegrityError

class SimpleTypeDialog(QDialog):
    """Універсальний діалог для створення/редагування сутностей з одним полем 'name'"""
    def __init__(self, repo, obj=None, entity_name="Запис", parent=None):
        super().__init__(parent)
        self.repo = repo
        self.obj = obj
        self.setWindowTitle(f"Редагування: {entity_name}" if obj else f"Новий: {entity_name}")
        self.setMinimumWidth(300)
        self._build_form()
        if obj:
            self._populate(obj)

    def _build_form(self):
        layout = QFormLayout(self)
        self.f_name = QLineEdit()
        layout.addRow("Назва *", self.f_name)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _populate(self, obj):
        self.f_name.setText(obj.name or "")

    def _save(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Поле 'Назва' є обов'язковим.")
            self.f_name.setFocus()
            return

        try:
            if self.obj:
                self.repo.update(self.obj, name=name)
            else:
                self.repo.create(name=name)
            self.accept()
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e.orig):
                QMessageBox.warning(self, "Помилка бази даних", "Така назва вже існує!")
                self.f_name.setFocus()
            else:
                QMessageBox.critical(self, "Помилка", str(e.orig))
        except Exception as e:
            QMessageBox.critical(self, "Помилка збереження", str(e))