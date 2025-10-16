from .qt import QIcon as QIcon, QObject as QObject
from .theme import QIconProvider as QIconProvider, QTheme as QTheme
from .tooltip import QToolTipFilter as QToolTipFilter
from qtpy import QtWidgets
from typing import Callable

class QToolButton(QtWidgets.QToolButton):
    def __init__(self, name: str, text: str = '', parent: QObject = None, icon: QIcon | str | None = None, tip: str = '', triggered: Callable[[bool], ...] | None = None, toggled: Callable[[bool], ...] | None = None) -> None: ...
    def setIcon(self, icon: QIcon | str, themed: bool = True): ...
