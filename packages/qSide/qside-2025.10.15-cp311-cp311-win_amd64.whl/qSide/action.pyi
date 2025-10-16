from .qt import QIcon as QIcon, QKeySequence as QKeySequence, QObject as QObject, Qt as Qt
from .theme import QIconProvider as QIconProvider, QTheme as QTheme
from qtpy import QtGui
from typing import Any, Callable

class QAction(QtGui.QAction):
    visiblePredicate: Callable[[QAction], bool] | None
    enabledPredicate: Callable[[QAction], bool] | None
    checkedPredicate: Callable[[QAction], bool] | None
    def __init__(self, name: str, text: str = '', parent: QObject | None = None, icon: QIcon | str | None = None, tip: str = '', data: Any = None, checkable: bool = False, checked: bool = False, shortcut: QKeySequence | QKeySequence.StandardKey | str | int = '', shortcutContext: Qt.ShortcutContext = ..., visiblePredicate: Callable[[QAction], bool] | None = None, enabledPredicate: Callable[[QAction], bool] | None = None, checkedPredicate: Callable[[QAction], bool] | None = None, triggered: Callable[[bool], None] | None = None, toggled: Callable[[bool], None] | None = None) -> None: ...
    def setIcon(self, icon: QIcon | str, themed: bool = True): ...
