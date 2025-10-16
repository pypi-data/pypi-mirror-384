from ...action import QAction as QAction
from ...layout import MARGIN_MEDIUM as MARGIN_MEDIUM, MARGIN_SMALL as MARGIN_SMALL, QHBox as QHBox, QVBox as QVBox, SPACING_EXTREME_SMALL as SPACING_EXTREME_SMALL
from ...lineedit import QLineEditEx as QLineEditEx
from ...messagebox import QMessageBox as QMessageBox
from ...pushbutton import QPushButton as QPushButton
from ...qt import QApplication as QApplication, QEvent as QEvent, QKeyEvent as QKeyEvent, QLabel as QLabel, QObject as QObject, QPaintEvent as QPaintEvent, QPainter as QPainter, QPen as QPen, QSplitter as QSplitter, QWidget as QWidget, Qt as Qt
from ...toolbutton import QToolButton as QToolButton
from ..extension import QCodePanel as QCodePanel
from ..textdecoration import QTextDecoration as QTextDecoration
from .decorator import Decorator as Decorator
from _typeshed import Incomplete

class FindReplacePanel(QCodePanel):
    A_NAME: str
    A_AREA: Incomplete
    A_AREA_GRAVITY: int
    A_Z_ORDER: int
    A_SCROLLABLE: bool
    MAX_HIGHLIGHT_MATCHES: int
    MATCH_DECORATION: str
    openFindPanelAction: Incomplete
    openReplacePanelAction: Incomplete
    findEdit: Incomplete
    replaceEdit: Incomplete
    toggleReplaceAction: Incomplete
    matchCaseAction: Incomplete
    matchWordsAction: Incomplete
    regexAction: Incomplete
    matchedCountLabel: Incomplete
    previousOccurrenceButton: Incomplete
    nextOccurrenceButton: Incomplete
    closeButton: Incomplete
    replaceButton: Incomplete
    replaceAllButton: Incomplete
    splitter: Incomplete
    def __init__(self, editor: QCodeEditor) -> None: ...
    def paintEvent(self, event: QPaintEvent): ...
    def initialize(self): ...
    def setReplaceToolsVisible(self, visible: bool): ...
    def setReplaceEnabled(self, enable: bool): ...
    def isReplaceEnabled(self) -> bool: ...
    def openFindPanel(self) -> None: ...
    def openReplacePanel(self) -> None: ...
    def beforeEditorKeyPressEvent(self, event: QKeyEvent) -> bool: ...
    def eventFilter(self, widget: QObject, event: QEvent) -> bool: ...
    def sizeHint(self): ...
    def show(self) -> None: ...
    def hide(self) -> None: ...
    @property
    def decorator(self) -> Decorator | None: ...
