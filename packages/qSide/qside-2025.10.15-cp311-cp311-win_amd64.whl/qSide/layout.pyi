from .qt import QLayout as QLayout, QLayoutItem as QLayoutItem, QWidget as QWidget, Qt as Qt
from qtpy import QtWidgets
from typing import Iterable

PADDING_LARGE: int
PADDING_MEDIUM: int
PADDING_SMALL: int
PADDING_EXTREME_SMALL: int
MARGIN_LARGE: int
MARGIN_MEDIUM: int
MARGIN_SMALL: int
SPACING_LARGE: int
SPACING_MEDIUM: int
SPACING_SMALL: int
SPACING_EXTREME_SMALL: int
BORDER_LINE_WIDTH: int
BORDER_THIN_LINE_WIDTH: int
BORDER_WINDOW_RADIUS: int
BORDER_TIP_RADIUS: int
BORDER_SHARP_RADIUS: int

def normMargins(margins: int | tuple[int, int, int, int]) -> tuple[int, int, int, int]: ...

class QVBox(QtWidgets.QVBoxLayout):
    def __init__(self, *items: QWidget | QLayout | QLayoutItem, spacing: int = ..., margins: int | tuple[int, int, int, int] = 0) -> None: ...

class QHBox(QtWidgets.QHBoxLayout):
    def __init__(self, *items: QWidget | QLayout | QLayoutItem, spacing: int = ..., margins: int | tuple[int, int, int, int] = 0) -> None: ...

class QForm(QtWidgets.QFormLayout):
    def __init__(self, fields: Iterable[tuple[str, QWidget]], spacing: int = ..., margins: int | tuple[int, int, int, int] = 0) -> None: ...

class QGrid(QtWidgets.QGridLayout):
    def __init__(self, spacing: int = ..., margins: int | tuple[int, int, int, int] = 0) -> None: ...

class QStacked(QtWidgets.QStackedLayout):
    def __init__(self, *items: QWidget | QLayout | QLayoutItem, spacing: int = ..., margins: int | tuple[int, int, int, int] = 0, stackingMode: QtWidgets.QStackedLayout.StackingMode = ...) -> None: ...
