#
# pyvider/components/functions/lens_jq.py
#

from typing import Any

from pyvider.cty import CtyValue
from pyvider.cty.conversion import cty_to_native
from pyvider.exceptions import FunctionError
from pyvider.hub import register_function

from ..capabilities.lens import LensCapability


@register_function(name="lens_jq", component_of="lens")
def lens_jq(input_data: Any, query: str, *, lens: LensCapability) -> Any:
    """Applies a jq query and returns a native Python object."""
    from provide.foundation import logger

    logger.debug(
        f"🔧 LENS_JQ_FUNCTION called with input_data={type(input_data)}, query={query!r}, lens={type(lens)}"
    )

    if not lens.is_enabled:
        raise FunctionError(
            "The 'lens' capability is disabled in the provider configuration."
        )

    if not isinstance(query, str) or not query:
        raise FunctionError("The 'query' argument must be a non-empty string.")

    # Ensure input_data is converted to native Python before passing to JQ
    if isinstance(input_data, CtyValue):
        # If it's a CTY value, convert it to native Python first
        native_input_data = cty_to_native(input_data)
    else:
        # Assume it's already native Python data
        native_input_data = input_data

    logger.debug(
        f"🔧 LENS_JQ_FUNCTION calling lens.jq({query!r}, {type(native_input_data)})"
    )
    logger.debug(
        f"🔧 LENS_JQ_FUNCTION native_input_data preview: {str(native_input_data)[:200]}..."
    )
    try:
        logger.debug(
            f"🔧 LENS_JQ_FUNCTION about to call lens.jq with args: query={query!r}, input_data={native_input_data}"
        )
        logger.debug(f"🔧 LENS_JQ_FUNCTION lens object: {lens}, type: {type(lens)}")
        result_cty = lens.jq(query, native_input_data)
        logger.debug(
            f"🔧 LENS_JQ_FUNCTION lens.jq returned: {type(result_cty)} = {result_cty}"
        )
        result = cty_to_native(result_cty)
        logger.debug(f"🔧 LENS_JQ_FUNCTION final result: {type(result)} = {result}")
        return result
    except Exception as jq_err:
        logger.error(
            f"🔧 LENS_JQ_FUNCTION error in JQ processing: {jq_err}", exc_info=True
        )
        raise


# 🔍🔧📊
