from pytest import fixture
from pytest import mark

from dotchatbot.input.parser import Parser
from dotchatbot.input.transformer import Message


@fixture
def parser() -> Parser:
    return Parser()


@mark.parametrize(
    "content,expected",
    [
        (
            "",
            []
        ),
        (
            "some content\n",
            [
                Message(role="user", content="some content\n"),
            ]
        ),
        (
            "@@> user:\n"
            "test\n"
            "this\n"
            "is\n"
            "a\n"
            "test\n",
            [
                Message(role="user", content="test\nthis\nis\na\ntest\n"),
            ]
        ),
        (
            "@@> user:\n"
            "one\n"
            "@@> assistant (test):\n"
            "two\n"
            "@@> user:\n"
            "three\n",
            [
                Message(role="user", content="one\n"),
                Message(role="assistant", model='test', content="two\n"),
                Message(role="user", content="three\n"),
            ],
        ),
        (
                "@@> user:\n"
                "one\n"
                "@@> assistant (unusual model name<>.2932938ds8):):(():):\n"
                "two\n"
                "@@> user:\n"
                "three\n",
                [
                    Message(role="user", content="one\n"),
                    Message(
                        role="assistant",
                        model='unusual model name<>.2932938ds8):):(():',
                        content="two\n"
                    ),
                    Message(role="user", content="three\n"),
                ],
        )
    ]
)
def test_parser(parser: Parser, content: str, expected: list[Message]) -> None:
    assert parser.parse(content) == expected
