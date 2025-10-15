#
# pyvider/components/resources/warning_example.py
#

from typing import Any

from attrs import define

from pyvider.hub import register_resource
from pyvider.resources.base import BaseResource
from pyvider.resources.context import ResourceContext
from pyvider.schema import PvsSchema, a_str, a_unknown, s_resource


@define(frozen=True)
class WarningExampleState:
    name: str | None = None
    old_name: str | None = None
    source_file: str | None = None


@register_resource("pyvider_warning_example")
class WarningExampleResource(BaseResource):
    state_class = WarningExampleState
    config_class = WarningExampleState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_resource(
            {
                "name": a_str(optional=True, computed=True),
                "old_name": a_str(optional=True, deprecated=True),
                "source_file": a_str(optional=True),
            }
        )

    async def _validate_config(self, config: WarningExampleState) -> list[str]:
        errors = []
        if config.name is not None and config.source_file is not None:
            errors.append("'name' and 'source_file' are mutually exclusive.")
        if (
            config.name is None
            and config.old_name is None
            and config.source_file is None
        ):
            errors.append(
                "One of 'name', 'old_name', or 'source_file' must be specified."
            )
        return errors

    async def _create(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any], None]:
        config = ctx.config
        if config.old_name is not None:
            ctx.add_attribute_warning(
                attribute_path="old_name",
                summary="Attribute 'old_name' is deprecated",
                detail="Please use the 'name' attribute instead.",
            )

        planned_name = config.name or config.old_name
        if config.source_file:
            planned_name = f"from_file:{config.source_file}"

        if planned_name is None:
            base_plan["name"] = a_unknown(a_str())
        else:
            base_plan["name"] = planned_name

        return base_plan, None

    async def _create_apply(
        self, ctx: ResourceContext
    ) -> tuple[WarningExampleState, None]:
        final_state = self.state_class(
            name=ctx.planned_state.name,
            old_name=ctx.planned_state.old_name,
            source_file=ctx.planned_state.source_file,
        )
        return final_state, None

    async def read(self, ctx: ResourceContext) -> WarningExampleState | None:
        return ctx.state

    async def _delete_apply(self, ctx: ResourceContext) -> None:
        pass


# ⚠️💡📚
