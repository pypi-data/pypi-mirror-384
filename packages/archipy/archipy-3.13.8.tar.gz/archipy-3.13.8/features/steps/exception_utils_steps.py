import asyncio
from http import HTTPStatus
from unittest.mock import patch

from behave import given, then, when
from fastapi.responses import JSONResponse
from grpc import StatusCode

from archipy.helpers.utils.error_utils import ErrorUtils
from archipy.models.dtos.error_dto import ErrorDetailDTO
from archipy.models.errors import BaseError, InvalidPhoneNumberError, NotFoundError
from features.test_helpers import get_current_scenario_context


@given('a raised exception "{exception_type}" with message "{message}"')
def step_given_raised_exception(context, exception_type, message):
    scenario_context = get_current_scenario_context(context)
    exception = eval(f"{exception_type}('{message}')")
    scenario_context.store("exception", exception)


@when("the exception is captured")
def step_when_exception_is_captured(context):
    scenario_context = get_current_scenario_context(context)
    exception = scenario_context.get("exception")
    with patch("logging.exception") as mock_log:
        ErrorUtils.capture_exception(exception)
        scenario_context.store("log_called", mock_log.called)


@then("it should be logged")
def step_then_exception_should_be_logged(context):
    scenario_context = get_current_scenario_context(context)
    log_called = scenario_context.get("log_called")
    assert log_called is True


@given('an exception with code "{code}", English message "{message_en}", and Persian message "{message_fa}"')
def step_given_create_exception_detail(context, code, message_en, message_fa):
    scenario_context = get_current_scenario_context(context)
    exception_details = ErrorDetailDTO.create_error_detail(code, message_en, message_fa)
    scenario_context.store("exception_details", exception_details)


@when("an exception detail is created")
def step_when_exception_detail_is_created(context):
    pass  # No need for additional processing


@then('the response should contain code "{expected_code}"')
def step_then_exception_detail_should_contain_code(context, expected_code):
    scenario_context = get_current_scenario_context(context)
    exception_details = scenario_context.get("exception_details")
    assert exception_details.code == expected_code


@given('a FastAPI exception "{exception_type}"')
def step_given_fastapi_exception(context, exception_type):
    scenario_context = get_current_scenario_context(context)
    fastapi_exception = eval(f"{exception_type}()")
    scenario_context.store("fastapi_exception", fastapi_exception)


@when("an async FastAPI exception is handled")
def step_when_fastapi_exception_is_handled(context):
    scenario_context = get_current_scenario_context(context)
    fastapi_exception = scenario_context.get("fastapi_exception")

    async def handle_exception():
        return await ErrorUtils.async_handle_fastapi_exception(None, fastapi_exception)

    with patch("fastapi.responses.JSONResponse") as mock_response:
        mock_response.return_value = JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"detail": "Error occurred"},
        )
        http_status = asyncio.run(handle_exception()).status_code
        scenario_context.store("http_status", http_status)


@then("the response should have an HTTP status of 500")
def step_then_http_status_should_be_500(context):
    scenario_context = get_current_scenario_context(context)
    http_status = scenario_context.get("http_status")
    assert http_status == 500


@given('a gRPC exception "{exception_type}"')
def step_given_grpc_exception(context, exception_type):
    scenario_context = get_current_scenario_context(context)
    grpc_exception = eval(f"{exception_type}()")
    scenario_context.store("grpc_exception", grpc_exception)


@when("gRPC exception is handled")
def step_when_grpc_exception_is_handled(context):
    scenario_context = get_current_scenario_context(context)
    grpc_exception = scenario_context.get("grpc_exception")
    grpc_code, _ = ErrorUtils.handle_grpc_exception(grpc_exception)
    scenario_context.store("grpc_code", grpc_code)


@then('the response should have gRPC status "INTERNAL"')
def step_then_grpc_status_should_be_internal(context):
    scenario_context = get_current_scenario_context(context)
    grpc_code = scenario_context.get("grpc_code")
    assert grpc_code == StatusCode.INTERNAL


@given("a list of FastAPI errors {exception_names}")
def step_given_list_of_exceptions(context, exception_names):
    scenario_context = get_current_scenario_context(context)
    exception_mapping = {
        "InvalidPhoneNumberError": InvalidPhoneNumberError,
        "NotFoundError": NotFoundError,
        "BaseError": BaseError,
    }
    exception_list = [
        exception_mapping[exc.strip()]
        for exc in exception_names.strip("[]").split(",")
        if exc.strip() in exception_mapping
    ]
    scenario_context.store("exception_list", exception_list)


@when("the FastAPI exception responses are generated")
def step_when_generate_exception_responses(context):
    scenario_context = get_current_scenario_context(context)
    exception_list = scenario_context.get("exception_list")
    responses = ErrorUtils.get_fastapi_exception_responses(exception_list)
    scenario_context.store("responses", responses)


@then("the responses should contain HTTP status codes")
def step_then_responses_should_contain_status_codes(context):
    scenario_context = get_current_scenario_context(context)
    responses = scenario_context.get("responses")
    assert isinstance(responses, dict)
    assert len(responses) > 0, "Expected non-empty responses, but got empty dictionary."
    assert any(isinstance(status, HTTPStatus) for status in responses.keys()), "No valid HTTPStatus keys found."
