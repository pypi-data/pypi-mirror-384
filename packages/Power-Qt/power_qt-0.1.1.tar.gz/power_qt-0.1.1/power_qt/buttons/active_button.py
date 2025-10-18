from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QPushButton, QMenu
from typing import Annotated

from dataclasses import dataclass
from power_qt.json_editor.json_editor_ui import JsonEditorWidget
__all__ = ['ActiveButton']

from power_qt.other import DefaultFieldsWidget, TempTest


@dataclass
class _button_parameters:
    _original_text: str
    _inprogress_text: str
    _cancelled_text: str
    _error_text: str
    _completed_text: str


button_typing = Annotated[str, _button_parameters('original', 'inprogress', 'cancelled', 'error', 'completed')]


class PropertyContextMenu:
    _properties: dict = {}
    __menu_activated = False

    def setupMenu(self):
        self.context_menu = QMenu(self)
        action1 = self.context_menu.addAction('Customize Tabs')
        action1.triggered.connect(self.showEditor)

        self.editor = DefaultFieldsWidget(self)
        self.editor2 = TempTest(self)
        self.editor.setWindowTitle('Name')
        self.editor.add_pages(self._properties)
        self.__menu_activated = True

    def _set_default_dictionary(self, new_obj):
        self._properties.update(new_obj)

    def contextMenuEvent(self, a0):
        if self.__menu_activated:
            self.context_menu.exec(a0.globalPos())

    def showEditor(self):
        self.editor2.show()


class ActiveButton(QPushButton, PropertyContextMenu):
    """Qt PushButton with messaging responses"""

    _properties = {'Button Text': {'original': '',
                                   'inprogress': 'Running',
                                   'cancelled': 'Operation cancelled',
                                   'error': 'Error Encountered!',
                                   'completed': 'Operation Completed'},
                   'Button Coloring': {'background-color': {'original': '#83fff9',
                                                            'inprogress': '#ceff83',
                                                            'cancelled': '#ffe883',
                                                            'error': '#ff0000',
                                                            'completed': '#83ff87'},
                                       'color': {'original': '#000000',
                                                 'inprogress': '#000000',
                                                 'cancelled': '#000000',
                                                 'error': '#000000',
                                                 'completed': '#000000'}
                                       }}

    def assignStylesheet(self, code):
        bkg_color = self._properties['Button Coloring']['background-color'][code]
        fgd_color = self._properties['Button Coloring']['color'][code]

        self.setStyleSheet('QPushButton {background-color:%s; color:%s}' % (bkg_color, fgd_color))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.reset)

        self.setupMenu()

    def setText(self, text):
        super().setText(text)
        self._properties['Button Text']['original'] = text
        self.assignStylesheet('original')

    def running(self):
        super().setText(self._properties['Button Text']['inprogress'])
        self.assignStylesheet('inprogress')
        self.setEnabled(False)

    def cancelled(self):
        super().setText(self._properties['Button Text']['cancelled'])
        self.assignStylesheet('cancelled')
        self.__timer.start(5000)
        self.setEnabled(True)

    def errored(self, *args, **kwargs):
        super().setText(self._properties['Button Text']['error'])
        self.assignStylesheet('error')
        self.setEnabled(True)

    def finished(self):
        super().setText(self._properties['Button Text']['completed'])
        self.assignStylesheet('completed')
        self.__timer.start(5000)
        self.setEnabled(True)

    def reset(self):
        super().setText(self._properties['Button Text']['original'])
        self.assignStylesheet('original')
        self.__timer.stop()

    def setTextLabels(self, target: button_typing):
        """Sets """
        pass
