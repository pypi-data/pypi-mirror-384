from typing import Optional

from qtpy.QtCore import QByteArray
from qtpy.QtGui import QShowEvent
from qtpy.QtWidgets import QWidget, QMainWindow

from .native_event import _native_event
from .titlebar import QTitleBar
from .utils import add_shadow_effect, add_window_animation, set_window_resizable, \
    is_window_resizable


class QMainWindowEx(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

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

    def windowTitle(self) -> str:
        return self._titleBar.text()

    def setWindowTitle(self, text: str):
        self._titleBar.setText(text)

    def showEvent(self, event: QShowEvent) -> None:
        self._titleBar.raise_()
        super(QMainWindowEx, self).showEvent(event)

    def nativeEvent(self, event_type: QByteArray, message: int):
        return _native_event(self, event_type, message)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        menuBarWidth = self.getMenuBarVisibleWidth()
        self._titleBar.move(menuBarWidth, 0)
        self._titleBar.resize(self.width() - menuBarWidth, self._titleBar.height())

    def getMenuBarVisibleWidth(self):
        total_width = sum(self.menuBar().actionGeometry(act).width() for act in self.menuBar().actions())
        return total_width
