import logging
import pathlib

from collections.abc import Callable
import pandas as pd
from PyQt6.QtCore import pyqtSignal, QThread, QTimer, QObject
from PyQt6.QtWidgets import QFileDialog, QApplication, QToolButton

from power_qt.buttons.active_button import ActiveButton
from power_qt.other.default_fields import DefaultFieldsWidget
from abc import ABC, abstractmethod

logger = logging.getLogger('__main__')
App = QApplication([])


class masterBaseClass(ABC):
    # import guicanvas & guitable

    _module_sources = []

    @abstractmethod
    def ConfigChanged(self, newname) -> None:
        """Target function for performing refresh of widget data when base data changes"""
        return any([name in self._module_sources for name in newname])

    @abstractmethod
    def start(self) -> None:
        """Generic startup function, perform all data modifications for widget here only"""
        pass

    def _set_default_dictionary(self, new_obj: dict):
        """Generic function for setting a class' default fields"""
        pass

    def create_editor(self, path, addable_dictionary: dict, window_name='Properties'):
        s_path = pathlib.Path(path)
        parent1 = s_path.parents[1].name
        parent2 = s_path.parents[0].name

        t_path = Core.cache / parent1 / parent2 / f'{s_path.stem}.json'

        t_path.parent.mkdir(parents=True, exist_ok=True)

        self.editor = DefaultFieldsWidget(self)
        self.editor.setWindowTitle(window_name)
        self.editor._path = t_path
        self.editor.add_pages(addable_dictionary)

    def edit_styles(self):
        self.editor.show()


class HelperBase():
    _return_signal = pyqtSignal(tuple())
    _timer = QTimer()
    _saveDialog = QFileDialog()
    __thread = None

    def addToolButton(self):
        self.toolb = QToolButton()
        self.layout().addWidget(self.toolb)

    def save_file(self,
                  target: Callable[[any], any],
                  target_kwargs: dict = None,
                  dialog_kwargs: dict = None,
                  *args,
                  **kwargs):
        """
                Helper function for moving a save process into a side thread while saving.

                For filename destinations only.

                target == callable(savepath, *args, **kwargs)

                returns to _thread_run_return
                """
        if dialog_kwargs is None:
            dialog_kwargs = {'filter': 'Excel File (*.xlsx)'}

        sender = self.sender()

        savedialog = self._saveDialog.getSaveFileName

        self.__save_helper(sender, target, savedialog, target_kwargs, dialog_kwargs, *args, **kwargs)

    def save_folder(self,
                    target: Callable[[any], any],
                    target_kwargs: dict = None,
                    dialog_kwargs: dict = None,
                    *args,
                    **kwargs):
        """
                Helper function for moving a save process into a side thread while saving.

                For folderpath destinations only.

                target == callable(folderpath, *args, **kwargs)

                returns to _thread_run_return
                """

        sender = self.sender()
        savedialog = self._saveDialog.getExistingDirectory

        self.__save_helper(sender, target, savedialog, target_kwargs, dialog_kwargs, *args, **kwargs)

    def __save_helper(self,
                      sender: QObject,
                      target: Callable[[any], any],
                      savedialog,
                      target_kwargs: dict = None,
                      dialog_kwargs: dict = None,
                      *args,
                      **kwargs):

        """Private method for assembling thread and savedialog from save_file and save_folder"""

        if dialog_kwargs is None:
            dialog_kwargs = dict()

        if target_kwargs is None:
            target_kwargs = dict()

        def_dialog_kwargs = {'directory': '',
                             'caption': 'Save File'}

        dialog_kwargs = def_dialog_kwargs | dialog_kwargs

        savepath = savedialog(parent=None, **dialog_kwargs)

        savepath = savepath[0] if isinstance(savepath, tuple) else savepath

        if savepath == '' and isinstance(sender, ActiveButton):
            sender.cancelled()
            return

        self.__create_saving_thread(sender, target, (savepath,), target_kwargs)

    def __create_saving_thread(self, sender_obj, target, savepath, target_kwargs):
        self.myThread = MasterThread(target, target_args=savepath, target_kwargs=target_kwargs)

        self.myThread.finished.connect(lambda returnable: self._thread_run_return(returnable))
        self.myThread.errored.connect(lambda returnable: self._thread_run_return(returnable))

        if isinstance(sender_obj, ActiveButton):
            self.myThread.started.connect(sender_obj.running)
            self.myThread.errored.connect(sender_obj.errored)
            self.myThread.finished.connect(sender_obj.finished)

        self.myThread.start()

    def threaded_run(self,
                     target=None,
                     target_args: tuple | list = None,
                     target_kwargs: dict = None):

        button = self.sender()

        if target_args is None:
            target_args = tuple()

        if target_kwargs is None:
            target_kwargs = dict()

        self.__thread = MasterThread(target=target,
                                     target_args=target_args,
                                     target_kwargs=target_kwargs)

        self.__thread.finished.connect(self._thread_run_return)
        self.__thread.errored.connect(self._thread_error_return)

        if isinstance(button, ActiveButton):
            self.__thread.started.connect(button.running)
            self.__thread.errored.connect(button.errored)
            self.__thread.finished.connect(button.finished)

        self.__thread.start()

    def _thread_run_return(self, *args, **kwargs):
        pass

    def _thread_error_return(self, *args, **kwargs):
        logger.exception(args[0])


class MasterThread(QThread):
    finished = pyqtSignal(tuple)
    errored = pyqtSignal(Exception)
    progress = pyqtSignal(int)
    returnable = None

    def __init__(self, target=None, target_args=None, target_kwargs=None):
        super().__init__()
        self.target = target
        self.args = () if target_args is None else target_args
        self.kwargs = {} if target_kwargs is None else target_kwargs
        self.kwargs['progress'] = self.progress

    def run(self):
        try:

            returnable = self.target(*self.args, **self.kwargs)

            if not isinstance(returnable, tuple):
                returnable = (returnable,)

            self.finished.emit(returnable)

        except Exception as E:
            logger.exception(E)
            self.errored.emit(E)
