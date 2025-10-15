#
# pyvider/components/resources/private_state_verifier.py
#

from typing import Any

from attrs import define, evolve

from pyvider.exceptions import ResourceError
from pyvider.hub import register_resource
from pyvider.resources.base import BaseResource
from pyvider.resources.context import ResourceContext
from pyvider.resources.private_state import PrivateState
from pyvider.schema import PvsSchema, a_str, a_unknown, s_resource


@define(frozen=True)
class VerifierConfig:
    input_value: str


@define(frozen=True)
class VerifierState:
    input_value: str | None = None
    decrypted_token: str | None = None


@define(frozen=True)
class VerifierPrivateState(PrivateState):
    secret_token: str


@register_resource("pyvider_private_state_verifier")
class PrivateStateVerifierResource(BaseResource):
    config_class = VerifierConfig
    state_class = VerifierState
    private_state_class = VerifierPrivateState

    @classmethod
    def get_schema(cls) -> PvsSchema:
        return s_resource(
            {
                "input_value": a_str(required=True),
                "decrypted_token": a_str(computed=True),
            }
        )

    async def _validate_config(self, config: VerifierConfig) -> list[str]:
        return []

    async def _create(
        self, ctx: ResourceContext, base_plan: dict[str, Any]
    ) -> tuple[dict[str, Any], VerifierPrivateState]:
        base_plan["decrypted_token"] = a_unknown(a_str())
        private_state = self.private_state_class(
            secret_token=f"SECRET_FOR_{ctx.config.input_value.upper()}"
        )
        return base_plan, private_state

    async def _create_apply(self, ctx: ResourceContext) -> tuple[VerifierState, None]:
        if not ctx.private_state:
            raise ResourceError("Apply phase failed: private state was not received.")

        final_state = evolve(
            ctx.planned_state, decrypted_token=ctx.private_state.secret_token
        )
        return final_state, None

    async def read(self, ctx: ResourceContext) -> VerifierState | None:
        return ctx.state

    async def _delete_apply(self, ctx: ResourceContext) -> None:
        pass


# 🔒✅🛡️
