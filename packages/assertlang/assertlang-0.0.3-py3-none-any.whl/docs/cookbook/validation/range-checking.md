# Range Checking

**Validate that values fall within acceptable minimum and maximum bounds.**

---

## Problem

Values often have natural bounds:
- Age: 0-150
- Percentage: 0-100
- Temperature: -273.15°C (absolute zero) to upper limit
- Array indices: 0 to length-1
- Port numbers: 0-65535
- HTTP status codes: 100-599

**Bad approach:**
```python
# Python: No bounds checking
def set_volume(level: int):
    # Accepts -1000 or 1000000
    # Causes hardware damage or crashes
    speaker.volume = level
```

---

## Solution

Use contracts to enforce min/max bounds:

```promptware
function set_volume(level: Int) -> Int
  requires:
    level >= 0
    level <= 100
  ensures:
    result >= 0
    result <= 100
  do
    return level
  end
end
```

---

## Basic Range Patterns

### Integer Range

```promptware
function validate_range(
    value: Int,
    min_val: Int,
    max_val: Int
) -> Result<Int, String>
  requires:
    min_val <= max_val
  do
    if value < min_val:
      return Err("Value " + String(value) + " below minimum " + String(min_val))
    end

    if value > max_val:
      return Err("Value " + String(value) + " above maximum " + String(max_val))
    end

    return Ok(value)
  end
end
```

### Float Range

```promptware
function validate_float_range(
    value: Float,
    min_val: Float,
    max_val: Float
) -> Result<Float, String>
  requires:
    min_val <= max_val
  do
    if value < min_val:
      return Err("Value below minimum")
    end

    if value > max_val:
      return Err("Value above maximum")
    end

    return Ok(value)
  end
end
```

---

## Common Range Patterns

### Percentage (0-100)

```promptware
function validate_percentage(value: Float) -> Result<Float, String>
  do
    if value < 0.0:
      return Err("Percentage cannot be negative")
    end

    if value > 100.0:
      return Err("Percentage cannot exceed 100%")
    end

    return Ok(value)
  end
end
```

### Age Validation

```promptware
function validate_age(age: Int) -> Result<Int, String>
  do
    return validate_range(age, 0, 150)
  end
end

function validate_adult_age(age: Int, legal_age: Int) -> Result<Int, String>
  requires:
    legal_age > 0
    legal_age <= 150
  do
    let age_result = validate_age(age)

    if age_result is Err(msg):
      return Err(msg)
    end

    if age < legal_age:
      return Err("Must be at least " + String(legal_age) + " years old")
    end

    return Ok(age)
  end
end
```

### Temperature Range

```promptware
function validate_temperature_celsius(temp: Float) -> Result<Float, String>
  do
    # Absolute zero: -273.15°C
    if temp < -273.15:
      return Err("Temperature below absolute zero")
    end

    # Reasonable upper limit for most applications
    if temp > 1000.0:
      return Err("Temperature unrealistically high")
    end

    return Ok(temp)
  end
end
```

### HTTP Status Code

```promptware
function validate_http_status(code: Int) -> Result<Int, String>
  do
    if code < 100:
      return Err("HTTP status code must be >= 100")
    end

    if code > 599:
      return Err("HTTP status code must be <= 599")
    end

    return Ok(code)
  end
end
```

---

## Array Index Bounds

### Safe Array Access

```promptware
function validate_index(
    index: Int,
    array_length: Int
) -> Result<Int, String>
  requires:
    array_length >= 0
  do
    if index < 0:
      return Err("Index cannot be negative")
    end

    if index >= array_length:
      return Err("Index " + String(index) + " out of bounds (length: " + String(array_length) + ")")
    end

    return Ok(index)
  end
end

function safe_get<T>(arr: List<T>, index: Int) -> Result<T, String>
  requires:
    len(arr) >= 0
  do
    let index_result = validate_index(index, len(arr))

    if index_result is Err(msg):
      return Err(msg)
    end

    return Ok(arr[index])
  end
end
```

---

## Inclusive vs Exclusive Ranges

### Inclusive Range [min, max]

```promptware
function in_range_inclusive(
    value: Int,
    min_val: Int,
    max_val: Int
) -> Bool
  requires:
    min_val <= max_val
  do
    return value >= min_val and value <= max_val
  end
end
```

### Exclusive Range (min, max)

```promptware
function in_range_exclusive(
    value: Int,
    min_val: Int,
    max_val: Int
) -> Bool
  requires:
    min_val < max_val
  do
    return value > min_val and value < max_val
  end
end
```

### Half-Open Range [min, max)

```promptware
function in_range_half_open(
    value: Int,
    min_val: Int,
    max_val: Int
) -> Bool
  requires:
    min_val < max_val
  do
    return value >= min_val and value < max_val
  end
end
```

---

## Multi-Range Validation

### Non-Contiguous Ranges

```promptware
function validate_port_number(port: Int) -> Result<Int, String>
  do
    # Valid port range: 0-65535
    if port < 0:
      return Err("Port number cannot be negative")
    end

    if port > 65535:
      return Err("Port number cannot exceed 65535")
    end

    # Warn about privileged ports (0-1023)
    if port >= 0 and port <= 1023:
      # Note: This is valid but requires root privileges
      return Ok(port)
    end

    return Ok(port)
  end
end
```

### Business Hours Range

```promptware
function validate_business_hour(hour: Int) -> Result<Int, String>
  do
    if hour < 0 or hour > 23:
      return Err("Hour must be 0-23")
    end

    # Business hours: 9 AM - 5 PM
    if hour < 9 or hour >= 17:
      return Err("Outside business hours (9 AM - 5 PM)")
    end

    return Ok(hour)
  end
end
```

---

## Real-World Examples

### Thermostat Control

```python
# Python
from range_validation import validate_float_range, Err

class Thermostat:
    def __init__(self):
        self.temperature = 20.0  # Default 20°C

    def set_temperature(self, target: float) -> dict:
        """Set thermostat temperature with validation."""

        # Validate range: 15°C - 30°C
        result = validate_float_range(target, 15.0, 30.0)

        if isinstance(result, Err):
            return {
                "success": False,
                "error": result.error,
                "current_temperature": self.temperature
            }

        self.temperature = result.value

        return {
            "success": True,
            "temperature": self.temperature
        }

# Usage
thermostat = Thermostat()

# Valid
response = thermostat.set_temperature(22.5)
assert response["success"] == True

# Too cold
response = thermostat.set_temperature(10.0)
assert response["success"] == False
assert "below minimum" in response["error"]

# Too hot
response = thermostat.set_temperature(35.0)
assert response["success"] == False
assert "above maximum" in response["error"]
```

### Pagination Parameters

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException, Query
from range_validation import validate_range, Err

app = FastAPI()

@app.get("/items")
def list_items(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Items per page")
):
    """List items with validated pagination."""

    # Validate page (min: 1, max: 10000)
    page_result = validate_range(page, 1, 10000)
    if isinstance(page_result, Err):
        raise HTTPException(status_code=400, detail=page_result.error)

    # Validate page_size (min: 1, max: 100)
    size_result = validate_range(page_size, 1, 100)
    if isinstance(size_result, Err):
        raise HTTPException(status_code=400, detail=size_result.error)

    # Fetch items
    offset = (page_result.value - 1) * size_result.value
    items = fetch_items(offset, size_result.value)

    return {
        "page": page_result.value,
        "page_size": size_result.value,
        "items": items
    }
```

### Rating System

```python
# Python
from range_validation import validate_range, Err

def submit_rating(product_id: str, rating: int) -> dict:
    """Submit product rating (1-5 stars)."""

    # Validate rating: 1-5
    rating_result = validate_range(rating, 1, 5)

    if isinstance(rating_result, Err):
        return {
            "success": False,
            "error": f"Rating must be 1-5 stars: {rating_result.error}"
        }

    # Save rating
    save_rating(product_id, rating_result.value)

    return {
        "success": True,
        "product_id": product_id,
        "rating": rating_result.value
    }
```

---

## Common Pitfalls

### ❌ Off-by-One Errors

```promptware
# Bad: Allows index == length (out of bounds!)
function validate_index_bad(index: Int, length: Int) -> Bool
  do
    return index >= 0 and index <= length  # Should be: index < length
  end
end
```

### ✅ Correct Bounds

```promptware
# Good: index must be < length
function validate_index_good(index: Int, length: Int) -> Result<Int, String>
  do
    if index < 0 or index >= length:
      return Err("Index out of bounds")
    end
    return Ok(index)
  end
end
```

### ❌ Swapped Min/Max

```promptware
# Bad: No validation that min <= max
function validate_bad(value: Int, min_val: Int, max_val: Int) -> Bool
  do
    return value >= min_val and value <= max_val
    # What if min_val > max_val? Always false!
  end
end
```

### ✅ Validate Min/Max

```promptware
# Good: Ensure min <= max
function validate_good(value: Int, min_val: Int, max_val: Int) -> Result<Int, String>
  requires:
    min_val <= max_val
  do
    if value < min_val or value > max_val:
      return Err("Out of range")
    end
    return Ok(value)
  end
end
```

---

## Integration Patterns

### With Pydantic

```python
# Python
from pydantic import BaseModel, field_validator

class ThermostatSettings(BaseModel):
    target_temperature: float
    min_temp: float = 15.0
    max_temp: float = 30.0

    @field_validator('target_temperature')
    def validate_temperature(cls, v, info):
        min_temp = info.data.get('min_temp', 15.0)
        max_temp = info.data.get('max_temp', 30.0)

        if v < min_temp:
            raise ValueError(f"Temperature below minimum {min_temp}")
        if v > max_temp:
            raise ValueError(f"Temperature above maximum {max_temp}")

        return v
```

### With Database Constraints

```python
# Python (SQLAlchemy)
from sqlalchemy import Column, Integer, CheckConstraint

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint('stock >= 0 AND stock <= 99999', name='check_stock_range'),
    )
```

---

## Testing

```python
# Python (pytest)
import pytest
from range_validation import *

def test_validate_range_valid():
    # Within range
    assert isinstance(validate_range(5, 0, 10), Ok)
    assert isinstance(validate_range(0, 0, 10), Ok)  # Min boundary
    assert isinstance(validate_range(10, 0, 10), Ok)  # Max boundary

def test_validate_range_invalid():
    # Below minimum
    result = validate_range(-1, 0, 10)
    assert isinstance(result, Err)
    assert "below minimum" in result.error

    # Above maximum
    result = validate_range(11, 0, 10)
    assert isinstance(result, Err)
    assert "above maximum" in result.error

def test_validate_percentage():
    assert isinstance(validate_percentage(0.0), Ok)
    assert isinstance(validate_percentage(50.0), Ok)
    assert isinstance(validate_percentage(100.0), Ok)

    assert isinstance(validate_percentage(-0.1), Err)
    assert isinstance(validate_percentage(100.1), Err)

def test_validate_age():
    assert isinstance(validate_age(0), Ok)
    assert isinstance(validate_age(25), Ok)
    assert isinstance(validate_age(150), Ok)

    assert isinstance(validate_age(-1), Err)
    assert isinstance(validate_age(151), Err)

def test_safe_array_access():
    arr = [10, 20, 30, 40, 50]

    # Valid indices
    result = safe_get(arr, 0)
    assert isinstance(result, Ok)
    assert result.value == 10

    result = safe_get(arr, 4)
    assert isinstance(result, Ok)
    assert result.value == 50

    # Invalid indices
    assert isinstance(safe_get(arr, -1), Err)
    assert isinstance(safe_get(arr, 5), Err)
    assert isinstance(safe_get(arr, 100), Err)

def test_validate_range_precondition():
    # Should fail precondition: min > max
    with pytest.raises(AssertionError):
        validate_range(5, 10, 0)
```

---

## Performance Optimization

### Disable Contracts in Production

```python
# Development: Full validation
import os
os.environ['PW_DISABLE_CONTRACTS'] = '0'

# Production: Skip contract checks for performance
os.environ['PW_DISABLE_CONTRACTS'] = '1'

# Function still returns Result<T,E> for error handling
result = validate_range(value, min_val, max_val)
```

### Inline Range Checks

For hot paths, inline simple range checks:

```python
# Instead of function call
def process_fast(value: int):
    # Inline check (faster)
    if value < 0 or value > 100:
        raise ValueError("Out of range")
    # Process value
```

---

## See Also

- [Positive Numbers](positive-numbers.md) - Specific range: > 0
- [Enum Validation](enum-validation.md) - Discrete value sets
- [Array Bounds](array-bounds.md) - Index validation patterns
- [Custom Validators](custom-validators.md) - Build reusable validators

---

**Difficulty:** Beginner
**Time:** 5 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
