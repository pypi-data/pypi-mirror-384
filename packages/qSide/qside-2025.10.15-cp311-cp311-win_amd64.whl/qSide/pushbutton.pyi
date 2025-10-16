from .qt import QIcon as QIcon, QWidget as QWidget
from .theme import QIconProvider as QIconProvider, QTheme as QTheme
from qtpy import QtWidgets
from typing import Callable

class QPushButton(QtWidgets.QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None, icon: QIcon | str | None = None, tip: str = '', triggered: Callable[[bool], ...] | None = None, toggled: Callable[[bool], ...] | None = None) -> None: ...
    def setIcon(self, icon: QIcon | str, themed: bool = True): ...
