Feature: Custom Exceptions Handling

  Scenario Outline: Verify exception message type details
    Given an exception type "<exception_enum>"
    Then the exception code should be "<expected_code>"
    And the English message should be "<expected_message_en>"
    And the Persian message should be "<expected_message_fa>"

    Examples:
      | exception_enum          | expected_code      | expected_message_en                     | expected_message_fa                          |
      | INVALID_PHONE           | INVALID_PHONE     | Invalid Iranian phone number            | شماره تلفن همراه ایران نامعتبر است.          |
      | NOT_FOUND               | NOT_FOUND        | Requested resource not found            | منبع درخواستی یافت نشد.                      |
      | TOKEN_EXPIRED           | TOKEN_EXPIRED    | Authentication token has expired        | توکن احراز هویت منقضی شده است.              |

  Scenario Outline: Verify HTTP and gRPC status codes in exception messages
    Given an exception type "<exception_enum>"
    Then the HTTP status should be <http_status>
    And the gRPC status should be <grpc_status>

    Examples:
      | exception_enum          | http_status  | grpc_status  |
      | INVALID_PHONE           | 400         | 3            |
      | NOT_FOUND               | 404         | 5            |
      | TOKEN_EXPIRED           | 401         | 16           |
