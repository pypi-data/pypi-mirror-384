from .action import QAction as QAction
from .qt import QIcon as QIcon, QSplitter as QSplitter, QStackedWidget as QStackedWidget, QToolBar as QToolBar, QWidget as QWidget, Qt as Qt, Signal as Signal
from .toolbutton import QToolButton as QToolButton
from .window import QMainWindowEx as QMainWindowEx
from _typeshed import Incomplete
from enum import Enum

class QMainWindow(QMainWindowEx):
    closed: Incomplete
    class Area(Enum):
        Left = 'left'
        Right = 'right'
        BottomLeft = 'bottom-left'
        BottomRight = 'bottom-right'
    def __init__(self) -> None: ...
    def toolBar(self) -> QToolBar: ...
    def addDockWidget(self, area: Area, name: str, icon: QIcon | str, widget: QWidget, before: str | None = None): ...
    def removeDockWidget(self, area: Area, index: int): ...
    def closeEvent(self, event) -> None: ...
