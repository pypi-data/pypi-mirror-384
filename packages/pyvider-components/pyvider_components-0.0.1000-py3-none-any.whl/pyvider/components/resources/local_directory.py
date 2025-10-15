#
# pyvider/components/resources/local_directory.py
#

from pathlib import Path
from typing import Any, cast

from attrs import define

from provide.foundation import logger
from provide.foundation.errors import resilient
from pyvider.common.types import StateType
from pyvider.exceptions import ResourceError
from pyvider.hub import register_resource
from pyvider.resources.base import BaseResource
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_num, a_str, s_resource


@define(frozen=True)
class LocalDirectoryConfig:
    path: str
    permissions: str | None = None


@define(frozen=True)
class LocalDirectoryState:
    path: str
    permissions: str | None = None
    id: str | None = None
    file_count: int | None = None


@register_resource("pyvider_local_directory")
class LocalDirectoryResource(
    BaseResource["pyvider_local_directory", LocalDirectoryState, LocalDirectoryConfig]
):
    config_class = LocalDirectoryConfig
    state_class = LocalDirectoryState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_resource(
            {
                "path": a_str(
                    required=True, description="The path of the directory to manage."
                ),
                "permissions": a_str(
                    optional=True,
                    computed=True,
                    description="The permissions for the directory in octal format. Must start with '0o' (e.g., '0o755').",
                ),
                "id": a_str(
                    computed=True, description="The absolute path of the directory."
                ),
                "file_count": a_num(
                    computed=True, description="The number of files in the directory."
                ),
            }
        )

    @resilient()
    async def _validate_config(self, config: LocalDirectoryConfig) -> list[str]:
        if config.permissions:
            is_valid = config.permissions.startswith("0o") and all(
                c in "01234567" for c in config.permissions[2:]
            )
            if not is_valid:
                logger.debug(
                    "Invalid permissions format",
                    permissions=config.permissions,
                    expected_format="0o755",
                )
                return [
                    f"The value '{config.permissions}' is not a valid octal string. It must be prefixed with '0o', for example: '0o755'."
                ]
        logger.debug("Configuration validation passed", permissions=config.permissions)
        return []

    async def _create(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, None]:
        config = cast(LocalDirectoryConfig, ctx.config)
        if not config:
            return None, None

        base_plan["permissions"] = config.permissions or "0o755"
        base_plan["id"] = str(Path(config.path).resolve())
        base_plan["file_count"] = 0

        return base_plan, None

    async def _update(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, None]:
        config = cast(LocalDirectoryConfig, ctx.config)
        if not config:
            return None, None
        base_plan["permissions"] = config.permissions or "0o755"
        return base_plan, None

    @resilient()
    async def _create_apply(
        self, ctx: ResourceContext
    ) -> tuple[StateType | None, None]:
        planned_state = cast(LocalDirectoryState, ctx.planned_state)
        path = Path(planned_state.path)
        logger.debug("Creating directory", path=str(path))
        path.mkdir(parents=True, exist_ok=True)
        try:
            path.chmod(int(planned_state.permissions, 8))
            logger.debug(
                "Set directory permissions",
                path=str(path),
                permissions=planned_state.permissions,
            )
        except (ValueError, TypeError) as e:
            raise ResourceError(
                f"Invalid permissions format: {planned_state.permissions}. Must be an octal string like '0o755'."
            ) from e
        return ctx.planned_state, None

    async def _update_apply(
        self, ctx: ResourceContext
    ) -> tuple[StateType | None, None]:
        return await self._create_apply(ctx)

    @resilient()
    async def read(self, ctx: ResourceContext) -> LocalDirectoryState | None:
        if not ctx.state or not ctx.state.path:
            logger.debug("No state or path provided for read operation")
            return None
        path = Path(ctx.state.path)
        if not path.is_dir():
            logger.debug("Path is not a directory or doesn't exist", path=str(path))
            return None
        current_permissions = "0o" + oct(path.stat().st_mode & 0o777)[2:]
        file_count = len([f for f in path.iterdir() if f.is_file()])
        logger.debug(
            "Read directory state",
            path=str(path),
            permissions=current_permissions,
            file_count=file_count,
        )
        return self.state_class(
            path=str(path),
            permissions=current_permissions,
            id=str(path.resolve()),
            file_count=file_count,
        )

    async def _delete_apply(self, ctx: ResourceContext) -> None:
        state = cast(LocalDirectoryState, ctx.state)
        if not state or not state.path:
            return
        path = Path(state.path)
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                logger.warning(
                    f"Directory {path} is not empty and will not be removed."
                )


# 📁🏠📂
