from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QAbstractItemView, QWidget, QLabel, QListWidgetItem, \
    QDoubleSpinBox, QHBoxLayout


class DragDropListWidget(QListWidget):
    currentCountChanged = pyqtSignal()
    trigResort = pyqtSignal()

    """Generic List Widget for holding Movable Items"""

    def __init__(self, parent=None):
        super(QListWidget, self).__init__(parent)
        # self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # self.setAcceptDrops(True)
        self.model().rowsInserted.connect(self.handleRowsInserted, Qt.ConnectionType.QueuedConnection)
        self.model().rowsRemoved.connect(self.handleRowsInserted)

        self.maxItems = 9999

    def baseItemWidget(self, widget):
        self._item_widget = widget

    def addItems(self, items: list[tuple]):
        for i, data in enumerate(sorted(items)):
            myQListWidgetItem = QListWidgetItem(self)
            # store the data needed to create/re-create the custom widget
            myQListWidgetItem.setData(Qt.ItemDataRole.UserRole, (i, data))
            self.addItem(myQListWidgetItem)

    def handleRowsInserted(self, parent, first, last):
        for index in range(first, last + 1):
            item = self.item(index)
            widget = QCustomSpin()

            widget.setNew(item)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)
            item.setText('')

    def dropEvent(self, event):
        if self.count() == self.maxItems and event.source() != self:
            event.setDropAction(Qt.DropAction.IgnoreAction)
        else:
            super().dropEvent(event)

    def getItems(self, role: int | None = None):
        return [self.itemWidget(self.item(x)).data(role) for x in range(self.count())]


class GenericItemWidget(QWidget):
    def __init__(self, parent=None):
        super(GenericItemWidget, self).__init__(parent)
        self.user_role = None
        self.display_role = None
        self.edit_role = None

        self.FullLayout = QHBoxLayout()
        self.setLayout(self.FullLayout)

    def setNew(self, item: QListWidgetItem, *args):
        self.display_role = item.data(Qt.ItemDataRole.DisplayRole)

        self.edit_role = item.data(Qt.ItemDataRole.EditRole)

        self.user_role = item.data(Qt.ItemDataRole.UserRole)

        label = QLabel(self.display_role)
        self.FullLayout.addWidget(label)

    def data(self, role, *args, **kwargs):
        return {Qt.ItemDataRole.DisplayRole: self.display_role,
                Qt.ItemDataRole.EditRole: self.edit_role,
                Qt.ItemDataRole.UserRole: self.user_role}

class QCustomSpin(GenericItemWidget):
    """Custom List widget item class"""

    def __init__(self, parent=None):
        super(QCustomSpin, self).__init__(parent)

    def setNew(self, item: QListWidgetItem, *args):
        super().setNew(item)

        self.spin = QDoubleSpinBox()
        self.spin.setSingleStep(0.01)
        self.spin.setValue(1)
        self.layout().addWidget(self.spin)

    def data(self, role, *args, **kwargs):
        return {self.display_role: self.spin.value()}
