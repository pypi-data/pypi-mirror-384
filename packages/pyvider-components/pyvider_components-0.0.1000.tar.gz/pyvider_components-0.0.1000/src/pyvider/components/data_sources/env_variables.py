#
# pyvider/components/data_sources/env_variables.py
#

import os
import re
from typing import cast

from attrs import define, field

from provide.foundation import logger
from provide.foundation.errors import capture_error_context, resilient
from pyvider.data_sources.base import BaseDataSource
from pyvider.data_sources.decorators import register_data_source
from pyvider.exceptions import DataSourceError
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_bool, a_list, a_map, a_str, s_data_source


@define(frozen=True)
class EnvVariablesConfig:
    keys: list[str] | None = None
    prefix: str | None = None
    regex: str | None = None
    exclude_empty: bool | None = None
    transform_keys: str | None = None
    transform_values: str | None = None
    case_sensitive: bool | None = None
    sensitive_keys: list[str] | None = None


@define(frozen=True)
class EnvVariablesState:
    values: dict[str, str] = field(factory=dict)
    sensitive_values: dict[str, str] = field(factory=dict)
    all_values: dict[str, str] = field(factory=dict)
    all_environment: dict[str, str] = field(factory=dict)


@register_data_source("pyvider_env_variables")
class EnvVariablesDataSource(
    BaseDataSource["pyvider_env_variables", EnvVariablesState, EnvVariablesConfig]
):
    config_class = EnvVariablesConfig
    state_class = EnvVariablesState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_data_source(
            attributes={
                "keys": a_list(a_str(), optional=True),
                "prefix": a_str(optional=True),
                "regex": a_str(optional=True),
                "exclude_empty": a_bool(optional=True, default=True),
                "transform_keys": a_str(optional=True),
                "transform_values": a_str(optional=True),
                "case_sensitive": a_bool(optional=True, default=True),
                "sensitive_keys": a_list(a_str(), optional=True),
                "values": a_map(a_str(), computed=True),
                "sensitive_values": a_map(a_str(), computed=True, sensitive=True),
                "all_values": a_map(a_str(), computed=True),
                "all_environment": a_map(a_str(), computed=True),
            }
        )

    @resilient()
    async def _validate_config(self, config: EnvVariablesConfig) -> list[str]:
        filter_count = sum(
            1 for v in [config.keys, config.prefix, config.regex] if v is not None
        )
        if filter_count > 1:
            logger.debug(
                "Multiple filters specified",
                keys=config.keys is not None,
                prefix=config.prefix is not None,
                regex=config.regex is not None,
            )
            return ["Only one of 'keys', 'prefix', or 'regex' can be specified."]
        logger.debug(
            "Environment variables configuration validation passed",
            filter_count=filter_count,
        )
        return []

    @resilient()
    async def read(self, ctx: ResourceContext) -> EnvVariablesState:
        if not ctx.config:
            raise DataSourceError("Configuration is required.")
        config = cast(EnvVariablesConfig, ctx.config)
        logger.debug(
            "Reading environment variables",
            keys=config.keys,
            prefix=config.prefix,
            regex=config.regex,
        )
        exclude_empty = config.exclude_empty is not False
        case_sensitive = config.case_sensitive is not False
        source_vars = os.environ.copy()
        filtered_vars = {}
        if config.keys is not None:
            for key in config.keys:
                if (value := source_vars.get(key)) is not None:
                    if exclude_empty and not value:
                        continue
                    filtered_vars[key] = value
        elif config.prefix is not None:
            prefix_to_match = config.prefix if case_sensitive else config.prefix.lower()
            for key, value in source_vars.items():
                key_to_check = key if case_sensitive else key.lower()
                if key_to_check.startswith(prefix_to_match):
                    if exclude_empty and not value:
                        continue
                    filtered_vars[key] = value
        elif config.regex is not None:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_regex = re.compile(config.regex, flags)
                for key, value in source_vars.items():
                    if compiled_regex.match(key):
                        if exclude_empty and not value:
                            continue
                        filtered_vars[key] = value
            except re.error as e:
                context = capture_error_context(
                    e,
                    category="validation",
                    operation="regex_compile",
                    regex_pattern=config.regex,
                    case_sensitive=case_sensitive,
                )
                raise DataSourceError(
                    f"Invalid regex provided: {e}. Context: {context}"
                ) from e
        else:
            for key, value in source_vars.items():
                if exclude_empty and not value:
                    continue
                filtered_vars[key] = value
        transformed_vars = {}
        for key, value in filtered_vars.items():
            final_key = (
                key.upper()
                if config.transform_keys == "upper"
                else (key.lower() if config.transform_keys == "lower" else key)
            )
            final_value = (
                value.upper()
                if config.transform_values == "upper"
                else (value.lower() if config.transform_values == "lower" else value)
            )
            transformed_vars[final_key] = final_value
        sensitive_keys_set = set(config.sensitive_keys or [])
        sensitive_vals = {
            k: v for k, v in transformed_vars.items() if k in sensitive_keys_set
        }
        non_sensitive_vals = {
            k: v for k, v in transformed_vars.items() if k not in sensitive_keys_set
        }
        return EnvVariablesState(
            values=non_sensitive_vals,
            sensitive_values=sensitive_vals,
            all_values=transformed_vars,
            all_environment=source_vars,
        )


# 🌍🔤📊
