Feature: Password Utilities

  Scenario: Hash a password successfully
    Given a password "SecureP@ss123"
    When the password is hashed
    Then a hashed password should be returned

  Scenario: Verify a correct password
    Given a password "SecureP@ss123"
    And the password is hashed
    When the password is verified
    Then the verification should succeed

  Scenario: Verify an incorrect password
    Given a password "SecureP@ss123"
    And the password is hashed
    When a different password "WrongPass123" is verified
    Then the verification should fail

  Scenario: Validate a strong password
    Given a password "StrongP@ssword1!"
    When the password is validated
    Then the password validation should succeed

  Scenario: Fail validation on a weak password
    Given a password "weak"
    When the password is validated
    Then the password validation should fail

  Scenario: Generate a secure password
    When a secure password is generated
    Then the generated password should meet security requirements

  Scenario: Prevent reusing an old password
    Given a password history containing "OldP@ssword1"
    When a user attempts to reuse "OldP@ssword1" as a new password
    Then the password validation should fail with an error message
