import sys
from PyQt6.QtWidgets import (QApplication, QComboBox, QWidget, QVBoxLayout, QStyledItemDelegate, QAbstractItemView, QListView)
from PyQt6.QtCore import QModelIndex, Qt

class CustomDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.isValid():
            painter.save()
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft, f"Name: {index.data(Qt.ItemDataRole.DisplayRole)}, Value: {index.data(Qt.ItemDataRole.UserRole)}")
            painter.restore()

class CustomView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(CustomDelegate(self))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.combo = QComboBox(self)
        self.combo.setView(CustomView(self.combo))

        layout = QVBoxLayout(self)
        layout.addWidget(self.combo)

        self.add_items()

    def add_items(self):
        data = [("Item 1", 10), ("Item 2", 20), ("Item 3", 30)]
        for name, value in data:
            self.combo.addItem(name, value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())