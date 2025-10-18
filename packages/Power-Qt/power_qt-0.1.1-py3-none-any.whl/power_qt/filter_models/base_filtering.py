import sys

from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtWidgets import QWidget, QApplication, QListWidget

from power_qt.pandas_models.basic_table_models import BasicPandasTableModel


class FilterModel(QWidget):
    _proxy_Base = None
    _dynamic_filters = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_website = QListWidget()
        self.search_priority = QListWidget()
        self.search_name = QListWidget()

        self.createProxies(BasicPandasTableModel(),
                           [(0, self.search_website),
                            (2, self.search_priority),
                            (1, self.search_name)])

    def createProxies(self, model, filtering_widgets):
        """Filtering Widgets as a list of tuples containing (int, widget) pairs"""
        if len(filtering_widgets) > 25:
            raise AttributeError

        self._proxy_Base = model

        self._dynamic_filters.clear()

        for i, (filterColumn, connected_widget) in enumerate(filtering_widgets):
            proxy_name = f'_proxy_{chr(65 + i)}'
            print(proxy_name)

            setattr(self, proxy_name, QSortFilterProxyModel())
            proxy = getattr(self, proxy_name)

            self._dynamic_filters.append((proxy_name, connected_widget))

            proxy.setFilterKeyColumn(filterColumn)  # Search all columns.
            proxy.setSourceModel(getattr(self, '_proxy_Base'))

        self.FinalModel = getattr(self, self._dynamic_filters[-1][0])

    def apply_filter(self):
        for proxy, field in self._dynamic_filters:
            if not field.selectedItems():
                proxy.setFilterFixedString('')  # clearing filter if none is selected
            else:
                _search = '|'.join([item.text() for item in field.selectedItems()])
                proxy.setFilterRegularExpression(_search)  # applying filter


if __name__ == '__main__':

    app_main = QApplication(sys.argv)  # load main window
    win = FilterModel()
    win.show()

    try:
        sys.exit(app_main.exec())
    except SystemExit:
        print('Closing Window...')
