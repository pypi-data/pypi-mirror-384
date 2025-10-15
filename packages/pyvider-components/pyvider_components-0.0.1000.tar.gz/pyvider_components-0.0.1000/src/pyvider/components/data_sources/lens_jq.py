#
# pyvider/components/data_sources/lens_jq.py
#

import json
from typing import Any, cast

from attrs import define

from provide.foundation import logger
from pyvider.conversion import cty_to_native
from pyvider.data_sources.base import BaseDataSource
from pyvider.data_sources.decorators import register_data_source
from pyvider.exceptions import DataSourceError
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_dyn, a_str, s_data_source

from ..capabilities.lens import LensCapability


@define(frozen=True)
class LensJqConfig:
    json_input: str
    query: str


@define(frozen=True)
class LensJqState:
    json_input: str
    query: str
    result: Any


@register_data_source("pyvider_lens_jq", component_of="lens")
class LensJqDataSource(BaseDataSource["pyvider_lens_jq", LensJqState, LensJqConfig]):
    config_class = LensJqConfig
    state_class = LensJqState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_data_source(
            {
                "json_input": a_str(required=True),
                "query": a_str(required=True),
                "result": a_dyn(computed=True),
            }
        )

    async def _validate_config(self, config: LensJqConfig) -> list[str]:
        return []

    async def read(self, ctx: ResourceContext, *, lens: LensCapability) -> LensJqState:
        if not lens.is_enabled:
            raise DataSourceError(
                "The 'lens' capability is disabled in the provider configuration."
            )

        config = cast(LensJqConfig, ctx.config)
        if not config:
            raise DataSourceError("Configuration is missing.")

        try:
            parsed_json = json.loads(config.json_input)
        except json.JSONDecodeError as e:
            raise DataSourceError(f"Invalid JSON in 'json_input': {e}") from e

        try:
            logger.debug(
                f"🔧 LENS_JQ_DATA_SOURCE about to call lens.jq with query={config.query!r}, input_data={parsed_json}"
            )
            logger.debug(
                f"🔧 LENS_JQ_DATA_SOURCE lens object: {lens}, type: {type(lens)}"
            )
            result_cty_value = lens.jq(config.query, parsed_json)
            logger.debug(
                f"🔧 LENS_JQ_DATA_SOURCE lens.jq returned: {type(result_cty_value)} = {result_cty_value}"
            )
            native_result = cty_to_native(result_cty_value)
            logger.debug(
                f"🔧 LENS_JQ_DATA_SOURCE final result: {type(native_result)} = {native_result}"
            )
            return LensJqState(
                json_input=config.json_input, query=config.query, result=native_result
            )
        except Exception as e:
            raise DataSourceError(f"Error processing jq query: {e}") from e


# 🔍🔧📊
