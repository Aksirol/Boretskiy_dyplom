from app.database.models import ComputerType, PeripheralType, Employee
from app.repositories.base import BaseRepository
from sqlalchemy import or_


class ComputerTypesRepository(BaseRepository[ComputerType]):
    def __init__(self, session_factory):
        super().__init__(session_factory, ComputerType)

    def search(self, query: str = "") -> list[ComputerType]:
        with self.session_factory() as session:
            q = session.query(ComputerType)
            if query:
                q = q.filter(ComputerType.name.ilike(f"%{query}%"))
            return q.order_by(ComputerType.name.asc()).all()


class PeripheralTypesRepository(BaseRepository[PeripheralType]):
    def __init__(self, session_factory):
        super().__init__(session_factory, PeripheralType)

    def search(self, query: str = "") -> list[PeripheralType]:
        with self.session_factory() as session:
            q = session.query(PeripheralType)
            if query:
                q = q.filter(PeripheralType.name.ilike(f"%{query}%"))
            return q.order_by(PeripheralType.name.asc()).all()

class EmployeesRepository(BaseRepository[Employee]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Employee)

    def search(self, query: str = "") -> list[Employee]:
        with self.session_factory() as session:
            q = session.query(Employee)
            if query:
                term = f"%{query}%"
                q = q.filter(or_(
                    Employee.full_name.ilike(term),
                    Employee.department.ilike(term),
                    Employee.position.ilike(term)
                ))
            return q.order_by(Employee.full_name.asc()).all()