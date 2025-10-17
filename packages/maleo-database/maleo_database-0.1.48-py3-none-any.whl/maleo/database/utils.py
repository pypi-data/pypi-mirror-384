from typing import Literal, overload
from maleo.types.string import ListOfStrs, OptStr
from .enums import CacheOrigin, CacheLayer


@overload
def build_cache_namespace(
    *ext: str,
    base: OptStr = None,
    origin: Literal[CacheOrigin.SERVICE],
    layer: CacheLayer,
    sep: str = ":",
) -> str: ...
@overload
def build_cache_namespace(
    *ext: str,
    base: OptStr = None,
    client: str,
    origin: Literal[CacheOrigin.CLIENT],
    layer: CacheLayer,
    sep: str = ":",
) -> str: ...
def build_cache_namespace(
    *ext: str,
    base: OptStr = None,
    client: OptStr = None,
    origin: CacheOrigin,
    layer: CacheLayer,
    sep: str = ":",
) -> str:
    slugs: ListOfStrs = []
    if base is not None:
        slugs.append(base)
    slugs.extend([origin, layer])
    if client is not None:
        slugs.append(client)
    slugs.extend(ext)
    return sep.join(slugs)


def build_cache_key(*ext: str, namespace: str, sep: str = ":"):
    return sep.join([namespace, *ext])
