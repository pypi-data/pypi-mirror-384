# Builder Pattern with Contracts

**Ensure complete object construction with validated builder pattern - prevent partially initialized objects.**

---

## Problem

Complex objects need multi-step construction:
- Optional fields can be forgotten
- Required fields left uninitialized
- Invalid combinations of fields
- Hard to enforce invariants during construction
- Partially constructed objects escape

**Bad approach:**
```python
# Python: Manual construction
class User:
    def __init__(self):
        self.name = None  # Might forget to set!
        self.email = None
        self.password_hash = None

user = User()
user.name = "John"
# Forgot email and password! Object invalid!
save_user(user)  # Crashes!
```

**Issues:**
- Forgot required fields
- No validation until use
- Partially constructed objects
- Hard to track what's required

---

## Solution

Use builder pattern with contracts:

```promptware
type UserBuilder:
  name: Option<String>
  email: Option<String>
  password_hash: Option<String>
  age: Option<Int>
end

type User:
  name: String
  email: String
  password_hash: String
  age: Option<Int>
end

function build_user(builder: UserBuilder) -> Result<User, List<String>>
  do
    let errors = []

    # Validate required fields are present
    if builder.name is None:
      errors = errors + ["Name is required"]
    end

    if builder.email is None:
      errors = errors + ["Email is required"]
    end

    if builder.password_hash is None:
      errors = errors + ["Password hash is required"]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    # Extract required fields (guaranteed Some after validation)
    let name = if builder.name is Some(n): n else: ""
    let email = if builder.email is Some(e): e else: ""
    let password = if builder.password_hash is Some(p): p else: ""

    # Validate extracted values
    if len(name) == 0:
      errors = errors + ["Name cannot be empty"]
    end

    if not ("@" in email):
      errors = errors + ["Invalid email format"]
    end

    if len(password) < 8:
      errors = errors + ["Password hash too short"]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    # Build final user
    return Ok(User(
      name=name,
      email=email,
      password_hash=password,
      age=builder.age
    ))
  end
end
```

**Usage:**
```python
# Python
from user_builder import UserBuilder, build_user, Err

# Build user step by step
builder = UserBuilder(
    name=Some("John Doe"),
    email=Some("john@example.com"),
    password_hash=Some("hashed_password_12345678"),
    age=Some(30)
)

# Contract validates all required fields present
result = build_user(builder)

if isinstance(result, Err):
    print(f"Build failed: {result.error}")
else:
    user = result.value
    print(f"User created: {user.name}")
```

---

## Fluent Builder API

```promptware
type ConfigBuilder:
  host: Option<String>
  port: Option<Int>
  timeout_ms: Option<Int>
  retries: Option<Int>
end

type Config:
  host: String
  port: Int
  timeout_ms: Int
  retries: Int
end

function set_host(builder: ConfigBuilder, host: String) -> ConfigBuilder
  requires:
    len(host) > 0
  do
    return ConfigBuilder(
      host=Some(host),
      port=builder.port,
      timeout_ms=builder.timeout_ms,
      retries=builder.retries
    )
  end
end

function set_port(builder: ConfigBuilder, port: Int) -> ConfigBuilder
  requires:
    port > 0
    port <= 65535
  do
    return ConfigBuilder(
      host=builder.host,
      port=Some(port),
      timeout_ms=builder.timeout_ms,
      retries=builder.retries
    )
  end
end

function build_config(builder: ConfigBuilder) -> Result<Config, List<String>>
  do
    let errors = []

    # Required fields
    if builder.host is None:
      errors = errors + ["Host required"]
    end

    if builder.port is None:
      errors = errors + ["Port required"]
    end

    # Optional fields with defaults
    let timeout = if builder.timeout_ms is Some(t): t else: 5000
    let retries = if builder.retries is Some(r): r else: 3

    if len(errors) > 0:
      return Err(errors)
    end

    # Extract required fields
    let host = if builder.host is Some(h): h else: ""
    let port = if builder.port is Some(p): p else: 0

    return Ok(Config(
      host=host,
      port=port,
      timeout_ms=timeout,
      retries=retries
    ))
  end
end
```

**Fluent Usage:**
```python
# Python
from config_builder import *

# Empty builder
builder = ConfigBuilder(
    host=None_(),
    port=None_(),
    timeout_ms=None_(),
    retries=None_()
)

# Fluent API
builder = set_host(builder, "localhost")
builder = set_port(builder, 8080)

result = build_config(builder)

if isinstance(result, Ok):
    config = result.value
    print(f"Config: {config.host}:{config.port}")
```

---

## Validation During Construction

```promptware
type EmailConfig:
  smtp_host: String
  smtp_port: Int
  username: String
  password: String
  use_tls: Bool
end

type EmailConfigBuilder:
  smtp_host: Option<String>
  smtp_port: Option<Int>
  username: Option<String>
  password: Option<String>
  use_tls: Option<Bool>
end

function validate_email_config_builder(
    builder: EmailConfigBuilder
) -> Result<EmailConfigBuilder, List<String>>
  do
    let errors = []

    # Validate SMTP host if present
    if builder.smtp_host is Some(host):
      if len(host) == 0:
        errors = errors + ["SMTP host cannot be empty"]
      end
    end

    # Validate port if present
    if builder.smtp_port is Some(port):
      if port <= 0 or port > 65535:
        errors = errors + ["Invalid SMTP port: " + String(port)]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(builder)
  end
end

function build_email_config(
    builder: EmailConfigBuilder
) -> Result<EmailConfig, List<String>>
  do
    # Validate builder first
    let validation_result = validate_email_config_builder(builder)

    if validation_result is Err(msgs):
      return Err(msgs)
    end

    # Check required fields
    let errors = []

    if builder.smtp_host is None:
      errors = errors + ["SMTP host required"]
    end

    if builder.smtp_port is None:
      errors = errors + ["SMTP port required"]
    end

    if builder.username is None:
      errors = errors + ["Username required"]
    end

    if builder.password is None:
      errors = errors + ["Password required"]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    # Extract fields (guaranteed Some)
    let host = if builder.smtp_host is Some(h): h else: ""
    let port = if builder.smtp_port is Some(p): p else: 0
    let user = if builder.username is Some(u): u else: ""
    let pass = if builder.password is Some(p): p else: ""
    let tls = if builder.use_tls is Some(t): t else: true

    return Ok(EmailConfig(
      smtp_host=host,
      smtp_port=port,
      username=user,
      password=pass,
      use_tls=tls
    ))
  end
end
```

---

## Real-World Example: HTTP Request Builder

```promptware
type HttpMethod:
  is GET
  is POST
  is PUT
  is DELETE
end

type HttpRequest:
  method: HttpMethod
  url: String
  headers: Map<String, String>
  body: Option<String>
  timeout_ms: Int
end

type HttpRequestBuilder:
  method: Option<HttpMethod>
  url: Option<String>
  headers: Map<String, String>
  body: Option<String>
  timeout_ms: Option<Int>
end

function add_header(
    builder: HttpRequestBuilder,
    key: String,
    value: String
) -> Result<HttpRequestBuilder, String>
  requires:
    len(key) > 0
    len(value) > 0
  do
    let new_headers = builder.headers
    new_headers[key] = value

    return Ok(HttpRequestBuilder(
      method=builder.method,
      url=builder.url,
      headers=new_headers,
      body=builder.body,
      timeout_ms=builder.timeout_ms
    ))
  end
end

function build_http_request(
    builder: HttpRequestBuilder
) -> Result<HttpRequest, List<String>>
  do
    let errors = []

    # Required fields
    if builder.method is None:
      errors = errors + ["HTTP method required"]
    end

    if builder.url is None:
      errors = errors + ["URL required"]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    # Extract required fields
    let method = if builder.method is Some(m): m else: HttpMethod.GET
    let url = if builder.url is Some(u): u else: ""

    # Validate URL format
    if not (url.startswith("http://") or url.startswith("https://")):
      errors = errors + ["URL must start with http:// or https://"]
    end

    # Default timeout
    let timeout = if builder.timeout_ms is Some(t): t else: 30000

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(HttpRequest(
      method=method,
      url=url,
      headers=builder.headers,
      body=builder.body,
      timeout_ms=timeout
    ))
  end
end
```

**Python Integration:**
```python
# http_client.py
from http_request_builder import *

# Create builder
builder = HttpRequestBuilder(
    method=None_(),
    url=None_(),
    headers={},
    body=None_(),
    timeout_ms=None_()
)

# Set method and URL
builder.method = Some(HttpMethod.POST)
builder.url = Some("https://api.example.com/users")

# Add headers
result = add_header(builder, "Content-Type", "application/json")
if isinstance(result, Ok):
    builder = result.value

result = add_header(builder, "Authorization", "Bearer token123")
if isinstance(result, Ok):
    builder = result.value

# Set body
builder.body = Some('{"name": "John Doe"}')

# Build request
request_result = build_http_request(builder)

if isinstance(request_result, Err):
    print(f"Build failed: {request_result.error}")
else:
    request = request_result.value
    print(f"Request: {request.method.value} {request.url}")
    print(f"Headers: {request.headers}")
```

---

## Testing

```python
# test_builder_pattern.py
import pytest
from user_builder import *

def test_build_user_valid():
    builder = UserBuilder(
        name=Some("John"),
        email=Some("john@example.com"),
        password_hash=Some("hashed12345678"),
        age=Some(30)
    )

    result = build_user(builder)
    assert isinstance(result, Ok)
    assert result.value.name == "John"

def test_build_user_missing_name():
    builder = UserBuilder(
        name=None_(),
        email=Some("john@example.com"),
        password_hash=Some("hashed12345678"),
        age=None_()
    )

    result = build_user(builder)
    assert isinstance(result, Err)
    assert any("Name is required" in err for err in result.error)

def test_build_config_with_defaults():
    builder = ConfigBuilder(
        host=Some("localhost"),
        port=Some(8080),
        timeout_ms=None_(),  # Should use default
        retries=None_()  # Should use default
    )

    result = build_config(builder)
    assert isinstance(result, Ok)
    assert result.value.timeout_ms == 5000  # Default
    assert result.value.retries == 3  # Default
```

---

## Common Pitfalls

### ❌ No Validation on Build

```python
# Bad: Builds invalid object
class User:
    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

user = User()  # Invalid! Missing required fields
```

### ✅ Contract Enforces Completeness

```promptware
# Good: Contract prevents incomplete objects
function build_user(builder: UserBuilder) -> Result<User, List<String>>
  do
    if builder.name is None:
      return Err(["Name required"])
    end

    # ... more validation ...

    return Ok(User(...))
  end
end
```

### ❌ Mutable Builder State

```python
# Bad: Builder state can be mutated unsafely
builder.name = None  # Breaks invariants!
```

### ✅ Immutable Builder Updates

```promptware
# Good: Builder updates return new builder
function set_name(builder: Builder, name: String) -> Builder
  do
    return Builder(name=Some(name), ...)  # New builder
  end
end
```

---

## See Also

- [Factory Pattern](factory-pattern.md) - Object creation patterns
- [Nested Validation](../validation/nested-validation.md) - Complex object validation
- [Multi-Field Constraints](../validation/multi-field-constraints.md) - Cross-field rules
- [State Machines](state-machines.md) - State transition validation

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Design Patterns
**Last Updated:** 2025-10-15
