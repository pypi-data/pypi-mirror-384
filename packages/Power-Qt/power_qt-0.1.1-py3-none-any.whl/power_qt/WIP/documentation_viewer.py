from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow
from _Utilities import Core, parseTree
from widgets.docs_window import Ui_help_window


class DocumentationView(QMainWindow, Ui_help_window):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        home_icon = QIcon(str(Core.assets / 'fugue-icons-3.5.6' / 'icons' / 'home.png'))
        redo_icon = QIcon(str(Core.assets / 'fugue-icons-3.5.6' / 'icons' / 'arrow.png'))
        undo_icon = QIcon(str(Core.assets / 'fugue-icons-3.5.6' / 'icons' / 'arrow-180.png'))
        printer_icon = QIcon(str(Core.assets / 'fugue-icons-3.5.6' / 'icons' / 'printer.png'))

        self.undo.setIcon(undo_icon)
        self.Home.setIcon(home_icon)
        self.redo.setIcon(redo_icon)
        self.compile_HTML.setIcon(printer_icon)

        myDocBrowser = QWebEngineView()
        myDocBrowser.load(QUrl.fromLocalFile(str(Core.docs / 'directory.html')))

        self.main_bar.addWidget(myDocBrowser)

        self.undo.clicked.connect(myDocBrowser.back)
        self.redo.clicked.connect(myDocBrowser.forward)
        self.Home.clicked.connect(lambda: myDocBrowser.load(QUrl.fromLocalFile(str(Core.docs / 'directory.html'))))
        self.compile_HTML.clicked.connect(self.combine_docs)
