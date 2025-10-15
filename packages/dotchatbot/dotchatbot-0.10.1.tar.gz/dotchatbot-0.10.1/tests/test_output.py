from pytest import mark

from dotchatbot.output.file import generate_filename_from_response


@mark.parametrize(
    "summary,expected",
    [("Test Filename", "test-filename-00000.dcb"), (
        "Test Filename Some's Invalid!",
        "test-filename-somes-invalid-00000.dcb"), (
        "   Test Filename Some's Invalid!   ",
        "test-filename-somes-invalid-00000.dcb"), ]
)
def test_generate_filename_from_response(summary: str, expected: str) -> None:
    assert generate_filename_from_response(
        summary, [], '.dcb'
    ) == expected
