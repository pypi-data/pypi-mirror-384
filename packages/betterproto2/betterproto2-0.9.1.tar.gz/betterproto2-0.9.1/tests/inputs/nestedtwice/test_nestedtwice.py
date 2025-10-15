import pytest

from tests.outputs.nestedtwice.nestedtwice import (
    Test,
    TestTop,
    TestTopMiddle,
    TestTopMiddleBottom,
    TestTopMiddleEnumBottom,
    TestTopMiddleTopMiddleBottom,
)


@pytest.mark.parametrize(
    ("cls", "expected_comment"),
    [
        (Test, "Test doc."),
        (TestTopMiddleEnumBottom, "EnumBottom doc."),
        (TestTop, "Top doc."),
        (TestTopMiddle, "Middle doc."),
        (TestTopMiddleTopMiddleBottom, "TopMiddleBottom doc."),
        (TestTopMiddleBottom, "Bottom doc."),
    ],
)
def test_comment(cls, expected_comment):
    assert cls.__doc__.strip() == expected_comment
