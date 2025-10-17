# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of `openai-without-pydantic` seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** Open a Public Issue

Please do not report security vulnerabilities through public GitHub issues. This helps protect users while we work on a fix.

### 2. Report Privately

Send a detailed report to the project maintainer via:
- **GitHub Security Advisory**: Use the "Security" tab → "Report a vulnerability" on this repository
- **Email**: [Add your security contact email here]

### 3. Include Details

Please include the following information:
- Type of vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (if available)
- Your contact information for follow-up

### What to Include in Your Report

A good security report should include:

```
**Vulnerability Type**: [e.g., Code Injection, API Key Exposure, etc.]

**Description**: 
[Clear description of the vulnerability]

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Impact**:
[What an attacker could do with this vulnerability]

**Affected Versions**:
[Which versions are affected]

**Suggested Fix** (optional):
[If you have ideas on how to fix it]

**Environment**:
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- Package version: [e.g., 0.1.0]
```

## Response Timeline

- **Initial Response**: Within 48 hours of report
- **Validation**: Within 1 week
- **Fix Development**: Depends on severity
- **Release**: Coordinated with reporter

## Security Best Practices for Users

### API Key Security

**DO:**
- ✅ Store API keys in environment variables
- ✅ Use `.env` files (add to `.gitignore`)
- ✅ Use secret management services in production
- ✅ Rotate API keys regularly
- ✅ Use different keys for dev/staging/production

**DON'T:**
- ❌ Hard-code API keys in source code
- ❌ Commit API keys to version control
- ❌ Share API keys in public forums
- ❌ Include API keys in logs or error messages

### Example: Secure API Key Handling

```python
import os
from openai_wrapper import ask_ai_question

# ✅ GOOD: Use environment variable
api_key = os.environ.get("OPENAI_API_KEY")

# ✅ GOOD: Use .env file (with python-dotenv)
from dotenv import load_dotenv
load_dotenv()

# ❌ BAD: Hard-coded key
# api_key = "sk-proj-abc123..."  # NEVER DO THIS!
```

### Input Validation

When using this package in production:

```python
def safe_ask_question(user_input: str, context: str) -> str:
    """
    Safely process user input with validation
    """
    # Validate and sanitize inputs
    if not user_input or len(user_input) > 1000:
        raise ValueError("Invalid input length")
    
    if not context or len(context) > 10000:
        raise ValueError("Invalid context length")
    
    # Use the package
    return ask_ai_question(
        input_text=context,
        question_asked=user_input,
        timeout=30  # Prevent hanging requests
    )
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
import time
from functools import wraps

def rate_limit(calls_per_minute: int):
    """Simple rate limiting decorator"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_minute=10)
def safe_ai_call(text: str, question: str) -> str:
    return ask_ai_question(text, question)
```

## Known Security Considerations

### 1. API Key Exposure
- This package requires an OpenAI API key
- Users must secure their keys appropriately
- Never commit keys to version control

### 2. Input Data
- All data sent to OpenAI API is processed externally
- Don't send sensitive/confidential information
- Review OpenAI's data usage policies

### 3. Dependencies
- Package depends on `requests` library
- Keep dependencies updated for security patches
- Run `pip list --outdated` regularly

### 4. Network Security
- All API calls use HTTPS
- Validate SSL certificates
- Consider using proxies in corporate environments

## Vulnerability Disclosure Policy

We follow coordinated vulnerability disclosure:

1. **Report received** → Acknowledge within 48 hours
2. **Validation** → Confirm vulnerability exists
3. **Development** → Create and test fix
4. **Release** → Publish patched version
5. **Disclosure** → Public announcement with credit to reporter

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 0.1.1)
- Documented in CHANGELOG.md
- Announced in GitHub releases
- Tagged with `security` label

## Contact

For security concerns, please contact:
- **GitHub Security Advisory**: Preferred method
- **Email**: [Add your security contact email]

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be credited in:
- Release notes
- CHANGELOG.md
- This security policy (if desired)

Thank you for helping keep `openai-without-pydantic` and its users safe!
