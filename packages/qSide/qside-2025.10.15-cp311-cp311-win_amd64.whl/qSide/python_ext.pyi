from .qt import QObject as QObject
from _typeshed import Incomplete

class classproperty(property):
    def __get__(self, cls, owner): ...

def caller(func: str) -> str: ...

class QPostInitObjectMeta(Incomplete):
    def __call__(cls, *args, **kwargs): ...
