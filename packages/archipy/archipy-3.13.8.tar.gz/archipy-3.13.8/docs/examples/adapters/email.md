# Email Adapter Examples

This page demonstrates how to use ArchiPy's email adapter functionality for sending emails with proper error handling and logging.

## Basic Usage

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError, InvalidArgumentError

# Configure logging
logger = logging.getLogger(__name__)

# Configure email adapter
try:
    email_adapter = EmailAdapter(
        host="smtp.example.com",
        port=587,
        username="your-username",
        password="your-password",
        use_tls=True
    )
except Exception as e:
    logger.error(f"Failed to configure email adapter: {e}")
    raise InternalError() from e
else:
    logger.info("Email adapter configured successfully")
```

## Sending Simple Emails

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError

# Configure logging
logger = logging.getLogger(__name__)

email_adapter = EmailAdapter(
    host="smtp.example.com",
    port=587,
    username="your-username",
    password="your-password",
    use_tls=True
)

# Send an email
try:
    email_adapter.send_email(
        subject="Test Email",
        body="This is a test email from ArchiPy",
        recipients=["recipient@example.com"],
        from_email="sender@example.com"
    )
except InvalidArgumentError as e:
    logger.error(f"Invalid email parameters: {e}")
    raise
except InternalError as e:
    logger.error(f"Failed to send email: {e}")
    raise
else:
    logger.info("Email sent successfully")
```

## Sending Emails with CC and BCC

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError

# Configure logging
logger = logging.getLogger(__name__)

email_adapter = EmailAdapter(
    host="smtp.example.com",
    port=587,
    username="your-username",
    password="your-password",
    use_tls=True
)

# Send email with CC and BCC
try:
    email_adapter.send_email(
        subject="Important Notification",
        body="This message has CC and BCC recipients",
        recipients=["primary@example.com"],
        cc=["cc1@example.com", "cc2@example.com"],
        bcc=["bcc@example.com"],
        from_email="sender@example.com"
    )
except InternalError as e:
    logger.error(f"Failed to send email with CC/BCC: {e}")
    raise
else:
    logger.info("Email sent with CC and BCC recipients")
```

## Sending HTML Emails

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError

# Configure logging
logger = logging.getLogger(__name__)

email_adapter = EmailAdapter(
    host="smtp.example.com",
    port=587,
    username="your-username",
    password="your-password",
    use_tls=True
)

html_content = """
<html>
  <body>
    <h1>Welcome to ArchiPy!</h1>
    <p>This is an <strong>HTML</strong> email.</p>
  </body>
</html>
"""

try:
    email_adapter.send_email(
        subject="HTML Email",
        body=html_content,
        recipients=["user@example.com"],
        from_email="sender@example.com",
        is_html=True
    )
except InternalError as e:
    logger.error(f"Failed to send HTML email: {e}")
    raise
else:
    logger.info("HTML email sent successfully")
```

## Sending Emails with Attachments

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError, InvalidArgumentError

# Configure logging
logger = logging.getLogger(__name__)

email_adapter = EmailAdapter(
    host="smtp.example.com",
    port=587,
    username="your-username",
    password="your-password",
    use_tls=True
)

try:
    email_adapter.send_email(
        subject="Email with Attachment",
        body="Please find the attached document",
        recipients=["user@example.com"],
        from_email="sender@example.com",
        attachments=["/path/to/document.pdf", "/path/to/image.png"]
    )
except InvalidArgumentError as e:
    logger.error(f"Invalid attachment path: {e}")
    raise
except InternalError as e:
    logger.error(f"Failed to send email with attachments: {e}")
    raise
else:
    logger.info("Email with attachments sent successfully")
```

## Integration with FastAPI

```python
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError, InvalidArgumentError

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI()
email_adapter = EmailAdapter(
    host="smtp.example.com",
    port=587,
    username="your-username",
    password="your-password",
    use_tls=True
)


class EmailRequest(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None


@app.post("/send-email")
async def send_email(email_request: EmailRequest) -> dict[str, str]:
    """Send an email via API endpoint."""
    try:
        email_adapter.send_email(
            subject=email_request.subject,
            body=email_request.body,
            recipients=email_request.to,
            cc=email_request.cc,
            bcc=email_request.bcc,
            from_email="noreply@example.com"
        )
    except InvalidArgumentError as e:
        logger.error(f"Invalid email request: {e}")
        raise HTTPException(status_code=400, detail="Invalid email parameters") from e
    except InternalError as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email") from e
    else:
        logger.info(f"Email sent to {len(email_request.to)} recipient(s)")
        return {"message": "Email sent successfully"}
```

## Error Handling Patterns

```python
import logging

from archipy.adapters.email import EmailAdapter
from archipy.models.errors import InternalError, InvalidArgumentError, ConfigurationError

# Configure logging
logger = logging.getLogger(__name__)


def send_notification_email(recipient: str, subject: str, body: str) -> bool:
    """Send a notification email with comprehensive error handling.

    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Email body content

    Returns:
        True if email sent successfully, False otherwise

    Raises:
        InvalidArgumentError: If email parameters are invalid
        InternalError: If email service fails
        ConfigurationError: If email adapter is not configured
    """
    try:
        email_adapter = EmailAdapter(
            host="smtp.example.com",
            port=587,
            username="your-username",
            password="your-password",
            use_tls=True
        )
    except Exception as e:
        logger.error(f"Email adapter configuration failed: {e}")
        raise ConfigurationError() from e

    try:
        email_adapter.send_email(
            subject=subject,
            body=body,
            recipients=[recipient],
            from_email="noreply@example.com"
        )
    except InvalidArgumentError as e:
        logger.error(f"Invalid email parameters: {e}")
        raise
    except InternalError as e:
        logger.error(f"Failed to send email: {e}")
        raise
    else:
        logger.info(f"Notification email sent to {recipient}")
        return True
```

## See Also

- [Error Handling](../error_handling.md) - Exception handling patterns with proper chaining
- [Configuration Management](../config_management.md) - Email configuration setup
- [BDD Testing](../bdd_testing.md) - Testing email operations
- [API Reference](../../api_reference/adapters.md) - Full Email adapter API documentation
