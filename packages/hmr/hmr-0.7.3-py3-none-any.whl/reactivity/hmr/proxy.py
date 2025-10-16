from collections.abc import MutableMapping
from typing import Any

from reactivity.context import Context

from ..collections import ReactiveMappingProxy


class Proxy[T: MutableMapping](ReactiveMappingProxy[str, Any]):
    def __init__(self, initial: MutableMapping[str, Any], check_equality=True, *, context: Context | None = None):
        super().__init__(initial, check_equality, context=context)
        self.raw: T = self._data  # type: ignore
