import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTreeView, QVBoxLayout, QTabWidget, QStackedWidget, QDialog

from power_qt.json_editor.data_tree import DataTreeWidget
from power_qt.other.json_models import QJsonTreeItem, QJsonModel


class QDefaultFieldsModel(QJsonModel):

    def __init__(self, parent=None, edit_columns=None):
        super(QDefaultFieldsModel, self).__init__(parent)

        self.editable_cols = [1]  # edit_columns

        self._rootItem = QJsonTreeItem()
        self._headers = ("key", "value")


    def json(self, root=None):
        """Serialise model as JSON-compliant dictionary

        Arguments:
            root (QJsonTreeItem, optional): Serialise from here
                defaults to the top-level item

        Returns:
            model as dict

        """
        root = root or self._rootItem
        return {self.objectName(): self.genJson(root)}  # modification to return from tabs

    def get_data(self):
        return self.json()

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


class DefaultFieldsWidget(QDialog):
    _isnested = False
    _models_cache = []
    _path = None
    _path_loaded_json = None
    attributeUpdated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._lay = QVBoxLayout(self)

        self._tab_block = QTabWidget(self)

        self._lay.addWidget(self._tab_block)
        self.setLayout(self._lay)

        self.resize(600, 1000)
        try:
            self.attributeUpdated.connect(self.save_json)
            self.attributeUpdated.connect(self.parent()._set_default_dictionary)
        except AttributeError:
            pass

        if parent is not None:
            self.setWindowTitle(str(parent))

    @property
    def path(self):

        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        try:
            with open(self._path, "r+") as fp:
                self._path_loaded_json = json.load(fp)
        except FileNotFoundError:
            self._path_loaded_json = dict()

    def add_pages(self, new_col_dict):

        if self._path_loaded_json:
            trg_dict = self._path_loaded_json
        else:
            trg_dict = new_col_dict

        self.__clearModels()

        self._isnested = self.isNested(trg_dict)

        if self._isnested:
            for tabname, dictionary in trg_dict.items():
                self._createModel(tabname, dictionary)
        else:
            self._createModel('Dictionary', trg_dict)

    def _createModel(self, name: str, _adict: dict):
        _model = QDefaultFieldsModel()
        _model.load(_adict)
        _model.setObjectName(name)

        _view = QTreeView(self._tab_block)
        _view.setModel(_model)
        _view.setObjectName(name)
        _view.expandAll()

        self._models_cache.append(_model)
        # _view.expandRecursively()
        _view.resizeColumnToContents(0)
        _view.resizeColumnToContents(1)
        _model.dataChanged.connect(self.updatedDictionary)

        self._tab_block.addTab(_view, name)

    def __clearModels(self):
        for tab in range(self._tab_block.count()):
            self._tab_block.removeTab(tab)

        for widget in self._tab_block.findChildren(QTreeView):
            widget.deleteLater()

    def updatedDictionary(self):
        if self._isnested:
            result = {}
            for model in self._models_cache:
                result.update(model.get_data())

        else:
            result = self._models_cache[0].get_data()

        self.attributeUpdated.emit(result)

    def getmyDict(self):
        trees = self._tab_block.findChildren(QStackedWidget)[0].findChildren(QTreeView)
        self._tab_block.objectName()
        d = {}

        for tree in trees:
            d[tree.objectName()] = tree.model().json()

        return d

    @staticmethod
    def isNested(_myDict: dict):
        return any(isinstance(i, dict) for i in _myDict.values())

    def save_json(self, data_from_ui):
        try:
            with open(self._path, "w+") as fp:
                json.dump(data_from_ui, fp)
            print("Saved Json to: {}".format(self._path))
        except:
            pass


class DefaultPropertiesWidget(DefaultFieldsWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

    def _createModel(self, name: str, _adict: dict):
        _view = DataTreeWidget(self._tab_block)
        _view.set_data(_adict)
        _view.setObjectName(name)

        _view.tree_widget.model().dataChanged.connect(self.updatedDictionary)

        self._models_cache.append(_view)

        self._tab_block.addTab(_view, name)
