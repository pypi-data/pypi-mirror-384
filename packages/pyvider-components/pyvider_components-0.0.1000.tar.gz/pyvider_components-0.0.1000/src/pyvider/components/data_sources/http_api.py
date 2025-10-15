#
# pyvider/components/data_sources/http_api.py
#

from decimal import Decimal
from typing import cast

from attrs import define

from provide.foundation import logger
from provide.foundation.transport import HTTPMethod, request
from provide.foundation.transport.errors import (
    HTTPResponseError,
    TransportConnectionError,
    TransportTimeoutError,
)
from pyvider.data_sources.base import BaseDataSource
from pyvider.data_sources.decorators import register_data_source
from pyvider.exceptions import DataSourceError
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_map, a_num, a_str, s_data_source


@define(frozen=True)
class HTTPAPIConfig:
    url: str
    method: str = "GET"
    headers: dict[str, str] | None = None
    timeout: int | Decimal = 30


@define(frozen=True)
class HTTPAPIState:
    url: str
    method: str
    status_code: int | None = None
    response_body: str = ""  # Always a string, empty on error to avoid null issues
    response_time_ms: int | None = None
    response_headers: dict[str, str] | None = None
    header_count: int | None = None
    content_type: str | None = None
    error_message: str | None = None


@register_data_source("pyvider_http_api")
class HTTPAPIDataSource(
    BaseDataSource["pyvider_http_api", HTTPAPIState, HTTPAPIConfig]
):
    config_class = HTTPAPIConfig
    state_class = HTTPAPIState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_data_source(
            {
                "url": a_str(required=True),
                "method": a_str(optional=True),
                "headers": a_map(a_str(), optional=True),
                "timeout": a_num(optional=True),
                "status_code": a_num(computed=True, optional=True),
                "response_body": a_str(computed=True, optional=True),
                "response_time_ms": a_num(computed=True, optional=True),
                "response_headers": a_map(a_str(), computed=True, optional=True),
                "header_count": a_num(computed=True, optional=True),
                "content_type": a_str(computed=True, optional=True),
                "error_message": a_str(computed=True, optional=True),
            }
        )

    async def _validate_config(self, config: HTTPAPIConfig) -> list[str]:
        """Enhanced config validation using provide-foundation utilities."""
        errors = []

        # Validate HTTP method using foundation HTTPMethod
        try:
            HTTPMethod(config.method.upper())
        except ValueError as e:
            errors.append(f"Invalid HTTP method '{config.method}': {e}")

        # Validate URL format
        if not config.url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")

        # Validate timeout
        if config.timeout <= 0:
            errors.append("Timeout must be greater than 0")
        elif config.timeout > 300:  # 5 minutes max
            errors.append("Timeout cannot exceed 300 seconds")

        logger.debug(
            "HTTP API config validation",
            errors=len(errors),
            method=config.method,
            url=config.url,
        )
        return errors

    async def _make_http_request(self, config: HTTPAPIConfig):
        """Make HTTP request using provide-foundation transport."""
        try:
            response = await request(
                method=HTTPMethod(config.method.upper()),
                uri=config.url,  # Fixed: provide.foundation.transport uses 'uri' not 'url'
                headers=config.headers or {},
                timeout=float(config.timeout),
            )
            return response
        except (TransportConnectionError, TransportTimeoutError) as e:
            # Foundation transport already includes retry logic
            raise DataSourceError(f"HTTP request failed: {e}") from e

    async def read(self, ctx: ResourceContext) -> HTTPAPIState:
        config = cast(HTTPAPIConfig, ctx.config)
        if not config:
            raise DataSourceError("Configuration is missing.")

        try:
            response = await self._make_http_request(config)

            return HTTPAPIState(
                url=config.url,  # Use original URL from config
                method=config.method,  # Use original method from config
                status_code=response.status,  # Foundation transport uses 'status'
                response_body=response.text,  # Foundation transport has text property
                response_time_ms=int(
                    response.elapsed_ms
                ),  # Foundation transport tracks elapsed_ms
                response_headers=response.headers,  # Foundation transport headers are already dict
                header_count=len(response.headers),
                content_type=response.headers.get("content-type"),
            )
        except (
            TransportConnectionError,
            TransportTimeoutError,
            HTTPResponseError,
        ) as e:
            logger.error(f"HTTP request failed: {e}", exc_info=True)
            return HTTPAPIState(
                url=config.url, method=config.method, error_message=str(e)
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during HTTP request: {e}", exc_info=True
            )
            return HTTPAPIState(
                url=config.url,
                method=config.method,
                error_message=f"Unexpected error: {e}",
            )


# 🌐📡📊
