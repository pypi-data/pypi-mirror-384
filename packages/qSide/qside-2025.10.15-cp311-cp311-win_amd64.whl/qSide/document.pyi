from .qt import QFont as QFont, QObject as QObject, QPlainTextDocumentLayout as QPlainTextDocumentLayout, QTextOption as QTextOption, Signal as Signal
from .textcursor import QTextDocumentCursor as QTextDocumentCursor
from _typeshed import Incomplete
from collections.abc import Generator
from contextlib import contextmanager
from qtpy import QtGui

class QTextEditChange:
    startCharacter: Incomplete
    oldEndCharacter: Incomplete
    newEndCharacter: Incomplete
    startPoint: Incomplete
    oldEndPoint: Incomplete
    newEndPoint: Incomplete
    removedText: Incomplete
    addedText: Incomplete
    def __init__(self, startCharacter: int, oldEndCharacter: int, newEndCharacter: int, startPoint: tuple[int, int], oldEndPoint: tuple[int, int], newEndPoint: tuple[int, int], removedText: str, addedText: str) -> None: ...

class QTextDocumentEx(QtGui.QTextDocument):
    textEditChanged: Incomplete
    def __init__(self, parent=None) -> None: ...
    @contextmanager
    def recordDocumentForContentsChangeComparison(self) -> Generator[None]: ...
    def setPlainText(self, text: str): ...
