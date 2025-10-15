#
# pyvider/components/capabilities/lens.py
#

from typing import Any

import jq

from provide.foundation import logger
from pyvider.capabilities import BaseCapability, register_capability
from pyvider.cty import CtyValue
from pyvider.cty.conversion import infer_cty_type_from_raw
from pyvider.exceptions import FunctionError
from pyvider.schema import PvsAttribute, a_bool, a_str


@register_capability("lens")
class LensCapability(BaseCapability):
    """
    Provides schema and services for enabling and configuring lens (jq) components.
    """

    def __init__(self, config: Any | None = None) -> None:
        super().__init__(config)
        self._config = config

    @property
    def is_enabled(self) -> bool:
        if self._config and hasattr(self._config, "lens_enabled"):
            return self._config.lens_enabled
        return True

    def jq(self, query: str, input_data: Any) -> CtyValue:
        """
        Executes a JQ query and converts the raw Python result to a CtyValue.
        """
        logger.debug(
            "⚙️ LENS-JQ ✅ Applying jq query via LensCapability service", query=query
        )
        try:
            # THE FIX: Use the correct `compile(...).transform(...)` API.
            compiled_query = jq.compile(query)
            final_raw_result = compiled_query.transform(input_data)

            inferred_type = infer_cty_type_from_raw(final_raw_result)
            return inferred_type.validate(final_raw_result)
        except Exception as e:
            logger.error(
                "⚙️ LENS-JQ ❌ JQ processing failed in capability",
                error=str(e),
                exc_info=True,
            )
            raise FunctionError(f"jq query failed: {e}") from e

    @staticmethod
    def get_schema_contribution() -> dict[str, PvsAttribute]:
        return {
            "lens_enabled": a_bool(
                optional=True,
                default=True,
                description="Enables or disables all lens (jq) related components.",
            ),
            "lens_jq_path": a_str(
                optional=True,
                description="Specifies a custom path to the 'jq' executable.",
            ),
        }


# 🔍👁️🛠️
