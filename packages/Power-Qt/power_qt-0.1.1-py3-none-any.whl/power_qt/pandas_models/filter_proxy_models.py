import logging

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel

logger = logging.getLogger('__main__')

from PyQt6.QtCore import Qt

__all__ = ['myCustomQsort']


class myCustomQsort(QSortFilterProxyModel):
    cache = set()

    def __init__(self, parent=None):
        super().__init__(parent)

    def clearCache(self):
        self.cache = set()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:

        value = self.sourceModel().index(source_row, 0, source_parent)

        inCache = value.data(Qt.ItemDataRole.DisplayRole) in self.cache
        matched = self.filterRegularExpression().match(value.data(self.filterRole())).hasMatch()
        if not inCache and matched:
            self.cache.add(str(value.data(Qt.ItemDataRole.DisplayRole)))
            return True
        else:
            return False
