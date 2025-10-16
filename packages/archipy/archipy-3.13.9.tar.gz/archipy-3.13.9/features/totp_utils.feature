Feature: TOTPUtils functionality

  Scenario: Generate TOTP with valid secret
    Given a valid secret "12345678901234567890"
    When a TOTP is generated
    Then a TOTP code is returned
    And an expiration time is provided

  Scenario: Verify TOTP with valid code
    Given a valid secret "12345678901234567890"
    And a TOTP code is generated
    When the TOTP code is verified
    Then the verification should succeed

  Scenario: Verify TOTP with invalid code
    Given a valid secret "12345678901234567890"
    And an invalid TOTP code "000000"
    When the invalid TOTP code is verified
    Then the verification should fail

  Scenario: Generate secret key
    When a secret key is generated
    Then a secret key is returned
