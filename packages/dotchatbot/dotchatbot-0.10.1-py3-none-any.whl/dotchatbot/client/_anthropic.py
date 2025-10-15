from typing import Iterable

import anthropic
from anthropic.types import MessageParam
from anthropic.types import ModelParam
from anthropic.types import TextBlock

from dotchatbot.client.services import ServiceClient
from dotchatbot.input.transformer import Message


def _message_param(
    message: Message
) -> MessageParam:
    if message.role == "user":
        return MessageParam(
            content=message.content, role="user"
        )
    elif message.role == "assistant":
        return MessageParam(
            content=message.content, role="assistant"
        )
    else:
        raise ValueError(f"Invalid role: {message.role}")


class Anthropic(ServiceClient):
    def __init__(
        self,
        system_prompt: str,
        api_key: str,
        max_tokens: int,
        model: ModelParam
    ):
        super().__init__(system_prompt=system_prompt)
        self._model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.max_tokens = max_tokens

    async def create_chat_completion(self, messages: list[Message]) -> Message:
        messages: Iterable[MessageParam] = map(
            _message_param, messages
        )
        response = await self.client.messages.create(
            max_tokens=self.max_tokens, messages=messages, model=self._model
        )
        if not response.content or type(response.content[0]) is not TextBlock:
            raise ValueError(
                "Unexpected response: {}".format(response.content)
            )
        content = response.content[0].text
        role = response.role

        if not content:
            raise ValueError("Empty response")

        return Message(role=role, model=self.model(), content=content)

    def model(self) -> str:
        return self._model
