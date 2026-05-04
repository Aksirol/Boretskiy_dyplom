from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt


class LoginWindow(QDialog):
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("Вхід у систему")
        self.setFixedSize(300, 160)

        # Вимикаємо кнопку [?] в заголовку вікна
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Форма для логіну та пароля
        form_layout = QFormLayout()
        self.f_username = QLineEdit()
        self.f_username.setPlaceholderText("Введіть логін")

        self.f_password = QLineEdit()
        self.f_password.setPlaceholderText("Введіть пароль")
        self.f_password.setEchoMode(QLineEdit.EchoMode.Password)  # Ховаємо пароль зірочками

        form_layout.addRow("Логін:", self.f_username)
        form_layout.addRow("Пароль:", self.f_password)
        layout.addLayout(form_layout)

        # Поле для відображення помилки (спочатку порожнє)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        # Кнопка входу
        self.btn_login = QPushButton("Увійти")
        self.btn_login.clicked.connect(self._handle_login)
        self.btn_login.setDefault(True)  # Реагуватиме на клавішу Enter
        layout.addWidget(self.btn_login)

    def _handle_login(self):
        username = self.f_username.text().strip()
        password = self.f_password.text().strip()

        if not username or not password:
            self.error_label.setText("Заповніть всі поля!")
            return

        # Звертаємося до сервісу для перевірки
        if self.auth_service.authenticate(username, password):
            self.accept()  # Закриваємо вікно з позитивним результатом
        else:
            self.error_label.setText("Невірний логін або пароль")
            self.f_password.clear()
            self.f_password.setFocus()