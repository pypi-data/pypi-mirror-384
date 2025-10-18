# Enum Validation

**Validate that values match a predefined set of allowed options using enums and contracts.**

---

## Problem

Many fields accept only specific values:
- User roles (admin, user, guest)
- Order statuses (pending, confirmed, shipped, delivered)
- HTTP methods (GET, POST, PUT, DELETE)
- File types (jpg, png, pdf, csv)
- Priority levels (low, medium, high, critical)

**Bad approach:**
```python
# Python: No validation
def set_user_role(role: str):
    # Accepts any string, including typos
    # No compile-time safety
    # No IDE autocomplete
    user.role = role  # What if role = "admni" (typo)?
```

**Issues:**
- Typos accepted ("admni" instead of "admin")
- Invalid values allowed
- No IDE autocomplete
- Hard to discover valid options
- Runtime bugs

---

## Solution

Use AssertLang enums with contract validation:

```promptware
type UserRole:
  is Admin
  is User
  is Guest
end

function set_user_role(role: UserRole) -> Bool
  requires:
    role == UserRole.Admin or
    role == UserRole.User or
    role == UserRole.Guest
  do
    # Type system ensures only valid roles
    return true
  end
end
```

---

## Basic Enum Patterns

### Simple Enum

```promptware
type Status:
  is Pending
  is Active
  is Completed
  is Cancelled
end

function create_task(status: Status) -> String
  requires:
    status != Status.Cancelled  # New tasks can't be cancelled
  do
    return "Task created with status: " + String(status)
  end
end
```

### Enum with Values

```promptware
type Priority:
  is Low = 1
  is Medium = 2
  is High = 3
  is Critical = 4
end

function escalate_if_critical(priority: Priority) -> Bool
  do
    if priority == Priority.Critical:
      return true
    end
    return false
  end
end
```

---

## Validation Patterns

### String to Enum Conversion

```promptware
function parse_user_role(role_str: String) -> Result<UserRole, String>
  requires:
    len(role_str) > 0
  do
    if role_str == "admin":
      return Ok(UserRole.Admin)
    else if role_str == "user":
      return Ok(UserRole.User)
    else if role_str == "guest":
      return Ok(UserRole.Guest)
    else:
      return Err("Invalid role: " + role_str + " (expected: admin, user, guest)")
    end
  end
end
```

**Generated Python:**
```python
from enum import Enum
from typing import Union

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

def parse_user_role(role_str: str) -> Union[Ok[UserRole], Err[str]]:
    assert len(role_str) > 0, "Precondition failed: len(role_str) > 0"

    if role_str == "admin":
        return Ok(UserRole.ADMIN)
    elif role_str == "user":
        return Ok(UserRole.USER)
    elif role_str == "guest":
        return Ok(UserRole.GUEST)
    else:
        return Err(f"Invalid role: {role_str} (expected: admin, user, guest)")
```

### Case-Insensitive Parsing

```promptware
function parse_status_flexible(status_str: String) -> Result<Status, String>
  requires:
    len(status_str) > 0
  do
    let lower = status_str.lower()

    if lower == "pending":
      return Ok(Status.Pending)
    else if lower == "active":
      return Ok(Status.Active)
    else if lower == "completed":
      return Ok(Status.Completed)
    else if lower == "cancelled" or lower == "canceled":
      return Ok(Status.Cancelled)
    else:
      return Err("Invalid status: " + status_str)
    end
  end
end
```

---

## State Transitions

### Valid Transitions Only

```promptware
type OrderStatus:
  is Pending
  is Confirmed
  is Shipped
  is Delivered
  is Cancelled
end

function can_transition(
    current: OrderStatus,
    next: OrderStatus
) -> Bool
  do
    # Pending -> Confirmed or Cancelled
    if current == OrderStatus.Pending:
      return next == OrderStatus.Confirmed or next == OrderStatus.Cancelled
    end

    # Confirmed -> Shipped or Cancelled
    if current == OrderStatus.Confirmed:
      return next == OrderStatus.Shipped or next == OrderStatus.Cancelled
    end

    # Shipped -> Delivered
    if current == OrderStatus.Shipped:
      return next == OrderStatus.Delivered
    end

    # Terminal states (no transitions)
    if current == OrderStatus.Delivered or current == OrderStatus.Cancelled:
      return false
    end

    return false
  end
end

function transition_order(
    current: OrderStatus,
    next: OrderStatus
) -> Result<OrderStatus, String>
  requires:
    can_transition(current, next)
  ensures:
    result == next if result is Ok
  do
    return Ok(next)
  end
end
```

---

## Permission Checks

### Role-Based Access Control

```promptware
type Permission:
  is Read
  is Write
  is Delete
  is Admin
end

function has_permission(
    role: UserRole,
    required: Permission
) -> Bool
  do
    # Admin has all permissions
    if role == UserRole.Admin:
      return true
    end

    # User has read and write
    if role == UserRole.User:
      if required == Permission.Read or required == Permission.Write:
        return true
      end
      return false
    end

    # Guest has only read
    if role == UserRole.Guest:
      return required == Permission.Read
    end

    return false
  end
end

function perform_action(
    role: UserRole,
    action: Permission
) -> Result<String, String>
  requires:
    has_permission(role, action)
  do
    return Ok("Action allowed: " + String(action))
  end
end
```

---

## Multi-Value Enums

### Flags/Bitfields

```promptware
type FilePermission:
  is Read = 1
  is Write = 2
  is Execute = 4
end

function has_all_permissions(
    granted: Int,
    required: Int
) -> Bool
  requires:
    granted >= 0
    required >= 0
  do
    # Bitwise AND check: (granted & required) == required
    return (granted & required) == required
  end
end

function can_execute_file(permissions: Int) -> Bool
  do
    return has_all_permissions(permissions, FilePermission.Execute)
  end
end
```

---

## Real-World Examples

### Order Processing API

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from order_validation import parse_status_flexible, transition_order, OrderStatus, Err

app = FastAPI()

class OrderStatusUpdate(BaseModel):
    order_id: str
    new_status: str

@app.post("/orders/{order_id}/status")
def update_order_status(order_id: str, update: OrderStatusUpdate):
    # Get current status from database
    current_status = get_current_status(order_id)  # Returns OrderStatus enum

    # Parse new status
    new_status_result = parse_status_flexible(update.new_status)
    if isinstance(new_status_result, Err):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {new_status_result.error}"
        )

    new_status = new_status_result.value

    # Validate transition
    transition_result = transition_order(current_status, new_status)
    if isinstance(transition_result, Err):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current_status} to {new_status}"
        )

    # Update database
    save_status(order_id, new_status)

    return {
        "order_id": order_id,
        "previous_status": current_status.value,
        "new_status": new_status.value
    }
```

### User Management System

```python
# Python
from user_validation import parse_user_role, has_permission, UserRole, Permission, Err

def create_user(email: str, role_str: str):
    """Create user with role validation."""

    # Parse role
    role_result = parse_user_role(role_str)
    if isinstance(role_result, Err):
        raise ValueError(f"Invalid role: {role_result.error}")

    role = role_result.value

    # Create user
    user = User(email=email, role=role)
    return user

def check_access(user: User, resource: str, action: str):
    """Check if user has permission for action."""

    # Map action string to Permission enum
    action_map = {
        "read": Permission.Read,
        "write": Permission.Write,
        "delete": Permission.Delete,
        "admin": Permission.Admin,
    }

    required_permission = action_map.get(action)
    if not required_permission:
        raise ValueError(f"Unknown action: {action}")

    # Check permission
    allowed = has_permission(user.role, required_permission)

    if not allowed:
        raise PermissionError(
            f"User {user.email} (role: {user.role.value}) "
            f"does not have {action} permission"
        )

    return True
```

---

## Common Pitfalls

### ❌ Using Magic Strings

```promptware
# Bad: Using strings instead of enums
function set_role_bad(role: String) -> Bool
  do
    if role == "admin":  # Typo: "admni" accepted!
      return true
    end
    return false
  end
end
```

### ✅ Using Enums

```promptware
# Good: Type-safe enums
function set_role_good(role: UserRole) -> Bool
  do
    if role == UserRole.Admin:  # Compiler catches typos
      return true
    end
    return false
  end
end
```

### ❌ No Validation on Transitions

```promptware
# Bad: Any transition allowed
function transition_bad(current: Status, next: Status) -> Status
  do
    return next  # Can go from Delivered back to Pending!
  end
end
```

### ✅ Validated Transitions

```promptware
# Good: Only valid transitions allowed
function transition_good(current: Status, next: Status) -> Result<Status, String>
  requires:
    can_transition(current, next)
  do
    return Ok(next)
  end
end
```

---

## Integration Patterns

### With Pydantic

```python
# Python
from pydantic import BaseModel, field_validator
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(BaseModel):
    email: str
    role: UserRole

    @field_validator('role')
    def validate_role(cls, v):
        # Pydantic automatically validates enum membership
        return v

# Usage
user = User(email="test@example.com", role="admin")  # Works
user = User(email="test@example.com", role="invalid")  # ValidationError
```

### With Database (SQLAlchemy)

```python
# Python
from sqlalchemy import Column, String, Enum as SQLEnum
import enum

class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)

    def transition_to(self, new_status: OrderStatus):
        # Use AssertLang contract validation
        result = transition_order(self.status, new_status)
        if isinstance(result, Err):
            raise ValueError(result.error)
        self.status = result.value
```

---

## Testing

```python
# Python (pytest)
import pytest
from enum_validation import *

def test_parse_user_role_valid():
    assert isinstance(parse_user_role("admin"), Ok)
    assert isinstance(parse_user_role("user"), Ok)
    assert isinstance(parse_user_role("guest"), Ok)

def test_parse_user_role_invalid():
    result = parse_user_role("invalid")
    assert isinstance(result, Err)
    assert "expected: admin, user, guest" in result.error

def test_status_transitions_valid():
    # Valid transitions
    assert can_transition(OrderStatus.Pending, OrderStatus.Confirmed) == True
    assert can_transition(OrderStatus.Confirmed, OrderStatus.Shipped) == True
    assert can_transition(OrderStatus.Shipped, OrderStatus.Delivered) == True

def test_status_transitions_invalid():
    # Invalid transitions
    assert can_transition(OrderStatus.Pending, OrderStatus.Shipped) == False
    assert can_transition(OrderStatus.Delivered, OrderStatus.Pending) == False
    assert can_transition(OrderStatus.Cancelled, OrderStatus.Confirmed) == False

def test_role_permissions():
    # Admin has all permissions
    assert has_permission(UserRole.Admin, Permission.Read) == True
    assert has_permission(UserRole.Admin, Permission.Write) == True
    assert has_permission(UserRole.Admin, Permission.Delete) == True

    # User has read and write
    assert has_permission(UserRole.User, Permission.Read) == True
    assert has_permission(UserRole.User, Permission.Write) == True
    assert has_permission(UserRole.User, Permission.Delete) == False

    # Guest has only read
    assert has_permission(UserRole.Guest, Permission.Read) == True
    assert has_permission(UserRole.Guest, Permission.Write) == False

def test_transition_order_contract():
    # Valid transition
    result = transition_order(OrderStatus.Pending, OrderStatus.Confirmed)
    assert isinstance(result, Ok)
    assert result.value == OrderStatus.Confirmed

    # Invalid transition (should fail precondition)
    with pytest.raises(AssertionError):
        transition_order(OrderStatus.Delivered, OrderStatus.Pending)
```

---

## Performance Considerations

### Enum Comparison Performance

Enum comparisons are O(1) constant time:
```python
# Both equally fast
if status == OrderStatus.Pending:  # Direct enum comparison
if status.value == "pending":      # String comparison
```

### Large Enum Sets

For enums with many values (100+), consider:
- Using dictionaries for parsing (O(1) lookup)
- Caching validation results
- Disabling contracts in production

```promptware
# Efficient parsing for large enums
function parse_large_enum(value: String) -> Result<LargeEnum, String>
  do
    # Use dictionary-based lookup (generated as hash map in target language)
    let enum_map = {
      "value1": LargeEnum.Value1,
      "value2": LargeEnum.Value2,
      # ... 100+ values
    }

    if value in enum_map:
      return Ok(enum_map[value])
    else:
      return Err("Invalid value: " + value)
    end
  end
end
```

---

## See Also

- [State Machines](../patterns/state-machines.md) - State transition patterns
- [Range Checking](range-checking.md) - Numeric range validation
- [Custom Validators](custom-validators.md) - Build custom validators
- [Conditional Validation](conditional-validation.md) - Multi-field validation

---

**Difficulty:** Beginner
**Time:** 10 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
