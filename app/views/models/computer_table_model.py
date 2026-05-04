from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex


class ComputerTableModel(QAbstractTableModel):
    COLUMNS = [
        ("inventory_number", "Інв. номер"),
        ("brand", "Виробник"),
        ("model", "Модель"),
        ("processor", "Процесор"),
        ("ram_gb", "RAM (ГБ)"),
        ("storage_gb", "Диск (ГБ)"),
        ("os", "ОС"),
        ("ip_address", "IP-адреса"),
        ("status", "Статус"),
        ("purchase_date", "Дата закупівлі"),
    ]

    def __init__(self):
        super().__init__()
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        obj = self._items[index.row()]

        # Для сортування (EditRole) і відображення (DisplayRole) віддаємо оригінальні типи
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            attr = self.COLUMNS[index.column()][0]
            val = getattr(obj, attr, None)

            if attr == "status":
                return {"active": "Активний", "repair": "Ремонт",
                        "decommissioned": "Списаний", "storage": "На зберіганні"}.get(val, val)

            # Якщо значення відсутнє, повертаємо порожній рядок (щоб уникнути помилок сортування)
            if val is None:
                return ""

            return val  # Повертаємо як є (int, date, str). PyQt сам розбереться!

        if role == Qt.ItemDataRole.UserRole:
            return obj

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section][1]
        return None

    def refresh(self, items: list) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def get_object(self, row: int):
        return self._items[row]