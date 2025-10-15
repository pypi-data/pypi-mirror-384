#
# pyvider/components/resources/timed_token.py
#

import datetime
from typing import Any
import uuid

from attrs import define, evolve

from provide.foundation import logger
from pyvider.resources.base import BaseResource
from pyvider.resources.context import ResourceContext
from pyvider.resources.decorators import register_resource
from pyvider.resources.private_state import PrivateState
from pyvider.schema.factory import a_str, a_unknown, s_resource
from pyvider.schema.types import PvsSchema


@define(frozen=True)
class TimedTokenConfig:
    name: str


@define(frozen=True)
class TimedTokenState:
    name: str | None = None
    id: str | None = None
    token: str | None = None
    expires_at: str | None = None


@define(frozen=True)
class TimedTokenPrivateState(PrivateState):
    token: str
    expires_at: str


@register_resource("pyvider_timed_token")
class TimedTokenResource(
    BaseResource["pyvider_timed_token", TimedTokenState, TimedTokenConfig]
):
    config_class = TimedTokenConfig
    state_class = TimedTokenState
    private_state_class = TimedTokenPrivateState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_resource(
            {
                "name": a_str(required=True),
                "id": a_str(computed=True),
                "token": a_str(computed=True, sensitive=True),
                "expires_at": a_str(computed=True, sensitive=True),
            }
        )

    async def _validate_config(self, config: TimedTokenConfig) -> list[str]:
        return []

    async def _create(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any], TimedTokenPrivateState]:
        base_plan["id"] = a_unknown(a_str())
        base_plan["token"] = a_unknown(a_str())
        base_plan["expires_at"] = a_unknown(a_str())

        private_state = self.private_state_class(
            token=f"token-{uuid.uuid4()}",
            expires_at=(
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
            ).isoformat(),
        )
        logger.debug(f"Creating private state: {private_state}")
        return base_plan, private_state

    async def _create_apply(
        self, ctx: ResourceContext
    ) -> tuple[TimedTokenState, TimedTokenPrivateState]:
        # Evolve the planned state, filling in the computed value for 'id'.
        final_state = evolve(
            ctx.planned_state,
            id=f"timed-token-id-{uuid.uuid4()}",
            token=ctx.private_state.token,
            expires_at=ctx.private_state.expires_at,
        )
        return final_state, ctx.private_state

    async def read(self, ctx: ResourceContext) -> TimedTokenState | None:
        logger.debug(f"Read method called. ctx.private_state: {ctx.private_state}")
        if ctx.private_state and ctx.state:
            # Private state is automatically decrypted by the framework
            # Just use the values directly from the private state
            return evolve(
                ctx.state,
                token=ctx.private_state.token,
                expires_at=ctx.private_state.expires_at,
            )
        return ctx.state

    async def _delete_apply(self, ctx: ResourceContext) -> None:
        pass


# ⏰🎟️🔑
