from behave import given, then
from features.test_helpers import get_current_scenario_context

from archipy.models.types.error_message_types import ErrorMessageType

# Exception Mapping
exception_mapping = {
    "INVALID_PHONE": ErrorMessageType.INVALID_PHONE,
    "NOT_FOUND": ErrorMessageType.NOT_FOUND,
    "TOKEN_EXPIRED": ErrorMessageType.TOKEN_EXPIRED,
}


@given('an exception type "{exception_enum}"')
def step_given_exception_type(context, exception_enum):
    scenario_context = get_current_scenario_context(context)
    exception_detail = exception_mapping[exception_enum].value  # Get ExceptionDetailDTO
    scenario_context.store("exception_detail", exception_detail)


@then('the exception code should be "{expected_code}"')
def step_then_check_exception_code(context, expected_code):
    scenario_context = get_current_scenario_context(context)
    exception_detail = scenario_context.get("exception_detail")
    assert exception_detail.code == expected_code, f"Expected '{expected_code}', but got '{exception_detail.code}'"


@then('the English message should be "{expected_message_en}"')
def step_then_check_english_message(context, expected_message_en):
    scenario_context = get_current_scenario_context(context)
    exception_detail = scenario_context.get("exception_detail")
    assert (
        exception_detail.message_en == expected_message_en
    ), f"Expected '{expected_message_en}', but got '{exception_detail.message_en}'"


@then('the Persian message should be "{expected_message_fa}"')
def step_then_check_persian_message(context, expected_message_fa):
    scenario_context = get_current_scenario_context(context)
    exception_detail = scenario_context.get("exception_detail")
    assert (
        exception_detail.message_fa == expected_message_fa
    ), f"Expected '{expected_message_fa}', but got '{exception_detail.message_fa}'"


@then("the HTTP status should be {http_status}")
def step_then_check_http_status(context, http_status):
    scenario_context = get_current_scenario_context(context)
    exception_detail = scenario_context.get("exception_detail")
    assert exception_detail.http_status == int(
        http_status,
    ), f"Expected HTTP {http_status}, but got {exception_detail.http_status}"


@then("the gRPC status should be {grpc_status}")
def step_then_check_grpc_status(context, grpc_status):
    scenario_context = get_current_scenario_context(context)
    exception_detail = scenario_context.get("exception_detail")
    assert exception_detail.grpc_status == int(
        grpc_status,
    ), f"Expected gRPC {grpc_status}, but got {exception_detail.grpc_status}"
