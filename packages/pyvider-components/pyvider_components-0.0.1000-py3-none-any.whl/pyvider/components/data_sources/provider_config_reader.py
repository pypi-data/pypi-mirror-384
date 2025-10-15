#
# pyvider/components/data_sources/provider_config_reader.py
#

from typing import Any, cast

from attrs import define

from pyvider.data_sources.base import BaseDataSource
from pyvider.data_sources.decorators import register_data_source
from pyvider.exceptions import DataSourceError
from pyvider.hub import hub
from pyvider.providers.context import ProviderContext
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_bool, a_map, a_num, a_str, s_data_source


@define(frozen=True)
class ProviderConfigReaderState:
    api_endpoint: str | None = None
    api_token: str | None = None
    api_timeout: int | None = None
    api_retries: int | None = None
    api_insecure_skip_verify: bool | None = None
    api_headers: dict[str, str] | None = None


@register_data_source("pyvider_provider_config_reader")
class ProviderConfigReaderDataSource(BaseDataSource):
    state_class = ProviderConfigReaderState
    config_class = None

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_data_source(
            attributes={
                "api_endpoint": a_str(computed=True),
                "api_token": a_str(computed=True, sensitive=True),
                "api_timeout": a_num(computed=True),
                "api_retries": a_num(computed=True),
                "api_insecure_skip_verify": a_bool(computed=True),
                "api_headers": a_map(a_str(), computed=True),
            }
        )

    async def _validate_config(self, config: Any) -> list[str]:
        return []

    async def read(self, ctx: ResourceContext) -> ProviderConfigReaderState:
        provider_ctx = cast(
            ProviderContext, hub.get_component("singleton", "provider_context")
        )
        if not provider_ctx or not provider_ctx.config:
            raise DataSourceError("Provider context has not been configured.")
        provider_config = provider_ctx.config
        return ProviderConfigReaderState(
            api_endpoint=getattr(provider_config, "api_endpoint", None),
            api_token=getattr(provider_config, "api_token", None),
            api_timeout=getattr(provider_config, "api_timeout", None),
            api_retries=getattr(provider_config, "api_retries", None),
            api_insecure_skip_verify=getattr(
                provider_config, "api_insecure_skip_verify", None
            ),
            api_headers=getattr(provider_config, "api_headers", None),
        )


# ⚙️📖📊
