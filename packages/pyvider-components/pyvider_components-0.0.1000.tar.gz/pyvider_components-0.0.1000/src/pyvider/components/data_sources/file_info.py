#
# pyvider/components/data_sources/file_info.py
#

# components/data_sources/file_info.py
import datetime
from pathlib import Path
import stat
from typing import cast

from attrs import define, field

from provide.foundation import logger
from provide.foundation.errors import capture_error_context, resilient
from provide.foundation.file import get_mtime, get_size
from pyvider.data_sources.base import BaseDataSource
from pyvider.data_sources.decorators import register_data_source
from pyvider.exceptions import DataSourceError
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_bool, a_num, a_str, s_data_source


@define(frozen=True)
class FileInfoConfig:
    path: str = field()


@define(frozen=True)
class FileInfoState:
    path: str = field()
    exists: bool = field(default=False)
    size: int = field(default=0)
    is_dir: bool = field(default=False)
    is_file: bool = field(default=False)
    is_symlink: bool = field(default=False)
    modified_time: str = field(default="")
    access_time: str = field(default="")
    creation_time: str = field(default="")
    permissions: str = field(default="")
    owner: str = field(default="")
    group: str = field(default="")
    mime_type: str = field(default="")


@register_data_source("pyvider_file_info")
class FileInfoDataSource(
    BaseDataSource["pyvider_file_info", FileInfoState, FileInfoConfig]
):
    config_class = FileInfoConfig
    state_class = FileInfoState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_data_source(
            {
                "path": a_str(required=True, description="Path to inspect."),
                "exists": a_bool(computed=True, description="Whether path exists."),
                "size": a_num(computed=True, description="Size in bytes."),
                "is_dir": a_bool(computed=True, description="Is it a directory."),
                "is_file": a_bool(computed=True, description="Is it a regular file."),
                "is_symlink": a_bool(
                    computed=True, description="Is it a symbolic link."
                ),
                "modified_time": a_str(
                    computed=True, description="Last modification time."
                ),
                "access_time": a_str(computed=True, description="Last access time."),
                "creation_time": a_str(computed=True, description="Creation time."),
                "permissions": a_str(computed=True, description="File permissions."),
                "owner": a_str(
                    computed=True,
                    description="Owner username, or numeric UID on non-Unix systems.",
                ),
                "group": a_str(
                    computed=True,
                    description="Group name, or numeric GID on non-Unix systems.",
                ),
                "mime_type": a_str(computed=True, description="MIME type."),
            }
        )

    @resilient()
    async def _validate_config(self, config: FileInfoConfig) -> list[str]:
        logger.debug("Validating file info config", path=config.path)
        return []

    @resilient()
    async def read(self, ctx: ResourceContext) -> FileInfoState:
        if not ctx.config:
            raise DataSourceError("Configuration is missing.")
        config = cast(FileInfoConfig, ctx.config)
        path = Path(config.path)

        if not path.exists():
            logger.debug("Path does not exist", path=config.path)
            return FileInfoState(path=config.path, exists=False)

        try:
            # Use provide-foundation utilities for safer file operations
            get_size(config.path)
            get_mtime(config.path)
            stat_info = path.stat()
        except (OSError, PermissionError) as e:
            context = capture_error_context(
                e, category="file_access", operation="stat", file_path=config.path
            )
            logger.warning(
                "Failed to access file", path=config.path, error=str(e), context=context
            )
            return FileInfoState(path=config.path, exists=True)
        logger.debug(
            "Reading file info",
            path=config.path,
            size=stat_info.st_size,
            is_dir=path.is_dir(),
        )
        owner, group = str(stat_info.st_uid), str(stat_info.st_gid)
        try:
            import pwd

            owner = pwd.getpwuid(stat_info.st_uid).pw_name
        except (ImportError, KeyError):
            pass
        try:
            import grp

            group = grp.getgrgid(stat_info.st_gid).gr_name
        except (ImportError, KeyError):
            pass

        mime_type = ""
        if path.is_file():
            try:
                import mimetypes

                mime_type = mimetypes.guess_type(config.path)[0] or ""
                logger.debug(
                    "Detected MIME type", path=config.path, mime_type=mime_type
                )
            except ImportError:
                logger.debug("mimetypes module not available")
                pass

        return FileInfoState(
            path=config.path,
            exists=True,
            size=stat_info.st_size,
            is_dir=path.is_dir(),
            is_file=path.is_file(),
            is_symlink=path.is_symlink(),
            modified_time=datetime.datetime.fromtimestamp(
                stat_info.st_mtime, tz=datetime.UTC
            ).isoformat(),
            access_time=datetime.datetime.fromtimestamp(
                stat_info.st_atime, tz=datetime.UTC
            ).isoformat(),
            creation_time=datetime.datetime.fromtimestamp(
                stat_info.st_ctime, tz=datetime.UTC
            ).isoformat(),
            permissions=oct(stat.S_IMODE(stat_info.st_mode)),
            owner=owner,
            group=group,
            mime_type=mime_type,
        )


# 📄ℹ️📊
