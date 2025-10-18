from PyQt6.QtCore import QPointF
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTransform, QPainter
from PyQt6.QtWidgets import QTableWidget, QApplication, QTableWidgetItem, QVBoxLayout
from PyQt6.QtWidgets import QWidget
from superqt import QSearchableListWidget, QDoubleRangeSlider, QSearchableComboBox

class SearchableCombo(QSearchableComboBox):
    def __init__(self, parent=None):
        QSearchableComboBox.__init__(self, parent)  # Inherit from QWidget


class SearchableList(QSearchableListWidget):
    def __init__(self, parent=None):
        QSearchableListWidget.__init__(self, parent)  # Inherit from QWidget


class Rangeslider(QDoubleRangeSlider):
    def __init__(self, parent=None):
        QDoubleRangeSlider.__init__(self, parent)  # Inherit from QWidget


class PasteableTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            selection = self.selectedIndexes()

            if selection:
                row_anchor = selection[0].row()
                column_anchor = selection[0].column()

                clipboard = QApplication.clipboard()

                rows = clipboard.text().split('\n')
                for indx_row, row in enumerate(rows):
                    values = row.split('\t')
                    for indx_col, value in enumerate(values):
                        item = QTableWidgetItem(value)
                        self.setItem(row_anchor + indx_row, column_anchor + indx_col, item)
            super().keyPressEvent(event)


class DynamicWidget(QWidget):
    """Widget for dynamic GUI widget updating"""

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def update_display_widget(self, widget):
        if self.layout.itemAt(0) is not None:
            self.layout.itemAt(0).widget().setParent(None)
        self.layout.addWidget(widget)

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None

    def setImage(self, image):
        self._image = image
        self.update()

    def paintEvent(self, event):
        if self._image is None or self._image.isNull():
            return
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        imageWidth = self._image.width()
        imageHeight = self._image.height()
        r1 = width / imageWidth
        r2 = height / imageHeight
        r = min(r1, r2)
        x = (width - imageWidth * r) / 2
        y = (height - imageHeight * r) / 2
        painter.setTransform(QTransform().translate(x, y).scale(r, r))
        painter.drawImage(QPointF(0, 0), self._image)
