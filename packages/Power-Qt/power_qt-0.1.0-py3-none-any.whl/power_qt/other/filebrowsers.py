from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QFileDialog


class FileBrowser(QWidget):
    start_dir = None
    filter = None

    class modes:
        SingleFile = 0
        MultiFile = 1
        Directory = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout()

        self.setLayout(self.layout)

        self.browseButton = QPushButton("Browse")
        self.browsedFiles = QLineEdit()

        self.layout.addWidget(self.browseButton)
        self.layout.addWidget(self.browsedFiles)

        self._saveDialog = QFileDialog()

    def savePaths(self):
        return self.browsedFiles.text()

    def setMode(self, mode: modes):
        if mode == self.modes.SingleFile:
            self.browseButton.clicked.connect(self._browser_pointer_file)

        elif mode == self.modes.MultiFile:
            self.browseButton.clicked.connect(self._browser_pointer_multifile)

        elif mode == self.modes.Directory:
            self.browseButton.clicked.connect(self._browser_pointer_folder)

        else:
            self.browseButton.clicked.connect(self._browser_pointer_file)

    def setFileBrowserSettings(self, filter_string=None,
                               start_dir=None):

        self.filter = filter_string
        self.start_dir = start_dir

    def _browser_pointer_file(self):
        filenames, filters = self._saveDialog.getOpenFileName(caption="Select File",
                                                              filter=self.filter,
                                                              directory=self.start_dir)
        self.browsedFiles.setText(filenames)

    def _browser_pointer_multifile(self):
        filenames, filters = self._saveDialog.getOpenFileNames(caption="Select File/s",
                                                               filter=self.filter,
                                                               directory=self.start_dir)
        self.browsedFiles.setText(' | '.join(filenames))

    def _browser_pointer_folder(self):
        filenames = self._saveDialog.getExistingDirectory(caption="Select Folder")
        self.browsedFiles.setText(filenames)
