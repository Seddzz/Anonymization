import asyncio

import pytest
from mcp.server.mcpserver.exceptions import UnexpectedToolError

from anonymizer.mcp_server import anonymize, detect, restore, server


def test_tools_are_registered():
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert {"detect", "anonymize", "restore"} <= names


def test_detect_returns_entities():
    entities = detect("Email a@b.com")
    assert any(entity["label"] == "EMAIL" for entity in entities)


def test_anonymize_and_restore_round_trip():
    result = anonymize("Email a@b.com from us")
    assert "[EMAIL_1]" in result["redacted"]
    restored = restore(result["mapping_id"], result["redacted"])
    assert restored["text"] == "Email a@b.com from us"


def test_anonymize_fake_strategy():
    result = anonymize("Email a@b.com", strategy="fake")
    assert "a@b.com" not in result["redacted"]


def test_restore_unknown_mapping_raises():
    with pytest.raises(ValueError, match="mapping not found"):
        restore("map_nope", "x")


def test_call_tool_returns_json():
    result = asyncio.run(server.call_tool("detect", {"text": "Email a@b.com"}))
    assert result.is_error is False
    text = "".join(item.text for item in result.content)
    assert "EMAIL" in text


def test_call_tool_unknown_mapping_raises():
    with pytest.raises(UnexpectedToolError):
        asyncio.run(
            server.call_tool("restore", {"mapping_id": "map_nope", "redacted": "x"})
        )
