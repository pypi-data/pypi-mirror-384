from typing import TypeAlias

from codeapi.types import CodeAPIError, CodeAPIException

from ._async import AsyncClient
from ._sync import Client

AsyncCodeAPI: TypeAlias = AsyncClient
CodeAPI: TypeAlias = Client


def __get_version():
    import importlib.metadata

    try:
        return importlib.metadata.version(__name__)
    except Exception:
        return None


__version__ = __get_version()

__all__ = [
    "CodeAPIError",
    "CodeAPIException",
    "AsyncClient",
    "AsyncCodeAPI",
    "Client",
    "CodeAPI",
]


for __name in __all__:
    if not __name.startswith("__") and hasattr(locals()[__name], "__module__"):
        setattr(locals()[__name], "__module__", __name__)

del __get_version
