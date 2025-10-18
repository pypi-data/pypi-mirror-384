import logging

from PyQt6.QtCore import pyqtSlot,Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QAbstractItemView, QPushButton, QVBoxLayout, QLabel, QHBoxLayout

logger = logging.getLogger('__main__')


# future version, create ui file for widget

class TwoListSelection(QWidget):
    """
    Custom two list selection widget, facilitates moving of items
    from left to right lists and vice versa

    """

    def __init__(self, parent=None):
        super(TwoListSelection, self).__init__(parent)

    def setup_layout(self, priority=False, myListWidget=None):
        lay = QHBoxLayout(self)
        self.mInput = myListWidget()
        self.mInput.setObjectName('Selected')

        self.mOuput = myListWidget()
        self.mOuput.setObjectName('Available')

        self.mInput.setSelectionMode(QAbstractItemView.SelectionMode(2))
        self.mOuput.setSelectionMode(QAbstractItemView.SelectionMode(2))

        self.mButtonToSelected = QPushButton(">>")
        self.mBtnMoveToAvailable = QPushButton(">")
        self.mBtnMoveToSelected = QPushButton("<")
        self.mButtonToAvailable = QPushButton("<<")

        vlay = QVBoxLayout()
        vlay.addStretch()
        vlay.addWidget(self.mButtonToSelected)
        vlay.addWidget(self.mBtnMoveToAvailable)
        vlay.addWidget(self.mBtnMoveToSelected)
        vlay.addWidget(self.mButtonToAvailable)
        vlay.addStretch()

        self.mBtnUp = QPushButton("Up")
        self.mBtnDown = QPushButton("Down")

        vlay2 = QVBoxLayout()
        vlay2.addStretch()
        vlay2.addWidget(self.mBtnUp)
        vlay2.addWidget(self.mBtnDown)
        vlay2.addStretch()

        vlay_available = QVBoxLayout()
        label_avail = QLabel()
        label_avail.setText('Available Items')
        label_avail.setFont(QFont('Helvetica', 12))

        vlay_available.addWidget(label_avail)
        vlay_available.addWidget(self.mInput)

        vlay_selected = QVBoxLayout()
        self.label_sel = QLabel()
        self.label_sel.setText('Selected Items')
        self.label_sel.setFont(QFont('Helvetica', 12))

        vlay_selected.addWidget(self.label_sel)
        vlay_selected.addWidget(self.mOuput)

        lay.addLayout(vlay_available)
        lay.addLayout(vlay)
        lay.addLayout(vlay_selected)

        if priority:
            lay.addLayout(vlay2)

        self.update_buttons_status()
        self.connections()

    @pyqtSlot()
    def update_buttons_status(self):

        if self.sender() is not None:
            sender_name = self.sender().objectName()
        else:
            sender_name = ''

        self.mBtnUp.setDisabled(not bool(self.mOuput.selectedItems()) or self.mOuput.currentRow() == 0)
        self.mBtnDown.setDisabled(not bool(self.mOuput.selectedItems()) or self.mOuput.currentRow() == (self.mOuput.count() - 1))
        self.mBtnMoveToAvailable.setDisabled(not bool(self.mInput.selectedItems()) or self.mOuput.currentRow() == 0)
        self.mBtnMoveToSelected.setDisabled(not bool(self.mOuput.selectedItems()))

        if sender_name == 'Selected' and self.mOuput.currentItem() is not None:
            self.mOuput.blockSignals(True)
            self.mOuput.selectionModel().clear()
            self.mOuput.blockSignals(False)

        if sender_name == 'Available' and self.mInput.currentItem() is not None:
            self.mInput.blockSignals(True)
            self.mInput.selectionModel().clear()
            self.mInput.blockSignals(False)

    def connections(self):
        self.mInput.itemSelectionChanged.connect(self.update_buttons_status)
        self.mOuput.itemSelectionChanged.connect(self.update_buttons_status)
        self.mBtnMoveToAvailable.clicked.connect(self.on_mBtnMoveToAvailable_clicked)
        self.mBtnMoveToSelected.clicked.connect(self.on_mBtnMoveToSelected_clicked)
        self.mButtonToAvailable.clicked.connect(self.on_mButtonToAvailable_clicked)
        self.mButtonToSelected.clicked.connect(self.on_mButtonToSelected_clicked)
        self.mBtnUp.clicked.connect(self.on_mBtnUp_clicked)
        self.mBtnDown.clicked.connect(self.on_mBtnDown_clicked)

    @pyqtSlot()
    def on_mBtnMoveToAvailable_clicked(self):
        self.mOuput.blockSignals(True)
        self.mInput.blockSignals(True)

        self.mOuput.addItem(self.mInput.takeItem(self.mInput.currentRow()))

        self.mOuput.blockSignals(False)
        self.mInput.blockSignals(False)

    @pyqtSlot()
    def on_mBtnMoveToSelected_clicked(self):
        self.mOuput.blockSignals(True)
        self.mInput.blockSignals(True)
        self.mInput.addItem(self.mOuput.takeItem(self.mOuput.currentRow()))
        self.mOuput.blockSignals(False)
        self.mInput.blockSignals(False)

    @pyqtSlot()
    def on_mButtonToAvailable_clicked(self):
        self.mOuput.blockSignals(True)
        self.mInput.blockSignals(True)
        while self.mOuput.count() > 0:
            self.mInput.addItem(self.mOuput.takeItem(0))
        self.mOuput.blockSignals(False)
        self.mInput.blockSignals(False)

    @pyqtSlot()
    def on_mButtonToSelected_clicked(self):
        self.mOuput.blockSignals(True)
        self.mInput.blockSignals(True)
        while self.mInput.count() > 0:
            self.mOuput.addItem(self.mInput.takeItem(0))
        self.mOuput.blockSignals(False)
        self.mInput.blockSignals(False)

    @pyqtSlot()
    def on_mBtnUp_clicked(self):
        row = self.mOuput.currentRow()
        currentItem = self.mOuput.takeItem(row)
        self.mOuput.insertItem(row - 1, currentItem)
        self.mOuput.setCurrentRow(row - 1)

    @pyqtSlot()
    def on_mBtnDown_clicked(self):
        row = self.mOuput.currentRow()
        currentItem = self.mOuput.takeItem(row)
        self.mOuput.insertItem(row + 1, currentItem)
        self.mOuput.setCurrentRow(row + 1)

    def addAvailableItems(self, items):
        self.mInput.addItems(items)

        self.mInput.setSortingEnabled(True)
        self.mOuput.setSortingEnabled(True)

    def get_left_elements(self):
        r = []
        for i in range(self.mInput.count()):
            it = self.mInput.item(i)
            r.append(it.text())
        return r

    def get_right_elements(self):
        r = []
        for i in range(self.mOuput.count()):
            it = self.mOuput.item(i)
            r.append(it.text())
        return r

    def changeSelectionMode(self, selection_mode: int):
        self.mInput.setSelectionMode(QAbstractItemView.SelectionMode(selection_mode))
        self.mOuput.setSelectionMode(QAbstractItemView.SelectionMode(selection_mode))

    def getCurrentItems(self):
        selected = self.mOuput.selectedItems() + self.mInput.selectedItems()
        return selected

    def getSingleSelected(self, role = Qt.ItemDataRole.DisplayRole):
        selected = self.mOuput.selectedItems() + self.mInput.selectedItems()

        return selected[0].data(role)
