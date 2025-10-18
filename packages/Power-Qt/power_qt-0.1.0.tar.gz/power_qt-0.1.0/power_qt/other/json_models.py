import re
import typing

from PyQt6 import QtCore
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtGui import QColor
from matplotlib import colors


class QJsonTreeItem(object):
    def __init__(self, parent=None):
        self._parent = parent

        self._key = ""
        self._value = ""
        self._type = None
        self._children = list()

    def appendChild(self, item):
        self._children.append(item)

    def child(self, row):
        return self._children[row]

    def parent(self):
        return self._parent

    def childCount(self):
        return len(self._children)

    def row(self):
        return (
            self._parent._children.index(self)
            if self._parent else 0
        )

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, typ):
        self._type = typ

    @classmethod
    def load(self, value, parent=None, sort=True):

        rootItem = QJsonTreeItem(parent)
        rootItem.key = "root"

        if isinstance(value, dict):
            items = (
                sorted(value.items())
                if sort else value.items()
            )

            for key, value in items:
                child = self.load(value, rootItem)
                child.key = key
                child.type = type(value)
                rootItem.appendChild(child)

        elif isinstance(value, list):
            for index, value in enumerate(value):
                child = self.load(value, rootItem)
                child.key = index
                child.type = type(value)
                rootItem.appendChild(child)

        else:
            rootItem.value = value
            rootItem.type = type(value)

        return rootItem


class QJsonModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None, edit_columns=None):
        super(QJsonModel, self).__init__(parent)

        self.editable_cols = edit_columns

        self._rootItem = QJsonTreeItem()
        self._headers = ("key", "value")

    def clear(self):
        self.load({})

    def load(self, document):
        """Load from dictionary

        Arguments:
            document (dict): JSON-compatible dictionary

        """

        assert isinstance(document, (dict, list, tuple)), (
                "`document` must be of dict, list or tuple, "
                "not %s" % type(document)
        )

        self._data = document
        self.beginResetModel()

        self._rootItem = QJsonTreeItem.load(document)
        self._rootItem.type = type(document)

        self.endResetModel()

        return True

    def json(self, root=None):
        """Serialise model as JSON-compliant dictionary

        Arguments:
            root (QJsonTreeItem, optional): Serialise from here
                defaults to the the top-level item

        Returns:
            model as dict

        """
        root = root or self._rootItem
        return self.genJson(root)

    def getLevel(self, parent_item):
        complete = False
        i = 0

        while not complete:
            if parent_item == None:
                return i
            else:
                i += 1

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return item.key

            if index.column() == 1:
                return item.value

        if role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                return item.value

        if role == Qt.ItemDataRole.BackgroundRole and index.column() == 1:
            if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', str(item.value)):
                return QColor(item.value)

        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 1:
            if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', str(item.value)):
                return QColor(self.ContrastColor(item.value))

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                item = index.internalPointer()
                item.value = str(value)

                self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.EditRole])

                return True

        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        elif orientation == Qt.Orientation.Horizontal:
            return self._headers[section]

        else:
            return

    def index(self, row, column, parent=QtCore.QModelIndex()):

        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:

            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def flags(self, index):
        flags = super(QJsonModel, self).flags(index)

        if index.column() in self.editable_cols:
            return Qt.ItemFlag.ItemIsEditable | flags
        else:
            return flags

    def genJson(self, item):
        nchild = item.childCount()

        if item.type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                document[ch.key] = self.genJson(ch)
            return document

        elif item.type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.genJson(ch))
            return document

        else:
            return item.value

    def ContrastColor(self, hexColor):
        R, G, B = colors.hex2color(hexColor)

        luminance = (0.299 * R + 0.587 * G + 0.114 * B)

        if (luminance > 0.5):
            d = 0  # // bright colors - black font
        else:
            d = 1  # // dark colors - white font

        return colors.rgb2hex((d, d, d))