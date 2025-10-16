from enum import Enum

class QSideInfo:
    class LibraryLocation(Enum):
        TranslationsPath = 1
        FontsPath = 2
    @staticmethod
    def location(loc: LibraryLocation) -> str: ...
