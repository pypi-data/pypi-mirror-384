import qdarkstyle
from .layout import BORDER_THIN_LINE_WIDTH as BORDER_THIN_LINE_WIDTH, BORDER_TIP_RADIUS as BORDER_TIP_RADIUS, BORDER_WINDOW_RADIUS as BORDER_WINDOW_RADIUS, PADDING_EXTREME_SMALL as PADDING_EXTREME_SMALL, PADDING_MEDIUM as PADDING_MEDIUM, SPACING_SMALL as SPACING_SMALL
from .qt import QFontMetrics as QFontMetrics

class QStylesheet:
    def __init__(self, fm: QFontMetrics, palette: qdarkstyle.palette.Palette) -> None: ...
    def toString(self) -> str: ...
