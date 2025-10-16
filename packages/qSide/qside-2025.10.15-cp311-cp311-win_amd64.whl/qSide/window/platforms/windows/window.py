from typing import Optional

from qtpy.QtCore import QByteArray
from qtpy.QtGui import QShowEvent
from qtpy.QtWidgets import QWidget

from .native_event import _native_event
from .titlebar import QTitleBar
from .utils import add_shadow_effect, add_window_animation, set_window_resizable, \
    is_window_resizable


class QWindowEx(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(QWindowEx, self).__init__(parent)
        self._titleBar = QTitleBar(self)
        add_shadow_effect(int(self.winId()))
        add_window_animation(int(self.winId()))

    def titleBar(self) -> QWidget:
        return self._titleBar

    def setTitleBar(self, titleBar: QWidget) -> None:
        self._titleBar = titleBar
        self.update()

    def setResizable(self, enable: bool) -> None:
        set_window_resizable(int(self.winId()), enable)
        self._titleBar.maximizeButton.hide() if not enable else self._titleBar.maximizeButton.show()

    def isResizable(self) -> None:
        return is_window_resizable(int(self.winId()))

    def showEvent(self, event: QShowEvent) -> None:
        self._titleBar.raise_()
        super(QWindowEx, self).showEvent(event)

    def nativeEvent(self, event_type: QByteArray, message: int):
        return _native_event(self, event_type, message)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._titleBar.resize(self.width(), self._titleBar.height())

    def setWindowTitle(self, title: str) -> None:
        self._titleBar.setText(title)

    def windowTitle(self) -> str:
        return self._titleBar.text()
