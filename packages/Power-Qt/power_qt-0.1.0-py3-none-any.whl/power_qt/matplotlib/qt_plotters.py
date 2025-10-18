import matplotlib
from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure

matplotlib.use('QTAgg')
__all__ = ['MplCanvas', 'MplTabbar']


class MplCanvas(Canvas):
    """
    Qt compatible matplotlib Canvas class, used as the base canvas
    in all widgets that conduct plotting.
    """
    ax: Axes | list[Axes]
    fig: Figure

    def __init__(self, figsize=(8.5, 11),
                 dpi=100,
                 width_ratios=None,
                 height_ratios=None,
                 nrows=1,
                 ncols=1,
                 *args,
                 **kwargs):
        self.fig = Figure(figsize=figsize,
                          dpi=dpi)

        self.ax = self.fig.subplots(nrows=nrows,
                                    ncols=ncols,
                                    width_ratios=width_ratios,
                                    height_ratios=height_ratios,
                                    *args,
                                    **kwargs)

        Canvas.__init__(self, self.fig)
        # Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        Canvas.updateGeometry(self)


class MplTabbar(QTabWidget):
    """
    Qt compatible tab widget with integrated MplCanvas creation
    """

    figure_tabs: list[MplCanvas] = []

    def __init__(self, parent=None):
        super().__init__(parent)

    def addPlot(self, figsize=(8.5, 11),
                dpi=100,
                width_ratios=None,
                height_ratios=None,
                nrows=1,
                ncols=1,
                tabname='Tab',
                *args,
                **kwargs):
        new_wid = QWidget()
        new_lay = QVBoxLayout()
        new_wid.setLayout(new_lay)
        new_lay.setContentsMargins(0, 0, 0, 0)

        new_canvas = MplCanvas(figsize=figsize,
                               dpi=dpi,
                               width_ratios=width_ratios,
                               height_ratios=height_ratios,
                               nrows=nrows,
                               ncols=ncols,
                               *args,
                               **kwargs)

        new_toolbar = NavigationToolbar(new_canvas, new_wid)
        self.figure_tabs.append(new_canvas)
        new_lay.addWidget(new_canvas)
        new_lay.addWidget(new_toolbar)

        super().addTab(new_wid, tabname)
