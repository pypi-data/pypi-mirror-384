#
# tests/test_resource_lifecycle_contract.py
#

import hashlib

import pytest

from pyvider.components.resources.file_content import (
    FileContentConfig,
    FileContentResource,
    FileContentState,
)
from pyvider.resources.context import ResourceContext


class TestResourceLifecycleContract:
    """
    TDD: These tests enforce the correct implementation of the Terraform
    resource lifecycle contract.
    """

    @pytest.mark.asyncio
    async def test_plan_matches_apply_result(self):
        """
        Verifies that the state returned by 'apply' is identical to the
        state proposed by 'plan' for a create operation.
        """
        resource = FileContentResource()
        config = FileContentConfig(filename="/tmp/test.txt", content="contract test")

        plan_ctx = ResourceContext(config=config)
        base_plan = {"filename": config.filename, "content": config.content}
        planned_state_dict, _ = await resource._create(plan_ctx, base_plan)
        planned_state = resource.state_class(**planned_state_dict)

        apply_ctx = ResourceContext(config=config, planned_state=planned_state)
        applied_state, _ = await resource._create_apply(apply_ctx)

        # The state returned by apply MUST be identical to the state from plan.
        assert planned_state == applied_state

    @pytest.mark.asyncio
    async def test_plan_correctly_predicts_computed_values_for_create(self):
        """
        Verifies that for a new resource, the 'plan' method correctly
        predicts all computed values.
        """
        resource = FileContentResource()
        config = FileContentConfig(filename="/tmp/test.txt", content="new file")
        ctx = ResourceContext(config=config, state=None)
        base_plan = {"filename": config.filename, "content": config.content}

        planned_state_dict, _ = await resource._create(ctx, base_plan)
        planned_state = resource.state_class(**planned_state_dict)

        # The plan MUST include the predicted values for computed attributes.
        assert planned_state.exists is True
        assert planned_state.content_hash == hashlib.sha256(b"new file").hexdigest()

    @pytest.mark.asyncio
    async def test_plan_correctly_predicts_computed_values_for_update(self):
        """
        Verifies that for a resource update, the 'plan' method
        correctly predicts the new computed values based on the config change.
        """
        resource = FileContentResource()
        prior_state = FileContentState(
            filename="/tmp/test.txt",
            content="old content",
            exists=True,
            content_hash="old_hash",
        )
        config = FileContentConfig(filename="/tmp/test.txt", content="updated content")
        ctx = ResourceContext(config=config, state=prior_state)
        base_plan = {"filename": config.filename, "content": config.content}

        planned_state_dict, _ = await resource._update(ctx, base_plan)
        planned_state = resource.state_class(**planned_state_dict)

        assert planned_state.content == "updated content"
        assert (
            planned_state.content_hash == hashlib.sha256(b"updated content").hexdigest()
        )
        assert planned_state.exists is True


# 🧪🔄📋
