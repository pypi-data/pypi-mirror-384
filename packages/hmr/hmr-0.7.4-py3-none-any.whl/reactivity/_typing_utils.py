from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import deprecated
else:
    deprecated = lambda _: lambda _: _
