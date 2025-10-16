from behave import then
from behave.runner import Context

from features.test_helpers import get_current_scenario_context


@then('an error message "{expected_message}" should be raised')
def step_then_error_message(context: Context, expected_message) -> None:
    """Verify that the expected error message was raised.

    Args:
        context: The behave context object
        expected_message: The error message that should have been raised
    """
    scenario_context = get_current_scenario_context(context)
    exception_message = scenario_context.get("exception_message")
    assert exception_message == expected_message


@then("the validation should {expected_result}")
def step_then_validation_result(context: Context, expected_result) -> None:
    """Verify that the validation result matches expectations.

    Args:
        context: The behave context object
        expected_result: String indicating expected result ("succeed" or "fail")
    """
    scenario_context = get_current_scenario_context(context)
    is_valid = scenario_context.get("is_valid")
    expected_bool = expected_result == "succeed"
    assert is_valid == expected_bool


@then("the verification should {expected_result}")
def step_then_verification_succeeds(context: Context, expected_result) -> None:
    """Verify that the verification result matches expectations.

    Args:
        context: The behave context object
        expected_result: String indicating expected result ("succeed" or "fail")
    """
    scenario_context = get_current_scenario_context(context)
    is_verified = scenario_context.get("is_verified")
    expected_bool = expected_result == "succeed"
    assert is_verified is expected_bool


@then("the result should be True")
def step_then_result_should_be_true(context: Context) -> None:
    """Verify that the result is True.

    Args:
        context: The behave context object
    """
    scenario_context = get_current_scenario_context(context)
    result = scenario_context.get("result")
    assert result is True


@then("the result should be False")
def step_then_result_should_be_false(context: Context) -> None:
    """Verify that the result is False.

    Args:
        context: The behave context object
    """
    scenario_context = get_current_scenario_context(context)
    result = scenario_context.get("result")
    assert result is False


@then("the result should be either True or False")
def step_then_result_should_be_boolean(context: Context) -> None:
    """Verify that the result is a boolean value.

    Args:
        context: The behave context object
    """
    scenario_context = get_current_scenario_context(context)
    result = scenario_context.get("result")
    assert isinstance(result, bool)
