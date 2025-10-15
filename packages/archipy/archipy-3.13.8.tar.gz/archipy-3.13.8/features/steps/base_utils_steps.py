from behave import given, then, when

from archipy.helpers.utils.base_utils import BaseUtils
from archipy.models.errors import (
    InvalidLandlineNumberError,
    InvalidNationalCodeError,
    InvalidPhoneNumberError,
)
from features.test_helpers import get_current_scenario_context


@given('an input phone number "{input_number}"')
def step_given_input_phone_number(context, input_number):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("input_number", input_number)


@when("the phone number is sanitized")
def step_when_sanitize_phone_number(context):
    scenario_context = get_current_scenario_context(context)
    input_number = scenario_context.get("input_number")
    sanitized_output = BaseUtils.sanitize_iranian_landline_or_phone_number(input_number)
    scenario_context.store("sanitized_output", sanitized_output)


@then('the sanitized output should be "{expected_output}"')
def step_then_check_sanitized_output(context, expected_output):
    scenario_context = get_current_scenario_context(context)
    sanitized_output = scenario_context.get("sanitized_output")
    assert sanitized_output == expected_output


@given('a valid mobile phone number "{phone_number}"')
def step_given_valid_phone_number(context, phone_number):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("phone_number", phone_number)


@when("the phone number is validated")
def step_when_validate_phone_number(context):
    scenario_context = get_current_scenario_context(context)
    phone_number = scenario_context.get("phone_number")
    try:
        BaseUtils.validate_iranian_phone_number(phone_number)
        scenario_context.store("is_valid", True)
    except InvalidPhoneNumberError:
        scenario_context.store("is_valid", False)


@given('an invalid mobile phone number "{phone_number}"')
def step_given_invalid_phone_number(context, phone_number):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("phone_number", phone_number)


@when("the phone number validation is attempted")
def step_when_validate_invalid_phone_number(context):
    scenario_context = get_current_scenario_context(context)
    phone_number = scenario_context.get("phone_number")
    try:
        BaseUtils.validate_iranian_phone_number(phone_number)
    except InvalidPhoneNumberError as e:
        scenario_context.store("exception_message", str(e.message))


@given('a valid landline phone number "{landline_number}"')
def step_given_valid_landline_number(context, landline_number):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("landline_number", landline_number)


@when("the landline number is validated")
def step_when_validate_landline_number(context):
    scenario_context = get_current_scenario_context(context)
    landline_number = scenario_context.get("landline_number")
    try:
        BaseUtils.validate_iranian_landline_number(landline_number)
        scenario_context.store("is_valid", True)
    except InvalidLandlineNumberError:
        scenario_context.store("is_valid", False)


@given('an invalid landline phone number "{landline_number}"')
def step_given_invalid_landline_number(context, landline_number):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("landline_number", landline_number)


@when("the landline number validation is attempted")
def step_when_validate_invalid_landline_number(context):
    scenario_context = get_current_scenario_context(context)
    landline_number = scenario_context.get("landline_number")
    try:
        BaseUtils.validate_iranian_landline_number(landline_number)
    except InvalidLandlineNumberError as e:
        scenario_context.store("exception_message", str(e.message))


@given('a valid national code "{national_code}"')
def step_given_valid_national_code(context, national_code):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("national_code", national_code)


@when("the national code is validated")
def step_when_validate_national_code(context):
    scenario_context = get_current_scenario_context(context)
    national_code = scenario_context.get("national_code")
    try:
        BaseUtils.validate_iranian_national_code_pattern(national_code)
        scenario_context.store("is_valid", True)
    except InvalidNationalCodeError:
        scenario_context.store("is_valid", False)


@given('an invalid national code "{national_code}"')
def step_given_invalid_national_code(context, national_code):
    scenario_context = get_current_scenario_context(context)
    scenario_context.store("national_code", national_code)


@when("the national code validation is attempted")
def step_when_validate_invalid_national_code(context):
    scenario_context = get_current_scenario_context(context)
    national_code = scenario_context.get("national_code")
    try:
        BaseUtils.validate_iranian_national_code_pattern(national_code)
    except InvalidNationalCodeError as e:
        scenario_context.store("exception_message", str(e.message))
