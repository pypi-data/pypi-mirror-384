import pandas as pd
import seaborn
from PyQt6.QtCore import QAbstractListModel, QModelIndex
from PyQt6.QtCore import Qt, QVariant
from PyQt6.QtGui import QColor

__all__ = ['PandasListModel_roles', 'PandasListModel']


class PandasListModel_roles(QAbstractListModel):

    def __init__(self,
                 data: pd.DataFrame,
                 target_column=0,
                 styler=None,
                 parent=None,
                 align=None,
                 style_on_cell=False,
                 *args,
                 **kwargs):

        super().__init__(parent)

        self._data = data
        self.target_column = target_column
        self.len_data = len(data)

        self.detect_flag = Qt.ItemDataRole.UserRole + 1
        self.fraction = Qt.ItemDataRole.UserRole + 2

    def data(self, index: QModelIndex, role: int = ...):
        row = index.row()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._data.iat[row, self.target_column]
        if role == Qt.ItemDataRole.BackgroundRole:
            return "#ff5468"
        if role == self.detect_flag:
            return self._data.iat[row, 0]

        if role == self.fraction:
            return self._data.iat[row, 1]

    def roleNames(self):
        return {Qt.ItemDataRole.UserRole + 1: b'detect_flag',
                Qt.ItemDataRole.UserRole + 2: b'fraction'}

    def rowCount(self, parent=QModelIndex()):
        r = len(self._data)
        return r


class PandasListModel(QAbstractListModel):
    """Custom class to populate a QTableview with a pandas dataframe"""

    _alignment = Qt.AlignmentFlag.AlignLeft
    _styler = None
    _original_data: pd.DataFrame = None
    _style_on_cell = None

    _data = None
    _col_width = None
    _RowCount = 0
    _ColCount = 0
    target_column = 0

    h_index = None
    v_index = None

    palette_list = seaborn.color_palette(None, 20).as_hex()
    palette_dict = dict()

    customRoles = {}

    def __init__(self,
                 data: pd.DataFrame = None,
                 target_column: int | str = 0,
                 styler=None,
                 parent=None,
                 alignment=None,
                 *args,
                 **kwargs):

        QAbstractListModel.__init__(self, parent)

        self.original_data = data
        self._alignment = alignment
        self._styler = styler

        self.target_column = target_column

    @property
    def original_data(self):
        return self._original_data

    @original_data.setter
    def original_data(self, value):
        self._original_data = value if value is not None else pd.DataFrame()
        self._data = self._original_data

        self._RowCount, self._ColCount = self._original_data.shape

        self.v_index = self._original_data.index
        self.h_index = self._original_data.columns
        self._col_width = self._original_data.map(lambda x: len(str(x)), na_action='ignore').max(axis=0).to_list()

    def setNewData(self,
                   data,
                   *args,
                   **kwargs):
        """Sets new internal data variable and refreshes model"""

        self._alignment = kwargs.get('align', Qt.AlignmentFlag.AlignLeft)

        self._styler = kwargs.get('styler', None)

        self._style_on_cell = kwargs.get('style_on_cell', False)

        self.target_column = kwargs.get('target_column', 0)

        self.original_data = data

        self.layoutChanged.emit()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if index.isValid() and self._data is not None:

            value = self._data.iat[index.row(), self.target_column]

            if self._styler is not None:
                if role == Qt.ItemDataRole.BackgroundRole:
                    return QColor(self._styler(value, role))

                elif role == Qt.ItemDataRole.ForegroundRole:
                    return QColor(self._styler(value, role))

            if role == Qt.ItemDataRole.DisplayRole:
                return str(value)

            if role == Qt.ItemDataRole.EditRole:
                return str(value)

            if role == Qt.ItemDataRole.UserRole:
                return str(value)

            if role == Qt.ItemDataRole.TextAlignmentRole and self._alignment is not None:
                return QVariant(self._alignment)

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                self._data.iat[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def rowCount(self, parent=QModelIndex()):
        return self._RowCount

    def columnCount(self, parent=None):
        return self._ColCount

    def headerData(self, index, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (orientation == Qt.Orientation.Horizontal
                and role == Qt.ItemDataRole.DisplayRole):
            return QVariant(str(self.h_index[index]))

        if (orientation == Qt.Orientation.Vertical
                and role == Qt.ItemDataRole.DisplayRole):
            return QVariant(str(self.v_index[index]))

        return QVariant()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled

    def getData(self) -> pd.Series:
        """Retrieve data as series"""
        return self._data[self.target_column]
