from .itemdelegate import QHtmlStyledItemDelegate as QHtmlStyledItemDelegate
from .qt import QFrame as QFrame
from _typeshed import Incomplete
from qtpy import QtWidgets

class QHtmlTreeWidget(QtWidgets.QTreeWidget):
    styledItemDelegate: Incomplete
    def __init__(self, parent=None) -> None: ...
