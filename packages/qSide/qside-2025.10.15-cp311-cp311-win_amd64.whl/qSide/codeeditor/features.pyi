from ..qt import QIcon as QIcon
from _typeshed import Incomplete
from dataclasses import dataclass
from typing import Literal

@dataclass
class Comments:
    lineComment: str | None = ...
    blockComment: list[str] | None = ...

@dataclass
class AutoClosingPair:
    open: str
    close: str
    notIn: list[str] | None = ...

@dataclass
class FoldingMarkers:
    start: str
    end: str

@dataclass
class Folding:
    markers: FoldingMarkers

@dataclass
class OnEnterAction:
    indent: Literal['none', 'indent', 'outdent', 'indentOutdent'] = ...

@dataclass
class OnEnterRule:
    beforeText: str
    action: OnEnterAction

@dataclass
class IndentationRules:
    increaseIndentPattern: str
    decreaseIndentPattern: str

@dataclass(frozen=True)
class QLanguageFeatures:
    language: str
    fileMimeType: str
    fileNameFilters: list[str]
    fileNameIcons: list[QIcon]
    comments: Comments
    brackets: list[list[str]]
    autoClosingPairs: list[AutoClosingPair]
    autoCloseBefore: str
    surroundingPairs: list[list[str]]
    folding: Folding
    indentationRules: IndentationRules
    onEnterRules: list[OnEnterRule]

PLAIN_TEXT_FEATURES: Incomplete
PYTHON_FEATURES: Incomplete
