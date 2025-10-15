#
# pyvider/components/functions/type_conversion_functions.py
#

from typing import Any

from provide.foundation import logger
from pyvider.hub import register_function


@register_function(name="tostring", summary="Explicitly converts a value to a string.")
def tostring(value: Any | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        result = "true" if value else "false"
        logger.debug("Converted boolean to string", original_value=value, result=result)
        return result
    result = str(value)
    logger.debug(
        "Converted value to string",
        value_type=type(value).__name__,
        result_length=len(result),
    )
    return result


# 🔄🏷️🎯
