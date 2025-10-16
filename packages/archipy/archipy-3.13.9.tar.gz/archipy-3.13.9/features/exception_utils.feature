Feature: Exception Utilities

  Scenario: Capture an exception
    Given a raised exception "ValueError" with message "Something went wrong"
    When the exception is captured
    Then it should be logged

  Scenario: Create an exception detail
    Given an exception with code "ERR001", English message "Invalid data", and Persian message "داده نامعتبر"
    When an exception detail is created
    Then the response should contain code "ERR001"

  Scenario: Handle a FastAPI exception
    Given a FastAPI exception "BaseError"
    When an async FastAPI exception is handled
    Then the response should have an HTTP status of 500

  Scenario: Handle a gRPC exception
    Given a gRPC exception "BaseError"
    When gRPC exception is handled
    Then the response should have gRPC status "INTERNAL"

  Scenario: Generate FastAPI exception responses
    Given a list of FastAPI errors ["InvalidPhoneNumberError", "NotFoundError"]
    When the FastAPI exception responses are generated
    Then the responses should contain HTTP status codes
