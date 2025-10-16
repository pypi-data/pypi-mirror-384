from .itemdelegate import QHtmlStyledItemDelegate as QHtmlStyledItemDelegate
from .qt import QFrame as QFrame
from qtpy import QtWidgets

class QHtmlListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None) -> None: ...
