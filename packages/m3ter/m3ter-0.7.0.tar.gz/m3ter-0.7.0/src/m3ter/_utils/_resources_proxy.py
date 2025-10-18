from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `m3ter.resources` module.

    This is used so that we can lazily import `m3ter.resources` only when
    needed *and* so that users can just import `m3ter` and reference `m3ter.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("m3ter.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
