from __future__ import annotations

from typing import List

import pytest
from pydantic import BaseModel

from agno.models.message import Message
from agno.models.response import ModelResponse
from agno.models.openai.like import OpenAILike

from dashscope import DashScope


class UserSchema(BaseModel):
    name: str
    age: int


@pytest.fixture()
def dashscope_model() -> DashScope:
    return DashScope(api_key="test-key")


def test_default_base_url_uses_intl_endpoint() -> None:
    model = DashScope(api_key="test-key")
    assert model.base_url == model._SINGAPORE_ENDPOINT


def test_china_region_uses_domestic_endpoint() -> None:
    model = DashScope(api_key="test-key", region="cn")
    assert model.base_url == model._CHINA_ENDPOINT


def test_ensure_json_hint_adds_system_message(dashscope_model: DashScope) -> None:
    messages = [Message(role="user", content="你好，请帮我总结一下")]
    response_format = {"type": "json_object"}

    result = dashscope_model._ensure_json_hint(messages, response_format)

    assert result[0].role == "system"
    assert "json" in result[0].content.lower()
    assert result[1:] == messages


def test_ensure_json_hint_keeps_existing_json_message(dashscope_model: DashScope) -> None:
    messages = [Message(role="user", content="请以 JSON 格式回答")]
    response_format = {"type": "json_object"}

    result = dashscope_model._ensure_json_hint(messages, response_format)

    assert result == messages


def test_ensure_json_hint_with_pydantic_schema(dashscope_model: DashScope) -> None:
    messages = [Message(role="user", content="提取用户姓名和年龄")]
    response_format = UserSchema

    result = dashscope_model._ensure_json_hint(messages, response_format)

    assert result[0].role == "system"
    assert "json" in result[0].content.lower()
    assert result[1:] == messages


def test_invoke_injects_json_hint(monkeypatch: pytest.MonkeyPatch, dashscope_model: DashScope) -> None:
    captured_messages: List[List[Message]] = []

    def fake_invoke(
        self: OpenAILike,
        messages: List[Message],
        assistant_message: Message,
        response_format,
        tools,
        tool_choice,
        run_response,
    ) -> ModelResponse:
        captured_messages.append(messages)
        return ModelResponse()

    monkeypatch.setattr(OpenAILike, "invoke", fake_invoke)

    original_messages = [Message(role="user", content="帮我整理信息")]
    assistant_message = Message(role="assistant")
    response_format = {"type": "json_object"}

    result = dashscope_model.invoke(
        original_messages,
        assistant_message,
        response_format=response_format,
        tools=None,
        tool_choice=None,
        run_response=None,
    )

    assert isinstance(result, ModelResponse)
    assert captured_messages
    hint_messages = captured_messages[0]
    assert hint_messages[0].role == "system"
    assert "json" in hint_messages[0].content.lower()
    assert hint_messages[1] == original_messages[0]


def test_invoke_stream_injects_json_hint(
    monkeypatch: pytest.MonkeyPatch, dashscope_model: DashScope
) -> None:
    captured_messages: List[List[Message]] = []

    def fake_invoke_stream(
        self: OpenAILike,
        messages: List[Message],
        assistant_message: Message,
        response_format,
        tools,
        tool_choice,
        run_response,
    ):
        captured_messages.append(messages)

        def generator():
            yield ModelResponse()

        return generator()

    monkeypatch.setattr(OpenAILike, "invoke_stream", fake_invoke_stream)

    original_messages = [Message(role="user", content="流式测试")]
    assistant_message = Message(role="assistant")
    response_format = {"type": "json_object"}

    stream = dashscope_model.invoke_stream(
        original_messages,
        assistant_message,
        response_format=response_format,
        tools=None,
        tool_choice=None,
        run_response=None,
    )

    chunks = list(stream)
    assert len(chunks) == 1
    assert isinstance(chunks[0], ModelResponse)
    hint_messages = captured_messages[0]
    assert hint_messages[0].role == "system"
    assert "json" in hint_messages[0].content.lower()
    assert hint_messages[1] == original_messages[0]


@pytest.mark.asyncio
async def test_ainvoke_injects_json_hint(monkeypatch: pytest.MonkeyPatch, dashscope_model: DashScope) -> None:
    captured_messages: List[List[Message]] = []

    async def fake_ainvoke(
        self: OpenAILike,
        messages: List[Message],
        assistant_message: Message,
        response_format,
        tools,
        tool_choice,
        run_response,
    ) -> ModelResponse:
        captured_messages.append(messages)
        return ModelResponse()

    monkeypatch.setattr(OpenAILike, "ainvoke", fake_ainvoke)

    original_messages = [Message(role="user", content="异步调用")]
    assistant_message = Message(role="assistant")
    response_format = {"type": "json_object"}

    result = await dashscope_model.ainvoke(
        original_messages,
        assistant_message,
        response_format=response_format,
        tools=None,
        tool_choice=None,
        run_response=None,
    )

    assert isinstance(result, ModelResponse)
    assert captured_messages
    hint_messages = captured_messages[0]
    assert hint_messages[0].role == "system"
    assert "json" in hint_messages[0].content.lower()
    assert hint_messages[1] == original_messages[0]


@pytest.mark.asyncio
async def test_ainvoke_stream_injects_json_hint(
    monkeypatch: pytest.MonkeyPatch, dashscope_model: DashScope
) -> None:
    captured_messages: List[List[Message]] = []

    async def fake_ainvoke_stream(
        self: OpenAILike,
        messages: List[Message],
        assistant_message: Message,
        response_format,
        tools,
        tool_choice,
        run_response,
    ):
        captured_messages.append(messages)

        async def generator():
            yield ModelResponse()

        return generator()

    monkeypatch.setattr(OpenAILike, "ainvoke_stream", fake_ainvoke_stream)

    original_messages = [Message(role="user", content="异步流式测试")]
    assistant_message = Message(role="assistant")
    response_format = {"type": "json_object"}

    stream = dashscope_model.ainvoke_stream(
        original_messages,
        assistant_message,
        response_format=response_format,
        tools=None,
        tool_choice=None,
        run_response=None,
    )

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) == 1
    assert isinstance(chunks[0], ModelResponse)
    hint_messages = captured_messages[0]
    assert hint_messages[0].role == "system"
    assert "json" in hint_messages[0].content.lower()
    assert hint_messages[1] == original_messages[0]
