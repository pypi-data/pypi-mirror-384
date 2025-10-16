import ctypes
from ctypes.wintypes import POINT

import win32con
import win32gui

from qtpy.QtCore import QByteArray, QPoint, Qt, QEvent
from qtpy.QtGui import QMouseEvent, QCursor
from qtpy.QtWidgets import QWidget, QPushButton, QApplication

from .c_structures import LPNCCALCSIZE_PARAMS
from .titlebar import MaximizeButtonState
from .utils import is_maximized, is_full_screen


def _native_event(widget: QWidget, event_type: QByteArray, message: int):
    msg = ctypes.wintypes.MSG.from_address(message.__int__())
    # get windowsOS native frame width
    user32 = ctypes.windll.user32
    dpi = user32.GetDpiForWindow(msg.hWnd)
    borderW = user32.GetSystemMetricsForDpi(win32con.SM_CXSIZEFRAME, dpi)# + user32.GetSystemMetricsForDpi(92, dpi)
    borderH = user32.GetSystemMetricsForDpi(win32con.SM_CYSIZEFRAME, dpi)# + user32.GetSystemMetricsForDpi(92, dpi)

    cpt = QCursor.pos()
    csc = QApplication.screenAt(cpt)
    wsc = widget.window().windowHandle().screen()
    pt = (((cpt - csc.geometry().topLeft()) * csc.devicePixelRatio() + csc.geometry().topLeft()) - wsc.geometry().topLeft()) / wsc.devicePixelRatio() + wsc.geometry().topLeft()

    # Qt geometry . x, y is in 1.0 factor scaling system, and width and height in DPI scaling system.
    geo = widget.geometry()
    x = pt.x() - geo.x()
    y = pt.y() - geo.y()

    if msg.message == win32con.WM_NCHITTEST:
        if widget.isResizable() and not is_maximized(msg.hWnd):
            w, h = geo.width(), geo.height()
            lx = x < borderW
            rx = x >= w - borderW
            ty = y < borderH
            by = y >= h - borderH

            if lx and ty:
                return True, win32con.HTTOPLEFT
            if rx and by:
                return True, win32con.HTBOTTOMRIGHT
            if rx and ty:
                return True, win32con.HTTOPRIGHT
            if lx and by:
                return True, win32con.HTBOTTOMLEFT
            if ty:
                return True, win32con.HTTOP
            if by:
                return True, win32con.HTBOTTOM
            if lx:
                return True, win32con.HTLEFT
            if rx:
                return True, win32con.HTRIGHT

        if widget.childAt(QPoint(x, y)) is widget._titleBar.maximizeButton:
            widget._titleBar.maximizeButton.setState(MaximizeButtonState.Hover)
            return True, win32con.HTMAXBUTTON

        if widget.childAt(x, y) not in widget._titleBar.findChildren(QPushButton):
            return False, 0
            # if borderHeight < y < widget._titleBar.height():
            #     return True, win32con.HTCAPTION

    elif msg.message == win32con.WM_MOVE:
        win32gui.SetWindowPos(msg.hWnd, None, 0, 0, 0, 0, win32con.SWP_NOMOVE |
                              win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE]:
        widget._titleBar.maximizeButton.setState(MaximizeButtonState.Normal)
    elif msg.message in [win32con.WM_NCLBUTTONDOWN, win32con.WM_NCLBUTTONDBLCLK]:
        if widget.childAt(QPoint(x, y)) is widget._titleBar.maximizeButton:
            QApplication.sendEvent(widget._titleBar.maximizeButton, QMouseEvent(
                QEvent.MouseButtonPress, QPoint(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
            return True, 0
    elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP]:
        if widget.childAt(QPoint(x, y)) is widget._titleBar.maximizeButton:
            QApplication.sendEvent(widget._titleBar.maximizeButton, QMouseEvent(
                QEvent.MouseButtonRelease, QPoint(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))

    elif msg.message == win32con.WM_NCCALCSIZE:
        rect = ctypes.cast(msg.lParam, LPNCCALCSIZE_PARAMS).contents.rgrc[0]

        isMax = is_maximized(msg.hWnd)
        isFull = is_full_screen(msg.hWnd)

        # adjust the size of client rect
        if isMax and not isFull:
            rect.top += borderH
            rect.left += borderW
            rect.right -= borderW
            rect.bottom -= borderH

        return True, win32con.WVR_REDRAW

    return False, 0
