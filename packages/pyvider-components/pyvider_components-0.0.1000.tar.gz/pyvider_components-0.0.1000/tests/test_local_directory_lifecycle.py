#
# tests/test_local_directory_lifecycle.py
#

from pathlib import Path
import shutil

import pytest

from pyvider.components.resources.local_directory import (
    LocalDirectoryConfig,
    LocalDirectoryResource,
    LocalDirectoryState,
)
from pyvider.resources.context import ResourceContext


@pytest.fixture
def temp_dir() -> Path:
    path = Path("/tmp/pyvider_test_dir")
    if path.exists():
        shutil.rmtree(path)
    yield path
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture
def resource() -> LocalDirectoryResource:
    return LocalDirectoryResource()


@pytest.mark.asyncio
async def test_create_lifecycle_contract(
    resource: LocalDirectoryResource, temp_dir: Path
):
    # 1. Define the configuration with the CANONICAL format.
    config = LocalDirectoryConfig(path=str(temp_dir), permissions="0o775")
    create_context = ResourceContext(config=config, state=None)
    base_plan = {"path": config.path, "permissions": config.permissions}

    # 2. Get the plan.
    planned_state_dict, _ = await resource._create(create_context, base_plan)
    planned_state = resource.state_class(**planned_state_dict)

    # 3. Assert the plan matches the config exactly.
    assert isinstance(planned_state, LocalDirectoryState)
    assert planned_state.path == str(temp_dir)
    assert planned_state.permissions == "0o775"
    assert planned_state.id == str(temp_dir.resolve())
    assert planned_state.file_count == 0

    # 4. Apply the plan.
    apply_context = ResourceContext(config=config, planned_state=planned_state)
    final_state, _ = await resource._create_apply(apply_context)

    # 5. The final state must be identical to the planned state.
    assert final_state == planned_state

    # 6. Verify the real world.
    assert temp_dir.exists()
    assert oct(temp_dir.stat().st_mode & 0o777) == "0o775"

    # 7. Verify the read operation.
    read_context = ResourceContext(config=None, state=final_state)
    read_state = await resource.read(read_context)
    assert read_state is not None
    assert read_state.permissions == "0o775"


# 🧪📁🔄
