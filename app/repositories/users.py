from app.database.models import User
from app.repositories.base import BaseRepository

class UsersRepository(BaseRepository[User]):
    def __init__(self, session_factory):
        super().__init__(session_factory, User)

    def get_by_username(self, username: str) -> User | None:
        """Повертає користувача за логіном або None, якщо такого немає."""
        with self.session_factory() as session:
            return session.query(User).filter(User.username == username).first()