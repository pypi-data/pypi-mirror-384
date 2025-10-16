# Bug Hunter 🐛🔫

**Automatic GitHub issue creation for Python errors using AI-powered descriptions**

Bug Hunter is a Python library that provides a decorator-based system for automatically creating GitHub issues when functions encounter errors or log critical messages. It uses Google's Gemini AI to generate intelligent, descriptive issue content that helps developers understand and fix problems faster.

## ✨ Features

- **🔍 Automatic Error Detection**: Captures both exceptions and logger.error calls
- **🤖 AI-Powered Descriptions**: Uses Gemini AI to generate detailed, helpful issue descriptions
- **🔄 Smart GitHub Integration**: Automatically creates well-formatted GitHub issues
- **🚫 Duplicate Prevention**: Automatically detects and prevents duplicate issues using deterministic titles
- **⚡ Thread-Safe**: Works correctly in multi-threaded applications
- **🛡️ Robust Error Handling**: Includes fallback mechanisms and retry logic
- **🏷️ Configurable**: Support for custom labels, assignees, and more

## 🚀 Quick Start

### Installation

```bash
pip install exc2issue
```

### Setup

1. **Get API Keys**:
   - GitHub Personal Access Token: Go to GitHub Settings → Developer settings → Personal access tokens
   - Gemini API Key: Get one from [Google AI Studio](https://aistudio.google.com/)

2. **Set Environment Variables**:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

### Basic Usage

```python
from exc2issue import exc2issue

@exc2issue(
    labels=["bug", "auto-generated"], 
    repository="your-username/your-repo"
)
def risky_function(data):
    # This will automatically create a GitHub issue if an error occurs
    if not data:
        raise ValueError("Data cannot be empty")
    return process_data(data)

# If this function fails, a GitHub issue will be created automatically
risky_function(None)
```

### Advanced Configuration

```python
from exc2issue import exc2issue
import logging

# Configure with custom settings
@exc2issue(
    labels=["bug", "critical", "production"],
    assignees=["maintainer-username", "team-lead"],  # Assign to multiple users
    repository="your-org/your-repo",
    github_token="custom_token",  # Optional: override env var
    gemini_api_key="custom_key"   # Optional: override env var
)
def critical_function():
    logger = logging.getLogger(__name__)
    
    try:
        # Some critical operation
        result = perform_operation()
    except Exception as e:
        # This will also create an issue
        logger.error("Critical operation failed: %s", str(e))
        raise
    
    return result
```

## 🔧 Configuration Options

### Decorator Parameters

|| Parameter | Type | Required | Description |
||-----------|------|----------|-------------|
|| `repository` | `str` | ✅ Yes | GitHub repository in format "owner/repo" |
|| `labels` | `List[str]` | ❌ No | Labels to apply to created issues |
|| `assignees` | `List[str]` | ❌ No | GitHub usernames to assign issues to |
|| `assignee` | `str` | ❌ No | Single GitHub username (legacy, use `assignees` instead) |
|| `github_token` | `str` | ❌ No | GitHub token (defaults to `GITHUB_TOKEN` env var) |
|| `gemini_api_key` | `str` | ❌ No | Gemini API key (defaults to `GEMINI_API_KEY` env var) |

### Pydantic Configuration (Advanced)

Bug Hunter uses Pydantic for configuration management, providing strong typing and validation. You can use environment variables with the `BUG_HUNTER_` prefix to configure all aspects of the library:

```python
from exc2issue.config import get_settings

# Load settings from environment variables or .env file
settings = get_settings()

@exc2issue(repository="your-org/repo", settings=settings)
def your_function():
    # Function implementation
    pass
```

**Environment Variable Configuration:**

- **GitHub Settings**: `BUG_HUNTER_GITHUB_TOKEN`, `BUG_HUNTER_GITHUB_BASE_URL`
- **Gemini Settings**: `BUG_HUNTER_GEMINI_API_KEY`, `BUG_HUNTER_GEMINI_MODEL_NAME`, `BUG_HUNTER_GEMINI_TEMPERATURE`, `BUG_HUNTER_GEMINI_MAX_OUTPUT_TOKENS`
- **Vertex AI Settings**: `BUG_HUNTER_VERTEXAI_PROJECT`, `BUG_HUNTER_VERTEXAI_LOCATION`, `BUG_HUNTER_VERTEXAI_MODEL_NAME`
- **Global Settings**: `BUG_HUNTER_ENABLED`, `BUG_HUNTER_DRY_RUN`
- **Logging Settings**: `BUG_HUNTER_LOGGING_LEVEL`, `BUG_HUNTER_LOGGING_FORMAT`

See `.env.example` for a complete list of configuration options.

### AI Provider Selection

Bug Hunter supports two AI providers with automatic fallback:

1. **Vertex AI** (Priority 1): Enterprise-grade AI with Google Cloud authentication
   - Requires: `BUG_HUNTER_VERTEXAI_PROJECT` and Google Cloud authentication
   - Best for: Production environments, enterprise deployments
   - Authentication: Uses Google Cloud Application Default Credentials (ADC)

2. **Gemini Developer API** (Priority 2): Simple API key-based authentication
   - Requires: `BUG_HUNTER_GEMINI_API_KEY`
   - Best for: Development, testing, personal projects
   - Authentication: API key from Google AI Studio

If both are configured, Vertex AI takes priority. If neither is configured, the library falls back to generating basic issue descriptions without AI enhancement.

#### Setting up Vertex AI (Recommended for Production)

```bash
# Install Google Cloud SDK
# Follow instructions at: https://cloud.google.com/sdk/docs/install

# Authenticate for local development
gcloud auth application-default login

# Set your project (or use environment variable)
export BUG_HUNTER_VERTEXAI_PROJECT=your-gcp-project-id
export BUG_HUNTER_VERTEXAI_LOCATION=us-central1  # Optional, defaults to us-central1
```

For production deployments on Google Cloud (GCE, GKE, Cloud Run), authentication is automatic through service accounts.

## 🔍 What Gets Captured

Bug Hunter captures comprehensive error information:

- **Exception Details**: Type, message, and full stack trace
- **Function Context**: Name and arguments passed to the function
- **Timestamp**: When the error occurred
- **Log Messages**: Critical log messages (logger.error level and above)

## 🎯 Deterministic Issue Titles

Bug Hunter uses a deterministic title format to prevent duplicate issues for the same error:

### Title Format
- **Exceptions**: `[EXCEPTION]-[function_name]-[ExceptionType]`
- **Log Errors**: `[LOG-ERROR]-[function_name]-[MessagePattern]`

### Examples
```text
[EXCEPTION]-[process_payment]-[ValueError]
[LOG-ERROR]-[database_connect]-[Connection_failed_after_{number}_seconds]
[EXCEPTION]-[send_email]-[SMTPException]
[LOG-ERROR]-[user_lookup]-[User_{email}_not_found]
```

### Benefits
- **No Duplicates**: Same error type in same function always gets same title
- **Highly Readable**: Exception type and message patterns are immediately visible
- **Informative**: Shows actual `ValueError`, `TypeError`, etc. instead of cryptic hashes
- **Pattern Recognition**: Log messages show static patterns with `{placeholders}` for variables
- **Searchable**: Easy to find all `ValueError` issues in `process_payment` function

### Pattern Recognition Benefits
- Automatically groups similar errors together
- Makes it easy to identify recurring issues
- Facilitates pattern-based debugging and analysis

### Pattern Extraction for Logs
For log messages, variable values are replaced with descriptive placeholders:
- Numbers: `30 seconds` → `{number} seconds`
- Emails: `user@example.com` → `{email}`
- Times: `14:30:25` → `{time}`
- Variables: `user123` → `{variable}`
- This ensures messages like "Connection failed after 30 seconds" and "Connection failed after 120 seconds" produce the same title

## 🚫 Duplicate Prevention

Bug Hunter includes intelligent duplicate detection to prevent creating multiple issues for the same error:

### How It Works
1. **Deterministic Titles**: Each error type in each function gets a consistent, deterministic title
2. **Open Issue Search**: Before creating a new issue, Bug Hunter searches for existing open issues with the same title
3. **Skip Creation**: If an open issue already exists, creation is skipped and an informative message is logged
4. **Closed Issues Ignored**: Closed issues are ignored, allowing new issues to be created for recurring problems

### Example Behavior
```python
@exc2issue(repository="myorg/myapp", labels=["bug"])
def process_payment(amount):
    if amount <= 0:
        raise ValueError("Amount must be positive")

# First error creates: [EXCEPTION]-[process_payment]-[ValueError]
process_payment(-10)  # Creates new issue

# Second identical error is detected as duplicate
process_payment(-5)   # Skips creation, logs: "Skipping duplicate issue creation for '[EXCEPTION]-[process_payment]-[ValueError]'"
```

### Fallback Behavior
- If GitHub search fails, the issue will still be created (fail-safe approach)
- Network errors or API rate limits won't prevent issue creation
- All search failures are logged for debugging

### Benefits
- **Reduced Noise**: Eliminates duplicate issues cluttering your repository
- **Better Issue Management**: One issue per unique error type and location
- **Robust Design**: Never prevents issue creation even if duplicate detection fails
- **Informative Logging**: Clear messages when duplicates are detected

## 🤖 AI-Generated Issue Content

The Gemini AI generates issue descriptions that include:

- Clear summary of what went wrong
- Technical details from the error
- Function arguments and context
- Stack trace analysis (for exceptions)
- Potential impact assessment
- Properly formatted markdown

## 🛡️ Error Handling

Bug Hunter is designed to be robust and never interfere with your application:

- **Fallback Descriptions**: If AI generation fails, creates basic issue descriptions
- **Silent Failures**: If issue creation fails, logs a warning but doesn't crash your app
- **Retry Logic**: Automatically retries transient failures
- **Input Sanitization**: Safely handles sensitive data and special characters

## 📊 Observability: Logging and Metrics

Bug Hunter provides comprehensive observability capabilities while respecting the separation of concerns: the library instruments the code, but you control the configuration and exposure.

### Logging

Bug Hunter uses Python's standard `logging` module to provide insights into its operation. The library uses the logger name `exc2issue.*` for all internal logging.

**Log Levels Used:**
- `DEBUG`: Detailed execution flow (function entry/exit, internal state)
- `WARNING`: Expected errors and graceful degradation scenarios
- `ERROR`: Unexpected errors with full stack traces
- `CRITICAL`: Fatal errors leading to aborts (e.g., SystemExit)

**Enabling Logs:**

```python
import logging

# Basic setup - enable all exc2issue logs
logging.basicConfig(level=logging.INFO)
logging.getLogger('exc2issue').setLevel(logging.DEBUG)

# Or use more specific logger configuration
logger = logging.getLogger('exc2issue.core.decorator')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
```

**Example Log Output:**

```text
2024-01-15 10:30:45 - exc2issue.core.decorator - DEBUG - Executing decorated function: process_payment
2024-01-15 10:30:45 - exc2issue.core.decorator - ERROR - Exception in process_payment: Invalid amount
2024-01-15 10:30:46 - exc2issue.core.issue_creator - INFO - Creating GitHub issue for process_payment
```

**Important Notes:**
- Bug Hunter never calls `logging.basicConfig()` or configures handlers
- You maintain full control over logging configuration
- All internal operations are logged at appropriate levels
- No print() statements are used

### Metrics Collection

Bug Hunter provides a callback-based metrics system that allows you to plug in your preferred metrics backend (Prometheus, StatsD, DataDog, etc.).

**Metrics Collected:**
- Function execution duration (in seconds)
- Error count by function and error type
- Success/failure count per function

**Setting Up Metrics:**

```python
from exc2issue import exc2issue, set_metrics_collector
from prometheus_client import Counter, Histogram

# 1. Implement the MetricsCollector protocol
class PrometheusCollector:
    def __init__(self):
        self.duration = Histogram(
            'exc2issue_duration_seconds',
            'Function execution duration',
            ['function']
        )
        self.errors = Counter(
            'exc2issue_errors_total',
            'Error count',
            ['function', 'error_type']
        )
        self.successes = Counter(
            'exc2issue_successes_total',
            'Success count',
            ['function']
        )
    
    def record_duration(self, function_name: str, duration_seconds: float) -> None:
        self.duration.labels(function=function_name).observe(duration_seconds)
    
    def record_error(self, function_name: str, error_type: str, error: BaseException) -> None:
        self.errors.labels(function=function_name, error_type=error_type).inc()
    
    def record_success(self, function_name: str) -> None:
        self.successes.labels(function=function_name).inc()

# 2. Register your collector
set_metrics_collector(PrometheusCollector())

# 3. Use the decorator as normal
@exc2issue(repository="myorg/myapp", labels=["bug"])
def my_function():
    # Metrics are automatically collected
    pass
```

**StatsD Example:**

```python
from exc2issue import set_metrics_collector
import statsd

class StatsDCollector:
    def __init__(self, host='localhost', port=8125):
        self.client = statsd.StatsClient(host, port)
    
    def record_duration(self, function_name: str, duration_seconds: float) -> None:
        self.client.timing(f'exc2issue.{function_name}.duration', duration_seconds * 1000)
    
    def record_error(self, function_name: str, error_type: str, error: BaseException) -> None:
        self.client.incr(f'exc2issue.{function_name}.errors.{error_type}')
    
    def record_success(self, function_name: str) -> None:
        self.client.incr(f'exc2issue.{function_name}.success')

set_metrics_collector(StatsDCollector())
```

**DataDog Example:**

```python
from exc2issue import set_metrics_collector
from datadog import statsd

class DataDogCollector:
    def record_duration(self, function_name: str, duration_seconds: float) -> None:
        statsd.histogram('exc2issue.duration', duration_seconds, tags=[f'function:{function_name}'])
    
    def record_error(self, function_name: str, error_type: str, error: BaseException) -> None:
        statsd.increment('exc2issue.errors', tags=[f'function:{function_name}', f'error_type:{error_type}'])
    
    def record_success(self, function_name: str) -> None:
        statsd.increment('exc2issue.success', tags=[f'function:{function_name}'])

set_metrics_collector(DataDogCollector())
```

**Important Notes:**
- Bug Hunter never starts HTTP servers or exposes endpoints
- No metrics storage or aggregation is performed by the library
- You control how and where metrics are sent
- If no collector is set, metrics collection is skipped (no errors)
- If metrics collection fails, the decorator continues normally

**MetricsCollector Protocol:**

```python
from typing import Protocol

class MetricsCollector(Protocol):
    """Interface that users implement for their metrics backend"""
    
    def record_duration(self, function_name: str, duration_seconds: float) -> None:
        """Record function execution duration"""
        ...
    
    def record_error(self, function_name: str, error_type: str, error: BaseException) -> None:
        """Record error occurrence"""
        ...
    
    def record_success(self, function_name: str) -> None:
        """Record successful execution"""
        ...
```

## 🔧 Developer Reference

### Utility Functions

For advanced usage or custom integrations, Bug Hunter provides utility functions:

```python
from exc2issue.utils import (
    generate_deterministic_title,
    sanitize_function_name,
    validate_title_format
)

# Generate deterministic title
title = generate_deterministic_title("my_func", "ValueError", "Invalid input provided")
# Result: "[EXCEPTION]-[my_func]-[ValueError]"

# Generate log pattern title
log_title = generate_deterministic_title("connect_db", "Log", "Connection failed after 30 seconds")
# Result: "[LOG-ERROR]-[connect_db]-[Connection_failed_after_{number}_seconds]"

# Sanitize problematic function names
safe_name = sanitize_function_name("<lambda>")
# Result: "lambda"

# Validate title format
is_valid = validate_title_format("[EXCEPTION]-[my_func]-[ValueError]")
# Result: True
```

### Title Generation Logic

1. **Function Name Sanitization**: Removes problematic characters like `<>`, handles special cases like `<module>`
2. **Exception Handling**: Uses actual exception type (ValueError, TypeError) for maximum clarity
3. **Log Pattern Extraction**: Replaces variable values with descriptive placeholders (`{number}`, `{email}`, `{time}`)
4. **Format Assembly**: Combines category, function name, and exception type or message pattern

## 📊 Examples

### Exception Handling

```python
@exc2issue(labels=["bug"], repository="myorg/myapp")
def divide_numbers(a, b):
    return a / b  # ZeroDivisionError will create an issue

divide_numbers(10, 0)  # Creates: "[EXCEPTION]-[divide_numbers]-[ZeroDivisionError]"
```

### Logger Error Monitoring

```python
import logging

@exc2issue(labels=["error", "database"], repository="myorg/myapp")
def connect_to_database():
    logger = logging.getLogger(__name__)
    try:
        # Database connection logic
        db.connect()
    except ConnectionError:
        logger.error("Failed to connect to database after 3 retries")
        # This creates an issue even without raising an exception
```

## 🏗️ Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/exc2issue.git
cd exc2issue

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
ruff format src/
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/exc2issue --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_decorator.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Run linting: `ruff check src/ && mypy src/`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📋 Requirements

- Python 3.12+
- GitHub Personal Access Token
- Google Gemini API Key

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent issue descriptions
- GitHub API for seamless issue creation
- The Python community for excellent testing and development tools

---

**Happy Bug Hunting! 🐛🔫**
