import pandas as pd
import polars as pl
import polars.selectors as cs
from PyQt6.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt6.QtGui import QColor
import seaborn

__all__ = ['BasicPolarsTableModel', 'BasicPandasTableModel']


class BaseTableModelFunction(QAbstractTableModel):
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


class BasicPolarsTableModel(BaseTableModelFunction):
    """
    Custom class to populate a QTableview with a pandas dataframe
    """

    def __init__(self,
                 data=None,
                 styler=None,
                 parent=None,
                 alignment=None,
                 style_on_cell: int = None,
                 *args,
                 **kwargs):

        QAbstractTableModel.__init__(self, parent)

        self.original_data = data
        self._alignment = alignment
        self._styler = styler
        self._style_on_cell = style_on_cell

    @property
    def original_data(self):
        return self._original_data

    @original_data.setter
    def original_data(self, value):
        self._original_data = value if value is not None else pl.DataFrame()
        self._original_data = self._original_data.with_columns((~cs.string()).cast(pl.String))
        self._data = self._original_data

        self._col_width = self._original_data.with_columns(pl.all().str.len_bytes().max().mul(5))

        self._RowCount = self._original_data.height
        self._ColCount = self._original_data.width

        self.v_index = range(self._RowCount)
        self.h_index = self._original_data.columns

    def getData(self):
        """Returns the private data variable with any edits that were made"""
        return self._data

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                self._data[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def rowCount(self, parent=None):
        return self._RowCount

    def columnCount(self, parent=None):
        return self._ColCount

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            value = self._data[index.row(), index.column()]

            if self._styler is not None:
                col_lookup = index.column() if self._style_on_cell is None else self._style_on_cell

                color_data = self._data[index.row(), col_lookup]

                if role == Qt.ItemDataRole.BackgroundRole or role == Qt.ItemDataRole.ForegroundRole:
                    return QColor(self._styler(color_data,
                                               role=role,
                                               colname=self.h_index[col_lookup],
                                               fullcol=self._data.row(index.row())))

            if role == Qt.ItemDataRole.DisplayRole:
                return str(value)

            if role == Qt.ItemDataRole.TextAlignmentRole and self._alignment is not None:
                return self._alignment

        return QVariant()

    def headerData(self, index, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.h_index[index])

            if orientation == Qt.Orientation.Vertical:
                return str(self.v_index[index])

        return QVariant()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled


class BasicPandasTableModel(BaseTableModelFunction):
    """
    Custom class to populate a QTableview with a pandas dataframe
    """

    def __init__(self,
                 data=None,
                 styler=None,
                 parent=None,
                 alignment=None,
                 style_on_cell: int = None,
                 *args,
                 **kwargs):

        QAbstractTableModel.__init__(self, parent)

        self.original_data = data
        self._alignment = alignment
        self._styler = styler
        self._style_on_cell = style_on_cell

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

    def autoColWidth(self):
        widths = []
        for i, col in enumerate(self._data.columns):
            max_char = max(max([len(str(x)) for x in self._data[col].values]), len(col))

            widths.append((i, max_char * 8))

        return widths

    def getData(self):
        """Returns the private data variable with any edits that were made"""
        return self._data

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                self._data.iat[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def rowCount(self, parent=None):
        return self._RowCount

    def columnCount(self, parent=None):
        return self._ColCount

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if index.isValid():
            value = self._data.iat[index.row(), index.column()]

            if self._styler is not None:
                col_lookup = index.column() if self._style_on_cell is None else self._style_on_cell

                color_data = self._data.iat[index.row(), col_lookup]

                if role == Qt.ItemDataRole.BackgroundRole or role == Qt.ItemDataRole.ForegroundRole:
                    return QColor(self._styler(color_data,
                                               role=role,
                                               colname=self.h_index[col_lookup],
                                               fullcol=self._data.iloc[index.row()]))

            else:
                if role == Qt.ItemDataRole.BackgroundRole:
                    return QColor('#FFFFFF')

                if role == Qt.ItemDataRole.ForegroundRole:
                    return QColor('#000000')

            if role == Qt.ItemDataRole.DisplayRole:
                return str(value)

            if role == Qt.ItemDataRole.TextAlignmentRole and self._alignment is not None:
                return self._alignment

        return QVariant()

    def headerData(self, index, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.h_index[index])

            if orientation == Qt.Orientation.Vertical:
                return str(self.v_index[index])

        return QVariant()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
