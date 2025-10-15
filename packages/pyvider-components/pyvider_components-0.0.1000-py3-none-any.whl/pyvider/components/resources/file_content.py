#
# pyvider/components/resources/file_content.py
#

import hashlib
from pathlib import Path
from typing import Any, cast

from attrs import define, field

from provide.foundation import logger
from provide.foundation.errors import resilient
from provide.foundation.file import (
    atomic_write_text,
    ensure_dir,
    safe_delete,
    safe_read_text,
)
from pyvider.common.types import StateType
from pyvider.hub import register_resource
from pyvider.resources.base import BaseResource
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_bool, a_str, s_resource


@define(frozen=True)
class FileContentConfig:
    filename: str = field()
    content: str = field()


@define(frozen=True)
class FileContentState:
    filename: str = field()
    content: str = field()
    exists: bool | None = field(default=None)
    content_hash: str | None = field(default=None)


@register_resource("pyvider_file_content")
class FileContentResource(
    BaseResource["pyvider_file_content", FileContentState, FileContentConfig]
):
    config_class = FileContentConfig
    state_class = FileContentState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_resource(
            {
                "filename": a_str(required=True),
                "content": a_str(required=True),
                "exists": a_bool(computed=True),
                "content_hash": a_str(computed=True),
            }
        )

    async def _validate_config(self, config: FileContentConfig) -> list[str]:
        return []

    @resilient()
    async def read(self, ctx: ResourceContext) -> FileContentState | None:
        filename_to_read = (
            ctx.state.filename
            if ctx.state
            else (ctx.config.filename if ctx.config else None)
        )
        if not filename_to_read:
            logger.debug("No filename provided for read operation")
            return None
        path = Path(filename_to_read)
        if not path.is_file():
            logger.debug("File does not exist or is not a file", path=str(path))
            return None

        content = safe_read_text(path)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        logger.debug(
            "Read file content",
            filename=filename_to_read,
            content_length=len(content),
            content_hash=content_hash[:8],
        )
        return self.state_class(
            filename=filename_to_read,
            content=content,
            exists=True,
            content_hash=content_hash,
        )

    async def _create(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, None]:
        config = cast(FileContentConfig, ctx.config)
        if not config:
            return None, None

        base_plan["exists"] = True
        base_plan["content_hash"] = hashlib.sha256(
            config.content.encode("utf-8")
        ).hexdigest()

        return base_plan, None

    async def _update(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, None]:
        return await self._create(ctx, base_plan)

    @resilient()
    async def _create_apply(
        self, ctx: ResourceContext
    ) -> tuple[StateType | None, None]:
        planned_state = cast(FileContentState, ctx.planned_state)
        path = Path(planned_state.filename)
        logger.debug("Creating file", path=str(path))
        ensure_dir(path.parent)
        atomic_write_text(path, planned_state.content)
        logger.debug(
            "Successfully wrote file",
            path=str(path),
            content_length=len(planned_state.content),
        )
        return planned_state, None

    async def _update_apply(
        self, ctx: ResourceContext
    ) -> tuple[StateType | None, None]:
        return await self._create_apply(ctx)

    @resilient()
    async def _delete_apply(self, ctx: ResourceContext) -> None:
        state = cast(FileContentState, ctx.state)
        if not state or not state.filename:
            logger.debug("No state or filename provided for delete operation")
            return
        path = Path(state.filename)
        if path.is_file():
            logger.debug("Deleting file", path=str(path))
            safe_delete(path)
            logger.debug("Successfully deleted file", path=str(path))
        else:
            logger.debug("File does not exist, nothing to delete", path=str(path))


# 📄💾🔧
