#
# pyvider/components/capabilities/api.py
#

from pyvider.capabilities import BaseCapability, register_capability
from pyvider.schema import PvsAttribute, a_bool, a_map, a_num, a_str


class AbstractApiCapability(BaseCapability):
    """
    Provides a standard set of API configuration attributes for a provider.
    """

    @staticmethod
    def get_schema_contribution() -> dict[str, PvsAttribute]:
        return {
            "api_endpoint": a_str(
                optional=True, description="The base URL for the API endpoint."
            ),
            "api_token": a_str(
                optional=True,
                sensitive=True,
                description="The authentication token for the API.",
            ),
            "api_timeout": a_num(
                optional=True,
                default=30,
                description="Timeout in seconds for API requests.",
            ),
            "api_retries": a_num(
                optional=True,
                default=3,
                description="Number of retries for failed API requests.",
            ),
            "api_insecure_skip_verify": a_bool(
                optional=True,
                default=False,
                description="If true, TLS certificate verification is skipped.",
            ),
            "api_headers": a_map(
                element_type_def=a_str(),
                optional=True,
                description="Custom headers to send with every API request.",
            ),
        }


@register_capability("api")
class ApiCapability(AbstractApiCapability):
    """
    The Pyvider API capability.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# 🔌🌐🛠️
