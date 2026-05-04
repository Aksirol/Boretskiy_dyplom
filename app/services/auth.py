import bcrypt
from functools import wraps
from app.database.models import User


class SessionManager:
    """Singleton для збереження поточного користувача в пам'яті процесу."""
    _instance = None
    current_user: User | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def login(self, user: User):
        self.current_user = user

    def logout(self):
        self.current_user = None

    def get_user(self) -> User | None:
        return self.current_user


# Глобальний екземпляр сесії користувача
session_manager = SessionManager()


class AuthService:
    def __init__(self, users_repo):
        self.users_repo = users_repo

    def authenticate(self, username: str, password: str) -> bool:
        """Перевіряє логін і пароль. У разі успіху зберігає користувача в сесії."""
        user = self.users_repo.get_by_username(username)

        if user:
            # Перевірка пароля чистим bcrypt
            # bcrypt.checkpw вимагає байти, тому конвертуємо обидва рядки
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                user.password_hash.encode('utf-8')
            )

            if is_valid:
                session_manager.login(user)
                return True

        return False


def require_role(required_role: str):
    """Декоратор для блокування методів/дій без потрібних прав."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = session_manager.get_user()
            if not user:
                raise PermissionError("Користувач не авторизований.")
            if required_role == "admin" and user.role != "admin":
                raise PermissionError("Ця дія доступна лише адміністраторам.")
            return func(*args, **kwargs)

        return wrapper

    return decorator