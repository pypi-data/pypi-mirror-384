# Date and Time Validation

**Validate dates, times, and timestamps with contracts for reliable scheduling and event handling.**

---

## Problem

Date and time validation is critical for:
- Event scheduling
- Booking systems
- Deadlines and expiration
- Historical data
- Future planning

**Bad approach:**
```python
# Python: No validation
def schedule_meeting(date: str, time: str):
    # Accepts "99/99/9999" and "25:99"
    # No timezone handling
    # No range checking
    meeting = create_meeting(date, time)
```

---

## Solution

Use contracts to enforce valid date/time ranges:

```promptware
function schedule_meeting(
    year: Int,
    month: Int,
    day: Int,
    hour: Int,
    minute: Int
) -> String
  requires:
    year >= 2024
    year <= 2100
    month >= 1
    month <= 12
    day >= 1
    day <= 31
    hour >= 0
    hour <= 23
    minute >= 0
    minute <= 59
  do
    return String(year) + "-" + String(month) + "-" + String(day) +
           " " + String(hour) + ":" + String(minute)
  end
end
```

---

## Basic Date Validation

### Valid Date Components

```promptware
function is_valid_date(year: Int, month: Int, day: Int) -> Bool
  do
    # Year range
    if year < 1900 or year > 2100:
      return false
    end

    # Month range
    if month < 1 or month > 12:
      return false
    end

    # Day range (simplified)
    if day < 1 or day > 31:
      return false
    end

    # Month-specific day limits
    if month == 2 and day > 29:
      return false
    end

    if (month == 4 or month == 6 or month == 9 or month == 11) and day > 30:
      return false
    end

    return true
  end
end
```

### Leap Year Handling

```promptware
function is_leap_year(year: Int) -> Bool
  requires:
    year > 0
  do
    if year % 400 == 0:
      return true
    end

    if year % 100 == 0:
      return false
    end

    if year % 4 == 0:
      return true
    end

    return false
  end
end

function days_in_month(year: Int, month: Int) -> Int
  requires:
    year > 0
    month >= 1
    month <= 12
  ensures:
    result >= 28
    result <= 31
  do
    if month == 2:
      if is_leap_year(year):
        return 29
      else:
        return 28
      end
    else if month == 4 or month == 6 or month == 9 or month == 11:
      return 30
    else:
      return 31
    end
  end
end
```

---

## Time Validation

### 24-Hour Format

```promptware
function validate_time_24h(hour: Int, minute: Int, second: Int) -> Result<String, String>
  do
    if hour < 0 or hour > 23:
      return Err("Hour must be 0-23, got: " + String(hour))
    end

    if minute < 0 or minute > 59:
      return Err("Minute must be 0-59, got: " + String(minute))
    end

    if second < 0 or second > 59:
      return Err("Second must be 0-59, got: " + String(second))
    end

    return Ok(String(hour) + ":" + String(minute) + ":" + String(second))
  end
end
```

### 12-Hour Format with AM/PM

```promptware
function validate_time_12h(
    hour: Int,
    minute: Int,
    am_pm: String
) -> Result<String, String>
  requires:
    len(am_pm) > 0
  do
    if hour < 1 or hour > 12:
      return Err("Hour must be 1-12, got: " + String(hour))
    end

    if minute < 0 or minute > 59:
      return Err("Minute must be 0-59, got: " + String(minute))
    end

    if am_pm != "AM" and am_pm != "PM":
      return Err("Period must be AM or PM, got: " + am_pm)
    end

    return Ok(String(hour) + ":" + String(minute) + " " + am_pm)
  end
end
```

---

## Date Range Validation

### Future Dates Only

```promptware
function validate_future_date(
    year: Int,
    month: Int,
    day: Int,
    current_year: Int,
    current_month: Int,
    current_day: Int
) -> Result<String, String>
  requires:
    is_valid_date(year, month, day)
    is_valid_date(current_year, current_month, current_day)
  do
    # Compare year
    if year < current_year:
      return Err("Date is in the past")
    end

    if year == current_year:
      # Compare month
      if month < current_month:
        return Err("Date is in the past")
      end

      if month == current_month:
        # Compare day
        if day < current_day:
          return Err("Date is in the past")
        end

        if day == current_day:
          return Err("Date must be in the future")
        end
      end
    end

    return Ok(String(year) + "-" + String(month) + "-" + String(day))
  end
end
```

### Date Within Range

```promptware
function validate_date_range(
    year: Int,
    month: Int,
    day: Int,
    min_year: Int,
    max_year: Int
) -> Result<String, String>
  requires:
    is_valid_date(year, month, day)
    min_year <= max_year
  do
    if year < min_year:
      return Err("Date too early (min year: " + String(min_year) + ")")
    end

    if year > max_year:
      return Err("Date too late (max year: " + String(max_year) + ")")
    end

    return Ok(String(year) + "-" + String(month) + "-" + String(day))
  end
end
```

---

## ISO 8601 Format

### Validate ISO Date String

```promptware
function validate_iso_date(date_str: String) -> Result<String, String>
  requires:
    len(date_str) > 0
  do
    # Expected format: YYYY-MM-DD
    if len(date_str) != 10:
      return Err("ISO date must be 10 characters (YYYY-MM-DD)")
    end

    # Check separators
    if date_str[4] != '-' or date_str[7] != '-':
      return Err("ISO date must use - separators")
    end

    # Extract components (simplified parsing)
    let year_str = date_str.substring(0, 4)
    let month_str = date_str.substring(5, 7)
    let day_str = date_str.substring(8, 10)

    # Validate format contains digits
    # (actual parsing would convert to int)

    return Ok(date_str)
  end
end
```

---

## Business Days

### Skip Weekends

```promptware
function is_weekday(year: Int, month: Int, day: Int) -> Bool
  requires:
    is_valid_date(year, month, day)
  do
    # Day of week calculation (simplified)
    # 0 = Monday, 6 = Sunday
    # (Real implementation would use proper algorithm)

    let day_of_week = ((year + month + day) % 7)

    # 5 = Saturday, 6 = Sunday
    if day_of_week == 5 or day_of_week == 6:
      return false
    end

    return true
  end
end

function validate_business_day(
    year: Int,
    month: Int,
    day: Int
) -> Result<String, String>
  requires:
    is_valid_date(year, month, day)
  do
    if not is_weekday(year, month, day):
      return Err("Date must be a weekday (Mon-Fri)")
    end

    return Ok(String(year) + "-" + String(month) + "-" + String(day))
  end
end
```

---

## Duration Validation

### Validate Time Duration

```promptware
function validate_duration_hours(hours: Int) -> Result<Int, String>
  do
    if hours < 0:
      return Err("Duration cannot be negative")
    end

    if hours > 8760:  # Max hours in a year
      return Err("Duration too long (max 1 year)")
    end

    return Ok(hours)
  end
end

function validate_meeting_duration(minutes: Int) -> Result<Int, String>
  do
    if minutes <= 0:
      return Err("Meeting must be at least 1 minute")
    end

    if minutes > 480:  # 8 hours
      return Err("Meeting too long (max 8 hours)")
    end

    # Round to nearest 15 minutes
    if minutes % 15 != 0:
      return Err("Duration must be in 15-minute increments")
    end

    return Ok(minutes)
  end
end
```

---

## Integration Examples

### Event Booking System

```python
# Python
from datetime_validation import (
    validate_future_date,
    validate_time_24h,
    validate_meeting_duration,
    Ok, Err
)

class EventBooking:
    def book_event(
        self,
        year: int, month: int, day: int,
        hour: int, minute: int,
        duration_minutes: int
    ):
        # Validate future date
        date_result = validate_future_date(
            year, month, day,
            2025, 10, 15  # Current date
        )
        if isinstance(date_result, Err):
            raise ValueError(f"Invalid date: {date_result.error}")

        # Validate time
        time_result = validate_time_24h(hour, minute, 0)
        if isinstance(time_result, Err):
            raise ValueError(f"Invalid time: {time_result.error}")

        # Validate duration
        duration_result = validate_meeting_duration(duration_minutes)
        if isinstance(duration_result, Err):
            raise ValueError(f"Invalid duration: {duration_result.error}")

        # Book event
        return {
            "date": date_result.value,
            "time": time_result.value,
            "duration": duration_result.value
        }
```

### API Endpoint

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class EventRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    duration_minutes: int

@app.post("/events")
def create_event(event: EventRequest):
    booking = EventBooking()

    try:
        result = booking.book_event(
            event.year, event.month, event.day,
            event.hour, event.minute,
            event.duration_minutes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Common Pitfalls

### ❌ Forgetting Leap Years

```promptware
# Bad: Always uses 28 for February
function days_in_february_bad() -> Int
  do
    return 28  # Wrong for leap years!
  end
end
```

### ❌ No Timezone Handling

```promptware
# Bad: Assumes local time without timezone
function schedule_bad(hour: Int) -> String
  do
    return "Meeting at " + String(hour) + ":00"
    # What timezone? Users will be confused
  end
end
```

### ✅ Good Pattern

```promptware
function schedule_good(hour: Int, timezone: String) -> String
  requires:
    hour >= 0
    hour <= 23
    len(timezone) > 0
  do
    return "Meeting at " + String(hour) + ":00 " + timezone
  end
end
```

---

## Testing

```python
# Python (pytest)
import pytest
from datetime_validation import *

def test_valid_dates():
    assert is_valid_date(2025, 1, 15) == True
    assert is_valid_date(2024, 2, 29) == True  # Leap year
    assert is_valid_date(2025, 2, 29) == False  # Not leap year

def test_leap_years():
    assert is_leap_year(2024) == True
    assert is_leap_year(2100) == False
    assert is_leap_year(2000) == True

def test_days_in_month():
    assert days_in_month(2024, 2) == 29  # Leap year
    assert days_in_month(2025, 2) == 28
    assert days_in_month(2025, 4) == 30
    assert days_in_month(2025, 1) == 31

def test_future_dates():
    result = validate_future_date(
        2026, 1, 1,  # Future date
        2025, 10, 15  # Current date
    )
    assert isinstance(result, Ok)

    result = validate_future_date(
        2024, 1, 1,  # Past date
        2025, 10, 15  # Current date
    )
    assert isinstance(result, Err)
```

---

## See Also

- [Positive Numbers](positive-numbers.md) - Numeric validation
- [Custom Validators](custom-validators.md) - Build custom validators
- [API Rate Limiting](../advanced/retry-with-backoff.md) - Time-based patterns

---

**Difficulty:** Intermediate
**Time:** 20 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
