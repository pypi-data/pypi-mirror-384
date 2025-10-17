import pytest
import os

from pathlib import Path
from typing import List, Union
from src.opencode_client.session import (
    TextPart,
    FileSourceText,
    FileSource,
    FilePart,
    UserMessage,
    AssistantMessage,
    AssistantMessageInfo,
    AssistantMessageStepFinish,
    AssistantMessageStepStart,
    AssistantMessageStepWithText,
)
from src.opencode_client.custom_tools import CustomTool


def test_textpart_from_string() -> None:
    part = TextPart.from_string("hello")
    assert isinstance(part, TextPart)
    assert part.text == "hello"
    assert part.type == "text"


def test_filesourcetext_from_file(tmp_path: Path) -> None:
    file = tmp_path / "test.txt"
    file.write_text("abc123")

    fst = FileSourceText.from_file(str(file))
    assert isinstance(fst, FileSourceText)
    assert fst.start == 0
    assert fst.end == 6
    assert fst.value == "abc123"


def test_filesource_from_file(tmp_path: Path) -> None:
    file = tmp_path / "test.txt"
    file.write_text("xyz")

    fs = FileSource.from_file(str(file))
    assert isinstance(fs, FileSource)
    assert fs.path.endswith("test.txt")
    assert fs.text.value == "xyz"


def test_filepart_from_file_success(tmp_path: Path) -> None:
    file = tmp_path / "file.txt"
    file.write_text("some text")

    part = FilePart.from_file(str(file))
    assert isinstance(part, FilePart)
    assert part.mime.startswith("text/")
    assert part.filename == str(file)
    assert part.source.text.value == "some text"  # type: ignore


def test_filepart_from_file_nonexistent() -> None:
    with pytest.raises(ValueError):
        FilePart.from_file("no_such_file.txt")


def test_filepart_from_file_wrong_type(tmp_path: Path) -> None:
    file = tmp_path / "binfile.png"
    file.write_bytes(b"\x00\x01")

    with pytest.raises(ValueError, match="Unsopported type"):
        FilePart.from_file(str(file))


def test_filepart_from_url_success() -> None:
    part = FilePart.from_url("https://txt2html.sourceforge.net/sample.txt")
    assert isinstance(part, FilePart)
    assert part.mime.startswith("text/")


def test_filepart_from_url_failure() -> None:
    with pytest.raises(ValueError):
        FilePart.from_url("file.unknownext")


def test_usermessage_to_string_with_textpart() -> None:
    msg = UserMessage(modelID="m", providerID="p", parts=[TextPart.from_string("hi")])
    out = msg.to_string()
    assert "<text>hi</text>" in out


def test_usermessage_tools() -> None:
    if Path(".opencode/tool/say_hello.ts").exists():
        os.remove(".opencode/tool/say_hello.ts")
    custom_tool = CustomTool(
        name="Say Hello",
        description="this is a test",
        fn="return `Hello ${args.name}!`",
        args={
            "name": {
                "description": "name of the person to say hello to",
                "type": "string",
            }
        },
    )
    msg = UserMessage(
        modelID="m",
        providerID="p",
        parts=[TextPart.from_string("hi")],
        custom_tools=[custom_tool],
        tools={"bash": True},
    )
    assert msg.tools is not None
    assert len(msg.tools) == 2
    assert len(msg.custom_tools) == 0
    assert (
        Path(".opencode/tool/say_hello.ts").exists()
        and Path(".opencode/tool/say_hello.ts").is_file()
    )
    msg_dct = msg.to_dict()
    assert "custom_tools" not in msg_dct
    assert len(msg_dct.get("tools", {})) == 2
    assert "bash" in msg_dct.get("tools", {})
    assert "say_hello" in msg_dct.get("tools", {})
    assert msg_dct.get("tools", {}).get("say_hello")


def test_usermessage_from_dict() -> None:
    msg = {
        "modelID": "m",
        "providerID": "p",
        "parts": [TextPart.from_string("hi")],
    }
    user_msg = UserMessage.from_dict(msg)
    assert user_msg.custom_tools == []
    assert user_msg.modelID == "m"
    assert user_msg.providerID == "p"
    assert user_msg.parts == [TextPart.from_string("hi")]
    assert user_msg.system == ""
    assert user_msg.messageID == ""
    assert user_msg.mode == "build"
    assert user_msg.tools == {}


def test_assistantmessage_to_string_with_reasoning_and_answer() -> None:
    info: AssistantMessageInfo = {
        "id": "a1",
        "system": ["sys_prompt"],
        "mode": "chat",
        "path": {"cwd": "/", "root": "/"},
        "cost": 0,
        "tokens": {
            "input": 1,
            "output": 1,
            "reasoning": 1,
            "cache": {"read": 0, "write": 0},
        },
        "modelID": "m",
        "providerID": "p",
        "time": {"started": 123},
        "sessionID": "s1",
    }

    parts: List[
        Union[
            AssistantMessageStepFinish,
            AssistantMessageStepStart,
            AssistantMessageStepWithText,
        ]
    ] = [
        {  # type: ignore
            "id": "1",
            "messageID": "m1",
            "sessionID": "s1",
            "type": "reasoning",
            "text": "thinking...",
        },
        {  # type: ignore
            "id": "2",
            "messageID": "m1",
            "sessionID": "s1",
            "type": "answer",
            "text": "final answer",
        },
    ]

    msg = AssistantMessage(info=info, parts=parts)
    out = msg.to_string(include_system_prompt=True)

    # checks
    assert out.startswith("<assistant>")
    assert "<system>sys_prompt</system>" in out
    assert "<reasoning>thinking...</reasoning>" in out
    assert "<answer>final answer</answer>" in out
    assert out.endswith("</assistant>")
