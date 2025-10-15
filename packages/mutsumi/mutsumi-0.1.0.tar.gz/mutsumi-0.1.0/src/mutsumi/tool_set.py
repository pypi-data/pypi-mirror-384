from collections.abc import Callable, Iterable
from copy import deepcopy
from typing import final

from openai.types.chat import (
    ChatCompletionToolUnionParam,
    ChatCompletionFunctionToolParam,
)

__all__ = ["ToolSet", "cvtFuncToParam"]


class ToolSet:
    def __init__(self, tools: Iterable[Callable[..., str]]):
        self.__tool_map: dict[str, Callable[..., str]] = {i.__name__: i for i in tools}
        self.__cache_avaliable_tool_names: list[str] | None = None
        self.__cache_tool_param: list[ChatCompletionToolUnionParam] | None = None
        return

    @final
    def getAvaliableToolNames(self) -> Iterable[str]:
        if self.__cache_avaliable_tool_names is None:
            self.__cache_avaliable_tool_names = list(self.__tool_map.keys())
        return deepcopy(self.__cache_avaliable_tool_names)

    @final
    def getToolByName(self, name: str) -> Callable[..., str] | None:
        return self.__tool_map.get(name)

    @final
    def toToolParam(self) -> list[ChatCompletionToolUnionParam]:
        if self.__cache_tool_param is None:
            self.__cache_tool_param = [
                cvtFuncToParam(v) for v in self.__tool_map.values()
            ]
        return deepcopy(self.__cache_tool_param)

    def __or__(self, value: "ToolSet") -> "ToolSet":
        sum_tool_map = self.__tool_map | value.__tool_map
        retval = ToolSet([])
        retval.__tool_map = sum_tool_map
        return retval


def cvtFuncToParam(f: Callable[..., str]) -> ChatCompletionFunctionToolParam:
    assert f.__doc__
    arg_cnt = len([i for i in f.__annotations__.keys() if i != "return"])
    arg_nodefault_cnt = arg_cnt - (0 if f.__defaults__ is None else len(f.__defaults__))
    return {
        "type": "function",
        "function": {
            "name": f.__name__,
            "description": f.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    k: {
                        "type": {
                            str: "string",
                            float: "number",
                            int: "integer",
                            bool: "boolen",
                        }.get(type(k), "object")
                    }
                    for k in f.__annotations__.keys()
                    if k != "return"
                },
                "required": [
                    k
                    for i, k in enumerate(f.__annotations__.keys())
                    if (k != "return" and i < arg_nodefault_cnt)
                ],
            },
        },
    }
