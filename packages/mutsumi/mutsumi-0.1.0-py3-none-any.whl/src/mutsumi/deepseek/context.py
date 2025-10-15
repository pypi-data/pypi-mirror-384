from typing import TYPE_CHECKING, Literal, Any, override

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from pydantic import BaseModel

from ..tool_set import ToolSet

if TYPE_CHECKING:
    from logging import Logger
    from .deepseek import Completions


__all__ = ["Context", "ContextWithTools", "Response"]


class Context:
    def __init__(
        self,
        ai: "Completions",
        logger: "Logger",
        system_prompt: str | None = None,
    ) -> None:
        self.ai = ai
        self.records: list[ChatCompletionMessageParam] = [
            {"content": i, "role": "system"} for i in (system_prompt,) if i
        ]
        self.logger = logger
        return

    def ask(
        self,
        msg: str,
        mode: Literal["chat", "reasoner"] = "chat",
    ):
        self.records.append({"role": "user", "content": msg})

        # log
        self.logger.info(">>> " + msg)

        raw_rsp = self.ai.create(
            messages=self.records,
            model="deepseek-" + mode,
            stream=False,
        )
        finish_reason = raw_rsp.choices[0].finish_reason
        rmsg = raw_rsp.choices[0].message

        rsp = Response.parseRawResponse(rmsg)
        self.records.append(rsp.toParam())

        # log
        if rsp.reasoning_content:
            self.logger.info("<?? " + rsp.reasoning_content)
        if rsp.content:
            self.logger.info("<<< " + rsp.content)
        if rsp.tool_calls:
            for i in rsp.tool_calls:
                self.logger.debug("<() " + str(i))
        return finish_reason, rsp


class ContextWithTools(Context):
    @override
    def __init__(
        self,
        ai: "Completions",
        logger: "Logger",
        tool_set: ToolSet,
        system_prompt: str | None = None,
    ) -> None:
        super().__init__(ai, logger, system_prompt)
        self.tool_set = tool_set
        return

    @override
    def ask(
        self,
        msg: str,
    ):
        self.records.append({"role": "user", "content": msg})

        # log
        self.logger.info(">>> " + msg)

        raw_rsp = self.ai.create(
            messages=self.records,
            model="deepseek-chat",
            tools=self.tool_set.toToolParam(),
            stream=False,
        )
        finish_reason = raw_rsp.choices[0].finish_reason
        rmsg = raw_rsp.choices[0].message

        rsp = Response.parseRawResponse(rmsg)
        self.records.append(rsp.toParam())

        # log
        if rsp.reasoning_content:
            self.logger.info("<?? " + rsp.reasoning_content)
        if rsp.content:
            self.logger.info("<<< " + rsp.content)
        if rsp.tool_calls:
            for i in rsp.tool_calls:
                self.logger.debug("<() " + str(i))

        return finish_reason, rsp

    def sendToolCallRetvals(
        self,
        values: list[tuple[str, Any]],
    ):
        for v in values:
            self.records.append(
                {
                    "role": "tool",
                    "tool_call_id": v[0],
                    "content": v[1],
                }
            )
            self.logger.debug(">() " + f"id='{v[0]}' retval='{v[1]}'")

        raw_rsp = self.ai.create(
            messages=self.records,
            model="deepseek-chat",
            tools=self.tool_set.toToolParam(),
            stream=False,
        )
        finish_reason = raw_rsp.choices[0].finish_reason

        rsp = Response.parseRawResponse(raw_rsp.choices[0].message)
        self.records.append(rsp.toParam())

        # log
        if rsp.reasoning_content:
            self.logger.info("<?? " + rsp.reasoning_content)
        if rsp.content:
            self.logger.info("<<< " + rsp.content)
        if rsp.tool_calls:
            for i in rsp.tool_calls:
                self.logger.debug("<() " + str(i))

        return finish_reason, rsp


class Response(BaseModel):
    content: str | None
    reasoning_content: str | None
    tool_calls: list["ToolCall"]

    @classmethod
    def parseRawResponse(cls, rmsg: ChatCompletionMessage):

        if rmsg.model_extra is None or (
            "reasoning_content" not in rmsg.model_extra.keys()
        ):
            reasoning_content = None
        else:
            reasoning_content = rmsg.model_extra["reasoning_content"]
            assert isinstance(reasoning_content, str) or reasoning_content is None

        if rmsg.tool_calls is None:
            tool_calls = []
        else:
            tool_calls: list[ToolCall] = []
            for f in rmsg.tool_calls:
                if not isinstance(f, ChatCompletionMessageToolCall):
                    raise TypeError(
                        f"type '{"ChatCompletionMessageToolCall"}' expected, {type(f)} gotten."
                    )
                id = f.id
                func_name = f.function.name
                func_argu = f.function.arguments
                tool_calls.append(
                    ToolCall(
                        id=id,
                        name=func_name,
                        arguments=func_argu,
                    )
                )
        return cls(
            content=rmsg.content,
            reasoning_content=reasoning_content,
            tool_calls=tool_calls,
        )

    def toParam(self) -> ChatCompletionAssistantMessageParam:
        return {
            "role": "assistant",
            "content": self.content,
            "tool_calls": (
                None
                if not (self.tool_calls)
                else [
                    {
                        "id": i.id,
                        "type": "function",
                        "function": {
                            "name": i.name,
                            "arguments": i.arguments,
                        },
                    }
                    for i in self.tool_calls
                ]
            ),  # type: ignore
        }


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str
