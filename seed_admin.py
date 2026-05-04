import bcrypt
from app.database.database import SessionLocal
from app.database.models import User


def create_initial_admin():
    with SessionLocal() as session:
        # Перевіряємо, чи вже існує користувач admin
        admin_exists = session.query(User).filter(User.username == "admin").first()

        if admin_exists:
            print("Користувач 'admin' вже існує в базі даних.")
            return

        # Хешування пароля чистим bcrypt
        password = "admin123".encode('utf-8')
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        admin = User(
            username="admin",
            password_hash=hashed_pw,
            role="admin",
            full_name="Головний адміністратор"
        )

        session.add(admin)
        session.commit()
        print("✅ Адміністратора створено успішно!")
        print("Логін: admin")
        print("Пароль: admin123")


if __name__ == "__main__":
    create_initial_admin()