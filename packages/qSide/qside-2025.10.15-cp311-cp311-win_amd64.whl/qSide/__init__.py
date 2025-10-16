# -*- coding: utf-8 -*-
# Copyright (C) 2018-2025 Connet Information Technology Company, Shanghai.

__version__ = "2025.10.15"

from .action import QAction
from .app import QPluginWidget, QPlugin, QApp, QEngine
from .breadcrumb import QBreadcrumbLabel
from .colorpick import QColorPick
from .config import (
    QOptionValidator, QRangeValidator, QStringValidator, QListValidator, QSizeValidator, QSizeFValidator,
    QFolderValidator, QShortcutValidator, QColorValidator, QMultiOptionsValidator, QEnumValidator,
    QBoolValidator, QEnumSerializer, QColorSerializer, QShortcutSerializer, QOptionItem, QUserConfig
)
from .document import QTextEditChange, QTextDocumentEx
from .infobadge import QInfoBadge, QDotInfoBadge, QIconInfoBadge
from .inputdialog import QInputDialog
from .itemdelegate import QHtmlStyledItemDelegate
from .label import QElideLabel
from .layout import QGrid, QForm, QStacked, QHBox, QVBox, MARGIN_MEDIUM, MARGIN_LARGE, MARGIN_SMALL, PADDING_LARGE, PADDING_MEDIUM, PADDING_SMALL, PADDING_EXTREME_SMALL, SPACING_SMALL, SPACING_EXTREME_SMALL, SPACING_MEDIUM, SPACING_LARGE
from .lineedit import QLineEditButton, QLineEditEx
from .listwidget import QHtmlListWidget
from .logging import QLogger, QLogFile, QLogging
from .mainwindow import QMainWindow
from .menu import QRoundMenu
from .messagebox import QMessageBox
from .pushbutton import QPushButton
from .python_ext import QPostInitObjectMeta
from .scrollbar import QScrollBar, QScrollDelegate
from .seperator import QHLine, QVLine
from .statetooltip import QStateToolTip
from .tabwidget import QTabBarEx, QTabWidget
from .textcursor import QTextDocumentCursor
from .theme import qLoadResources, QIconProvider, QTheme
from .toolbutton import QToolButton
from .tooltip import QToolTipFilter
from .treewidget import QHtmlTreeWidget
from .treeview import QHtmlTreeView
from .window import QWindowEx, QMainWindowEx, QDialogEx, QTitleBar
from .stylesheet import QStylesheet
from .libraryinfo import QSideInfo
from .fontfamily import SANS_SERIF, MONOSPACE
from .spacer import QHSpacer, QVSpacer
from .codeeditor.codeeditor import QCodeEditor
from .codeeditor.extension import QCodePanel, QCodeExtension
from .codeeditor.scheme import QCodeScheme,LIGHT,DARK
from .codeeditor.features import QLanguageFeatures, PYTHON_FEATURES, PLAIN_TEXT_FEATURES, Comments, AutoClosingPair, FoldingMarkers, Folding, OnEnterAction, OnEnterRule, IndentationRules
from .codeeditor.hexeditor import QHexEditor, QHexDocument
from .codeeditor.syntaxhighlighter import PythonSyntaxHighlighter, QSyntaxHighlighter, QTreeSitterSyntaxHighlighter
from .codeeditor.textdecoration import QTextDecoration
from .qt import *