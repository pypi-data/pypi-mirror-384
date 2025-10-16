import sys

if sys.platform == "darwin":
    from .mac import QWindowEx, QMainWindowEx, QDialogEx, QTitleBar
else:
    from .windows import QWindowEx, QMainWindowEx, QDialogEx, QTitleBar
