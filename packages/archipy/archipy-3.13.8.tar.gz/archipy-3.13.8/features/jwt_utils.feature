Feature: JWT Utilities

  Scenario: Generate an access token
    Given a valid user UUID
    When an access token is created
    Then a JWT token should be returned

  Scenario: Generate a refresh token
    Given a valid user UUID
    When a refresh token is created
    Then a JWT token should be returned

  Scenario: Decode a valid access token
    Given a valid user UUID
    And a valid access token
    When the token is decoded
    Then the decoded payload should be valid

  Scenario: Decode a valid refresh token
    Given a valid user UUID
    And a valid refresh token
    When the token is decoded
    Then the decoded payload should be valid

  Scenario: Expired token should not be valid
    Given a valid user UUID
    And an expired access token
    When the token is decoded
    Then a TokenExpiredError should be raised

  Scenario: Invalid token should not be accepted
    Given a valid user UUID
    And an invalid token
    When the token is decoded
    Then an InvalidTokenError should be raised
