from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QAbstractItemView, QWidget, QVBoxLayout, QLabel, QListWidgetItem

class ThumbListWidget(QListWidget):
    currentCountChanged = pyqtSignal()
    trigResort = pyqtSignal()

    """List Widget for holding Movable Items"""

    def __init__(self, type, parent=None):
        super(ThumbListWidget, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)

        self.maxItems = 9999

    # def addItems(self, items: list):
    #     for i, data in enumerate(sorted(items)):
    #         myQListWidgetItem = QCustomListWidgetItem(self)
    #         # store the data needed to create/re-create the custom widget
    #         myQListWidgetItem.setData(Qt.ItemDataRole.UserRole, (i, data))
    #         self.addItem(myQListWidgetItem)

    # def handleRowsOrdered(self, parent, first, last):
    #     for index in range(first, last + 1):
    #         item = self.item(index)
    #         if item is not None and self.itemWidget(item) is None:
    #             index, name = item.data(Qt.ItemDataRole.UserRole)
    #             widget = QCustomQWidget()
    #             widget.setTextUp(name)
    #             item.setSizeHint(widget.sizeHint())
    #             self.setItemWidget(item, widget)
    #
    #
    # def handleRowsInserted(self, parent, first, last):
    #     for index in range(first, last + 1):
    #         item = self.item(index)
    #
    #         if item is not None and self.itemWidget(item) is None:
    #             index, name = item.data(Qt.ItemDataRole.UserRole)
    #             widget = QCustomQWidget()
    #             widget.setTextUp(name)
    #             item.setSizeHint(widget.sizeHint())
    #             self.setItemWidget(item, widget)
    #             self.currentCountChanged.emit()

    def dropEvent(self, event):
        if self.count() == self.maxItems and event.source() != self:
            event.setDropAction(Qt.IgnoreAction)
        else:
            super().dropEvent(event)

    def getItems(self):
        return [self.item(x).text() for x in range(self.count())]


class QCustomListWidgetItem(QListWidgetItem):
    """Custom List widget item class"""

    def __init__(self, parent=None):
        super(QListWidgetItem, self).__init__(parent)

    def __gt__(self, other):
        return self.data(Qt.ItemDataRole.UserRole)[-1] > other.data(Qt.ItemDataRole.UserRole)[-1]  # or whatever

    def __lt__(self, other):
        return self.data(Qt.ItemDataRole.UserRole)[-1] < other.data(Qt.ItemDataRole.UserRole)[-1]  # or whatever


class QCustomQWidget(QWidget):
    """Custom List widget item class"""

    def __init__(self, parent=None):
        super(QCustomQWidget, self).__init__(parent)
        self.textQVBoxLayout = QVBoxLayout()
        self.textUpQLabel = QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.setLayout(self.textQVBoxLayout)

    def setTextUp(self, text):
        self.textUpQLabel.setText(text)

    def gettext(self):
        return self.textUpQLabel.text()
