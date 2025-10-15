#
# tests/test_tdd_function_semantics.py
#

import pytest

from pyvider.components.functions.numeric_functions import add
from pyvider.components.functions.string_manipulation import lower, upper
from pyvider.conversion import unmarshal
from pyvider.cty import CtyNumber, CtyString, CtyValue


@pytest.mark.usefixtures("discovered_components_session")
class TestFunctionSemantics:
    """
    TDD: Verifies that core functions correctly handle unknown and null values,
    which is critical for go-cty compatibility.
    """

    # --- Unknown Value Tests ---

    @pytest.mark.asyncio
    async def test_add_with_unknown_operand_returns_unknown(self):
        """TDD: add(known, unknown) -> unknown"""
        from pyvider.conversion import marshal
        from pyvider.protocols.tfprotov6.handlers import CallFunctionHandler
        import pyvider.protocols.tfprotov6.protobuf as pb

        arg1 = marshal(10, schema=CtyNumber())
        arg2 = marshal(CtyValue.unknown(CtyNumber()), schema=CtyNumber())
        request = pb.CallFunction.Request(name="add", arguments=[arg1, arg2])

        response = await CallFunctionHandler(request, context=None)

        assert not response.error.text
        result_cty = unmarshal(response.result, schema=CtyNumber())
        assert result_cty.is_unknown

    @pytest.mark.asyncio
    async def test_upper_with_unknown_operand_returns_unknown(self):
        """TDD: upper(unknown) -> unknown"""
        from pyvider.conversion import marshal
        from pyvider.protocols.tfprotov6.handlers import CallFunctionHandler
        import pyvider.protocols.tfprotov6.protobuf as pb

        arg = marshal(CtyValue.unknown(CtyString()), schema=CtyString())
        request = pb.CallFunction.Request(name="upper", arguments=[arg])

        response = await CallFunctionHandler(request, context=None)
        assert not response.error.text
        result_cty = unmarshal(response.result, schema=CtyString())
        assert result_cty.is_unknown

    # --- Null Value Tests (These are synchronous tests) ---

    def test_add_with_null_operand_returns_null(self):
        """TDD: add(known, null) -> null"""
        result = add(10, None)
        assert result is None

    def test_upper_with_null_operand_returns_null(self):
        """TDD: upper(null) -> null"""
        result = upper(None)
        assert result is None

    def test_lower_with_null_operand_returns_null(self):
        """TDD: lower(null) -> null"""
        result = lower(None)
        assert result is None


# 🧪🎯📚
