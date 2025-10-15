Feature: App Utilities

  Scenario: Create a FastAPI app with default settings
    When a FastAPI app is created
    Then the app should have the correct title
    And exception handlers should be registered

  Scenario: Handle a common custom exception
    Given a FastAPI app
    When an endpoint raises a "BaseError"
    Then the response should have status code 500

  Scenario: Handle validation errors in FastAPI
    Given a FastAPI app
    When an endpoint raises a validation error
    Then the response should have status code 422

  Scenario: Generate unique route ID
    Given a FastAPI route with tag "user" and name "get_user_info"
    When a unique ID is generated
    Then the unique ID should be "user-get_user_info"

  Scenario: Setup CORS middleware
    Given a FastAPI app with CORS configuration
    When CORS middleware is setup
    Then the app should allow origins "https://example.com"
