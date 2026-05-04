from sqlalchemy.orm import joinedload
from app.database.models import StatusLog, User
from app.repositories.base import BaseRepository


class StatusLogsRepository(BaseRepository[StatusLog]):
    def __init__(self, session_factory):
        super().__init__(session_factory, StatusLog)

    def _format_logs(self, logs: list[StatusLog]) -> list[StatusLog]:
        """Додає зручні текстові атрибути для відображення в таблиці."""
        status_map = {
            "active": "Активний", "repair": "Ремонт",
            "decommissioned": "Списаний", "storage": "На зберіганні", "—": "—"
        }
        for log in logs:
            log.user_name = log.user.full_name if log.user else "Невідомо"
            log.date_str = log.changed_at.strftime("%Y-%m-%d %H:%M") if log.changed_at else "—"
            log.device_name = "Комп'ютер" if log.device_type == "computer" else "Периферія"
            log.old_st_str = status_map.get(log.old_status, log.old_status)
            log.new_st_str = status_map.get(log.new_status, log.new_status)
        return logs

    def get_by_device(self, device_type: str, device_id: int) -> list[StatusLog]:
        with self.session_factory() as session:
            logs = session.query(StatusLog).options(joinedload(StatusLog.user)) \
                .filter(StatusLog.device_type == device_type, StatusLog.device_id == device_id) \
                .order_by(StatusLog.changed_at.desc()).all()
            return self._format_logs(logs)

    def get_recent(self, limit: int = 100, device_type=None, user_id=None, date_from=None, date_to=None) -> list[
        StatusLog]:
        with self.session_factory() as session:
            q = session.query(StatusLog).options(joinedload(StatusLog.user))

            if device_type: q = q.filter(StatusLog.device_type == device_type)
            if user_id: q = q.filter(StatusLog.changed_by == user_id)
            if date_from: q = q.filter(StatusLog.changed_at >= date_from)
            if date_to: q = q.filter(StatusLog.changed_at <= date_to)

            logs = q.order_by(StatusLog.changed_at.desc()).limit(limit).all()
            return self._format_logs(logs)