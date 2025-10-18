import pandas as pd
import polars as pl
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QTableView, QAbstractItemView, QApplication

from power_qt.item_delegates.basic_delegates import SelectedHighlighter
from power_qt.pandas_models.basic_table_models import BasicPolarsTableModel, BasicPandasTableModel


class reTableView(QTableView):
    """

    Custom Qt Tableview widget for converting Pandas dataframes into
    GUI viewable tables, uses Pandasmodel_Deux by default. Can be updated using setmodel

    """
    _model = None

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)  # Inherit from QWidget
        self.horizontalHeader().setStyleSheet("QHeaderView::section {background-color:#acacac; font-weight: bold;}")
        self.verticalHeader().setStyleSheet("QHeaderView::section {background-color:#acacac; font-weight: bold;}")

        self.toggle_editing(False)
        self._pandas_model = BasicPandasTableModel()
        self._polars_model = BasicPolarsTableModel()

        self._model = self._pandas_model
        self.__current_model_type = 'Pandas'

        self.setModel(self._model)
        self.setItemDelegate(delegate=SelectedHighlighter(self._model))

    def _check_dataframe(self, dataframe: pl.DataFrame | pd.DataFrame):
        if isinstance(dataframe, pl.DataFrame) and self.__current_model_type != 'Polars':
            self.setModel(self._polars_model)
            self._model = self._polars_model
            self.__current_model_type = 'Polars'

        elif isinstance(dataframe, pd.DataFrame) and self.__current_model_type != 'Pandas':
            self.setModel(self._pandas_model)
            self._model = self._pandas_model
            self.__current_model_type = 'Pandas'

        else:
            pass

    def updateModelData(self, dataframe: pd.DataFrame | pl.DataFrame, *args, **kwargs):

        self._check_dataframe(dataframe)

        self.model().beginResetModel()
        self.model().setNewData(dataframe, *args, **kwargs)
        self.model().endResetModel()

    def update_table(self, dataframe: pd.DataFrame | pl.DataFrame, *args, **kwargs):
        self.updateModelData(dataframe, *args, **kwargs)

    def setModel(self, model) -> None:
        super(reTableView, self).setModel(model)

    def setItemDelegate(self, delegate) -> None:
        super(reTableView, self).setItemDelegate(delegate)

    def toggle_editing(self, _bool: bool, custom_=None):
        "Toggles editing to double-click-to-edit"
        if custom_ is not None:
            self.setEditTriggers(custom_)
        else:
            if _bool:
                self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
            else:
                self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def expanding(self, model=None):
        if model is not None:
            m = model.autoColWidth()
        else:
            m = self.model().autoColWidth()

        for index, width in m:
            self.setColumnWidth(index, width)

    def adjust_columns(self, _all=None, column_indicies=None):
        for index, (width, col_name) in enumerate(zip(self.model()._col_width, self.model()._columns)):
            self.setColumnWidth(index, int(max(int(width), int(len(col_name))) * 5))

    def index(self, row, columns, parent=None, *args, **kwargs):
        return self.model().index(row, columns, parent)

    def keyPressEvent(self, event):
        clipboard = QApplication.clipboard()

        if event.matches(QKeySequence.StandardKey.Copy):  # copy
            selectedRows = [r.row() for r in self.selectionModel().selectedIndexes()]
            selectedColumns = [c.column() for c in self.selectionModel().selectedIndexes()]

            s = ''

            for r in range(min(selectedRows), max(selectedRows) + 1):

                # s += self.table.verticalHeaderItem(c).text() + '\t'
                for c in range(min(selectedColumns), max(selectedColumns) + 1):
                    print(r, c)
                    try:
                        s += str(self.model().index(r, c).data(Qt.ItemDataRole.DisplayRole)) + "\t"
                    except AttributeError:
                        s += "\t"

                s = s[:-1] + "\n"  # eliminate last '\t'

            clipboard.setText(s)
            # QTableView.keyPressEvent(self, event)

