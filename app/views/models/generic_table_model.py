from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

class GenericTableModel(QAbstractTableModel):
    def __init__(self, columns: list[tuple[str, str]]):
        super().__init__()
        # columns - це список кортежів: [("назва_атрибута_в_ORM", "Назва колонки в UI")]
        self.COLUMNS = columns
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        obj = self._items[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            attr = self.COLUMNS[index.column()][0]
            val = getattr(obj, attr, None)
            return str(val) if val is not None else "—"

        if role == Qt.ItemDataRole.UserRole:
            return obj

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.COLUMNS[section][1]
        return None

    def refresh(self, items: list) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def get_object(self, row: int):
        return self._items[row]