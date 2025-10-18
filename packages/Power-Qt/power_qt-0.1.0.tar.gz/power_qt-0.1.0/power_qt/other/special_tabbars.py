from PyQt6 import QtWidgets, QtGui
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QTabBar, QTabWidget, QMenu

from power_qt.other.default_fields import DefaultFieldsWidget

__all__ = ['StylizedTabWidget']


class _TabBar(QTabBar):
    colorCodes = {}

    def paintEvent(self, event):
        style = self.style()
        painter = QtGui.QPainter(self)
        option = QtWidgets.QStyleOptionTab()
        for index in range(self.count()):
            self.initStyleOption(option, index)

            bgcolor = QtGui.QColor(self.colorCodes.get(self.tabText(index), '#FFFFFF'))

            option.palette.setColor(QtGui.QPalette.ColorRole.Window, bgcolor)
            option.palette.setColor(QtGui.QPalette.ColorRole.Button, bgcolor)
            style.drawControl(QtWidgets.QStyle.ControlElement.CE_TabBarTab, option, painter)


class StylizedTabWidget(QTabWidget):
    icons = {}

    def __init__(self, parent=None):
        super(StylizedTabWidget, self).__init__(parent)
        self.setTabBar(_TabBar(self))

        self.context_menu = QMenu(self)
        action1 = self.context_menu.addAction('Customize Tabs')
        action1.triggered.connect(self.showEditor)

        attributes = {'Icons': StylizedTabWidget.icons,
                      'Colors': _TabBar.colorCodes}

        self.editor = DefaultFieldsWidget(self)
        self.editor.setWindowTitle('Name')
        self.editor.add_pages(attributes)

    def _set_default_dictionary(self, new_obj):
        StylizedTabWidget.icons.update(new_obj.get('Icons', {}))
        _TabBar.colorCodes.update(new_obj.get('Colors', {}))

    def showEditor(self):
        self.editor.show()

    def contextMenuEvent(self, a0):
        self.context_menu.exec(a0.globalPos())

    def addTab(self, widget, text):
        QTabWidget.addTab(self, widget, text)

    def setTabText(self, index, text):
        QTabWidget.setTabText(self, index, text)

        tab_icon = self.icons.get(text)

        if tab_icon is not None:
            self.setTabIcon(index, QIcon(QPixmap(str(tab_icon))))

    def refresh_tabs(self):
        for i in range(self.count()):
            pass

    def modIcons(self, tabText=None, icon_path=None, ):
        _TabBar.colorCodes = _TabBar.colorCodes | {tabText: icon_path}

    def modColors(self, tabText=None, color=None):
        _TabBar.colorCodes = _TabBar.colorCodes | {tabText: color}
