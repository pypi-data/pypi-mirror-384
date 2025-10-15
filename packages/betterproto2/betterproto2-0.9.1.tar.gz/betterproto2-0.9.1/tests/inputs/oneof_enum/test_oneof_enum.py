import betterproto2
from tests.outputs.oneof_enum.oneof_enum import Move, Signal, Test
from tests.util import get_test_case_json_data


def test_which_one_of_returns_enum_with_default_value():
    """
    returns first field when it is enum and set with default value
    """
    message = Test.from_json(get_test_case_json_data("oneof_enum", "oneof_enum-enum-0.json")[0].json)

    assert message.move is None
    assert message.signal == Signal.PASS
    assert betterproto2.which_one_of(message, "action") == ("signal", Signal.PASS)


def test_which_one_of_returns_enum_with_non_default_value():
    """
    returns first field when it is enum and set with non default value
    """
    message = Test.from_json(get_test_case_json_data("oneof_enum", "oneof_enum-enum-1.json")[0].json)

    assert message.move is None
    assert message.signal == Signal.RESIGN
    assert betterproto2.which_one_of(message, "action") == ("signal", Signal.RESIGN)


def test_which_one_of_returns_second_field_when_set():
    message = Test.from_json(get_test_case_json_data("oneof_enum")[0].json)
    assert message.move == Move(x=2, y=3)
    assert message.signal is None
    assert betterproto2.which_one_of(message, "action") == ("move", Move(x=2, y=3))
