from pydantic import BaseModel, Field
from typing import Annotated, Literal, TypeVar, overload
from maleo.enums.expiration import Expiration
from maleo.types.string import OptStr
from ..enums import CacheOrigin, CacheLayer
from ..utils import build_cache_namespace


class BaseAdditionalConfig(BaseModel):
    """Base additional configuration class for database."""


OptBaseAdditionalConfig = BaseAdditionalConfig | None
AdditionalConfigT = TypeVar("AdditionalConfigT", bound=OptBaseAdditionalConfig)


class RedisAdditionalConfig(BaseAdditionalConfig):
    ttl: Annotated[
        float | int | Expiration,
        Field(Expiration.EXP_15MN.value, description="Time to live"),
    ] = Expiration.EXP_15MN.value
    base_namespace: Annotated[str, Field(..., description="Base namespace")]

    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[False],
        base: OptStr = None,
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[False],
        base: OptStr = None,
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[True],
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[True],
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    def build_namespace(
        self,
        *ext: str,
        use_self_base: bool = True,
        base: OptStr = None,
        client: OptStr = None,
        origin: CacheOrigin,
        layer: CacheLayer,
        sep: str = ":",
    ) -> str:
        if use_self_base:
            final_base = self.base_namespace
        else:
            final_base = base
        if origin is CacheOrigin.CLIENT:
            if client is None:
                raise ValueError(
                    "Argument 'client' can not be None if origin is client"
                )

            return build_cache_namespace(
                *ext,
                base=final_base,
                client=client,
                origin=origin,
                layer=layer,
                sep=sep,
            )

        return build_cache_namespace(
            *ext,
            base=final_base,
            origin=origin,
            layer=layer,
            sep=sep,
        )
