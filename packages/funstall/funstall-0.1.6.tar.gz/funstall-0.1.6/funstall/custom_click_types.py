from typing import Any

from click import Context, Parameter, ParamType


class _StringListParamType(ParamType):
    name = "list of strings"

    def convert(
        self,
        value: Any,
        param: Parameter | None,
        ctx: Context | None,
    ) -> list[str]:
        if not isinstance(value, str):
            self.fail("invalid value")
        return value.split(",")


string_list = _StringListParamType()
