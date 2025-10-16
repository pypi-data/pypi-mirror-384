# Debug Helper Python SDK

A production-grade debugging and issue tracking helper SDK for Python applications.

## Installation

```bash
pip install debug-helper
```

## Quick Start

```python
from debug_helper import DebugLogger

# Initialize the logger with your project API key
logger = DebugLogger(api_key="dh_your_project_api_key_here")

# Report an issue
logger.issue(
    title="Payment API returned empty response",
    description="Expected JSON but got empty payload",
    file_name="payments.py",
    line_number=101,
    log_path="/var/logs/payments/error.log"
)
```

## Features

- **Easy Integration**: Simple API for reporting issues from your Python applications
- **Automatic Context Capture**: Automatically collects environment information, stack traces, and system details
- **Log File Upload**: Upload local log files or reference remote/S3 files
- **Error Handling**: Built-in retry logic and proper error handling
- **Configurable**: Flexible configuration options for different environments

## Configuration

### Basic Configuration

```python
from debug_helper import DebugLogger

logger = DebugLogger(
    api_key="your_project_api_key",
    api_url="https://api.your-debug-helper.com",  # Optional: defaults to localhost
    timeout=30,  # Request timeout in seconds
    retries=3,   # Number of retry attempts
    auto_logging=True  # Automatically capture environment info
)
```

### Environment Variables

You can also configure the SDK using environment variables:

```bash
export DEBUG_HELPER_API_KEY="your_project_api_key"
export DEBUG_HELPER_API_URL="https://api.your-debug-helper.com"
```

## API Reference

### DebugLogger.issue()

Report an issue to the Debug Helper service.

```python
logger.issue(
    title: str,                    # Required: Short summary of the issue
    description: str = "",         # Detailed description
    file_name: str = "",          # File where the issue occurred
    line_number: int = None,      # Line number of the issue
    function_name: str = "",      # Function name where issue occurred
    log_path: str = None,         # Path to log file (local or remote)
    severity: str = "medium",     # low, medium, high, critical
    exception: Exception = None,  # Python exception object
    environment_info: dict = None # Additional environment info
)
```

### Exception Handling

Automatically capture and report exceptions:

```python
try:
    # Your code that might raise an exception
    risky_operation()
except Exception as e:
    logger.issue(
        title="Risky operation failed",
        description="The risky operation encountered an error",
        exception=e,  # Automatically extracts stack trace
        severity="high"
    )
```

### Auto-reporting with Context Manager

Use the auto-reporter context manager for automatic exception reporting:

```python
from debug_helper.utils import AutoIssueReporter

with AutoIssueReporter(logger, title_prefix="Payment Processing"):
    # Any unhandled exception will be automatically reported
    process_payment(payment_data)
```

### Log File Handling

#### Upload Local Files

```python
logger.issue(
    title="Database connection failed",
    log_path="/var/logs/app/database.log"  # Will be uploaded automatically
)
```

#### Reference Remote Files

```python
logger.issue(
    title="S3 processing error",
    log_path="s3://my-bucket/logs/error-2023-09-16.log"  # Reference to S3 file
)
```

#### Reference HTTP URLs

```python
logger.issue(
    title="External API error",
    log_path="https://logs.example.com/api-errors/2023-09-16.log"
)
```

## Advanced Usage

### Custom Environment Information

```python
logger.issue(
    title="Custom issue",
    environment_info={
        "user_id": "12345",
        "session_id": "abcdef",
        "feature_flags": {"new_ui": True},
        "request_id": "req_123456"
    }
)
```

### Testing Connection

```python
if logger.test_connection():
    print("Connected to Debug Helper successfully!")
else:
    print("Failed to connect to Debug Helper")
```

### Quick Reporting Function

For one-off issue reporting without creating a logger instance:

```python
from debug_helper import report_issue

report_issue(
    api_key="your_api_key",
    title="Quick issue report",
    description="Something went wrong"
)
```

## Error Handling

The SDK includes comprehensive error handling:

```python
from debug_helper import DebugLogger, DebugHelperException

try:
    logger = DebugLogger(api_key="invalid_key")
    logger.issue(title="Test issue")
except DebugHelperException as e:
    print(f"Debug Helper error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### 1. Use Descriptive Titles

```python
# Good
logger.issue(title="PayPal API timeout during checkout process")

# Bad
logger.issue(title="Error")
```

### 2. Include Context

```python
logger.issue(
    title="Database query timeout",
    description=f"Query took {query_time}ms, exceeded {timeout}ms limit",
    file_name="database.py",
    line_number=get_caller_info()[1],
    environment_info={
        "query": query_sql,
        "parameters": query_params,
        "execution_time": query_time
    }
)
```

### 3. Use Appropriate Severity Levels

- **critical**: System is down, immediate attention required
- **high**: Major functionality broken, affects many users
- **medium**: Important feature not working, affects some users
- **low**: Minor issue, cosmetic problems

### 4. Handle Sensitive Information

The SDK automatically filters out common sensitive environment variables, but be cautious with custom data:

```python
# Avoid including sensitive data
logger.issue(
    title="Authentication failed",
    environment_info={
        "user_id": user.id,  # OK
        "username": user.username,  # OK
        # "password": user.password,  # DON'T DO THIS
        "last_login": user.last_login  # OK
    }
)
```

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://docs.debughelper.com
- GitHub Issues: https://github.com/your-org/debug-helper/issues
- Email: support@debughelper.com