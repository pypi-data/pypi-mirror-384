from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtGui import QColor, QPalette, QPainter, QBrush
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem


class SelectedHighlighter(QStyledItemDelegate):
    """Delegate for changing highlighting behavior in QTableviews"""

    color_default = QColor("#CFAAFF")

    _test_color = '#FFAAFB'

    _properties = {'foreground': {'selected': {'active': "#000000",
                                               'inactive': "#000000"},
                                  'unselected': {'active': "#000000",
                                                 'inactive': "#000000"}
                                  },
                   'background': {'selected': {'active': "#B8B8B8",
                                               'inactive': "#B8B8B8"},
                                  'unselected': {'active': "#000000",
                                                 'inactive': "#000000"}}}

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:

        if option.state & QStyle.StateFlag.State_Selected:  # color mixing for selected indexes
            item_color = index.data(
                Qt.ItemDataRole.BackgroundRole)  # retrieve background color of the index, if one exists
            mix_color = self._properties.get('background').get('selected').get('active')

            if item_color is not None:
                mixed_color = SelectedHighlighter.combineColors(item_color, mix_color)
                option.palette.setColor(QPalette.ColorRole.Highlight,
                                        mixed_color)  # background color changes if selected

        QStyledItemDelegate.paint(self, painter, option, index)

    def initStyleOption(self, option: QStyleOptionViewItem, index):
        super(SelectedHighlighter, self).initStyleOption(option, index)

        c_selected = QColor(
            self._properties.get('background').get('selected').get('active'))  # coloring of font in the selection
        color_unselect = self._properties.get('foreground').get('unselected').get(
            'active')  # color of the unselected font if available, otherwise default to black

        c_unselected = index.data(Qt.ItemDataRole.ForegroundRole)
        c_unselected = c_unselected if isinstance(c_unselected, QColor) else QColor(color_unselect)

        cg = (
            QPalette.ColorGroup.Active if option.state & QStyle.StateFlag.State_Enabled else QPalette.ColorGroup.Disabled)

        if option.state & QStyle.StateFlag.State_Selected:
            option.palette.setColor(cg, QPalette.ColorRole.HighlightedText, c_selected)  # text color for selected

            # option.palette.setColor(cg, QPalette.ColorRole.Highlight, QColor(self._test_color)) #background color for selected

        # option.backgroundBrush = QBrush(QColor('white'))#colors background of listview

        option.palette.setBrush(QPalette.ColorRole.Text, c_unselected)  #
        """
        setBrush(self, cg: QPalette.ColorGroup, cr: QPalette.ColorRole, brush: Union[QBrush, Union[QColor, Qt.GlobalColor, int], QGradient])
        setBrush(self, acr: QPalette.ColorRole, abrush: Union[QBrush, Union[QColor, Qt.GlobalColor, int], QGradient])
        """

    def initStyleOptionTest(self, option: QStyleOptionViewItem, index):
        """Testing Method"""

        super(SelectedHighlighter, self).initStyleOption(option, index)

        # use option.state and QStyle.StateFlags for finer control of coloring

        if option.state & QStyle.StateFlag.State_Selected:
            pass

            # Status type as ColorGroup, then target role as ColorRole
            option.palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor('#FFAAFB'))
            option.palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor('#BEAAFF'))
            option.palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor('#AAC9FF'))

            option.palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor('#FF00FB'))
            option.palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor('#6536FF'))
            option.palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, QColor('#3680FF'))

            option.palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor('#000000'))
            option.palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor('#000000'))
            option.palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor('#000000'))

        option.backgroundBrush = QBrush(QColor(100, 200, 100, 200))  # colors entire background

        """
        QPalette.ColorGroup.Disabled
        QPalette.ColorGroup.Active #AKA Normal
        QPalette.ColorGroup.Inactive
        """

    @staticmethod
    def combineColors(color1, color2) -> QColor:
        color1 = QColor(color1) if not isinstance(color1, QColor) else color1
        color2 = QColor(color2) if not isinstance(color2, QColor) else color2
        mixed_color = QColor()

        # average color channels
        mixed_color.setRed(int((color1.red() + color2.red()) / 2))
        mixed_color.setGreen(int((color1.green() + color2.green()) / 2))
        mixed_color.setBlue(int((color1.blue() + color2.blue()) / 2))

        return mixed_color
