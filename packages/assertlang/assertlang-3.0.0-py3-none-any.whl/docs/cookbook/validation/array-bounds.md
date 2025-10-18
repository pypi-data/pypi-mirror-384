# Recipe: Array Bounds Validation

**Problem:** Prevent array index out of bounds errors and ensure collections have expected sizes.

**Difficulty:** Beginner
**Time:** 10 minutes

---

## The Problem

Array operations fail without bounds checking:
- **Index out of bounds**: Accessing `arr[5]` when `len(arr) = 3`
- **Empty arrays**: Operating on empty collections
- **Wrong sizes**: Expected array of 5, got array of 2
- **Runtime crashes**: Index errors discovered at runtime, not compile time

---

## Solution

```al
function get_first_item(items: array<string>) -> string {
    @requires non_empty: len(items) > 0

    @ensures result_from_array: len(result) >= 0

    let first = items[0];
    return first;
}

function get_item_at_index(
    items: array<string>,
    index: int
) -> string {
    @requires non_empty: len(items) > 0
    @requires valid_index: index >= 0 && index < len(items)

    @ensures result_exists: len(result) >= 0

    let item = items[index];
    return item;
}

function process_batch(items: array<string>) -> array<string> {
    @requires min_size: len(items) >= 3
    @requires max_size: len(items) <= 1000

    @ensures same_size: len(result) == len(items)
    @ensures all_processed: len(result) > 0

    let processed = items.map(|item| item.upper());
    return processed;
}
```

**Generated Python:**
```python
def get_first_item(items: list[str]) -> str:
    check_precondition(len(items) > 0, "non_empty",
        f"Array must not be empty, got length {len(items)}")

    first = items[0]

    check_postcondition(len(first) >= 0, "result_from_array")
    return first

def get_item_at_index(items: list[str], index: int) -> str:
    check_precondition(len(items) > 0, "non_empty")
    check_precondition(
        index >= 0 and index < len(items),
        "valid_index",
        f"Index {index} out of bounds for array length {len(items)}"
    )

    item = items[index]

    check_postcondition(len(item) >= 0, "result_exists")
    return item

def process_batch(items: list[str]) -> list[str]:
    check_precondition(len(items) >= 3, "min_size",
        f"Batch too small: {len(items)} items (minimum 3)")
    check_precondition(len(items) <= 1000, "max_size",
        f"Batch too large: {len(items)} items (maximum 1000)")

    processed = [item.upper() for item in items]

    check_postcondition(len(processed) == len(items), "same_size")
    check_postcondition(len(processed) > 0, "all_processed")
    return processed
```

---

## Explanation

**Three validation patterns:**

1. **Empty check** - `len(items) > 0` prevents operations on empty arrays
2. **Bounds check** - `index >= 0 && index < len(items)` validates index range
3. **Size constraints** - `len(items) >= 3 && <= 1000` enforces batch size limits

**Postconditions verify:**
- Output size matches expectations
- Results not empty
- Transformations preserved size (if expected)

---

## Variations

### Exact Size
```al
@requires exact_size: len(items) == 5
// Array must have exactly 5 elements
```

### Minimum Size Only
```al
@requires has_items: len(items) >= 1
// At least one element
```

### Maximum Size Only
```al
@requires reasonable_size: len(items) <= 10000
// No more than 10K elements
```

### Range Check
```al
@requires size_range: len(items) >= 10 && len(items) <= 100
// Between 10 and 100 elements
```

### Multi-Dimensional Arrays
```al
function process_matrix(matrix: array<array<int>>) -> int {
    @requires not_empty: len(matrix) > 0
    @requires rows_not_empty: len(matrix[0]) > 0
    @requires rectangular: all_rows_same_length(matrix)

    // ... process matrix
}
```

### Safe Slice
```al
function get_slice(
    items: array<string>,
    start: int,
    end: int
) -> array<string> {
    @requires valid_start: start >= 0 && start < len(items)
    @requires valid_end: end >= start && end <= len(items)
    @requires non_empty_slice: end > start

    @ensures result_size: len(result) == (end - start)

    let slice = items[start:end];
    return slice;
}
```

---

## Common Pitfalls

### ❌ Only checking `len() > 0` before indexing
```al
function get_third(items: array<string>) -> string {
    @requires non_empty: len(items) > 0
    return items[2];  // ❌ Crashes if len(items) < 3!
}
```

**Fix**: Check specific index.
```al
@requires has_third: len(items) >= 3
```

---

### ❌ Forgetting zero-based indexing
```al
@requires valid_index: index >= 1 && index <= len(items)  // ❌ Wrong!
```

**Fix**: Use `0` to `len-1`.
```al
@requires valid_index: index >= 0 && index < len(items)  // ✓
```

---

### ❌ No postcondition on transformed arrays
```al
function double_elements(nums: array<int>) -> array<int> {
    @requires non_empty: len(nums) > 0
    // ❌ No postcondition!

    let doubled = nums.map(|n| n * 2);
    return doubled;  // Could return wrong size if bug in map()
}
```

**Fix**: Add size postcondition.
```al
@ensures same_size: len(result) == len(nums)
```

---

### ❌ Mutable array without invariant
```python
class Buffer:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)
        # ❌ No check on maximum size!
```

**Fix**: Add capacity invariant.
```al
@invariant within_capacity: len(items) <= max_capacity
```

---

## Real-World Example

**Batch processing with pagination:**
```al
function process_page(
    all_items: array<string>,
    page_num: int,
    page_size: int
) -> array<string> {
    @requires has_items: len(all_items) > 0
    @requires positive_page: page_num > 0
    @requires valid_page_size: page_size > 0 && page_size <= 100
    @requires page_exists: (page_num - 1) * page_size < len(all_items)

    @ensures result_not_empty: len(result) > 0
    @ensures result_size_valid: len(result) <= page_size

    let start_index = (page_num - 1) * page_size;
    let end_index_candidate = start_index + page_size;
    let end_index = min(end_index_candidate, len(all_items));

    let page = all_items[start_index:end_index];
    return page;
}
```

**Usage:**
```python
from pagination import process_page

items = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]

# ✓ Valid pagination
page_1 = process_page(items, page_num=1, page_size=3)
# Returns: ["a", "b", "c"]

page_2 = process_page(items, page_num=2, page_size=3)
# Returns: ["d", "e", "f"]

page_4 = process_page(items, page_num=4, page_size=3)
# Returns: ["j"] (last page, smaller)

# ❌ Invalid (caught by contracts)
process_page([], 1, 10)          # has_items failed
process_page(items, 0, 10)       # positive_page failed
process_page(items, 1, 500)      # valid_page_size failed
process_page(items, 100, 10)     # page_exists failed
```

---

## Testing Pattern

```python
import pytest
from array_utils import get_item_at_index, process_batch

def test_valid_index_access():
    items = ["a", "b", "c"]
    assert get_item_at_index(items, 0) == "a"
    assert get_item_at_index(items, 2) == "c"

def test_empty_array_rejected():
    with pytest.raises(Exception, match="non_empty"):
        get_item_at_index([], 0)

def test_negative_index_rejected():
    with pytest.raises(Exception, match="valid_index"):
        get_item_at_index(["a", "b"], -1)

def test_out_of_bounds_rejected():
    with pytest.raises(Exception, match="valid_index"):
        get_item_at_index(["a", "b"], 5)

def test_batch_size_constraints():
    # Too small
    with pytest.raises(Exception, match="min_size"):
        process_batch(["a", "b"])  # Need at least 3

    # Valid
    result = process_batch(["a", "b", "c"])
    assert len(result) == 3

    # Too large
    with pytest.raises(Exception, match="max_size"):
        process_batch(["x"] * 1001)  # Max 1000
```

---

## Performance Tip

**Bounds checks are fast**: ~1µs overhead per check, negligible vs actual array operations.

**For tight loops**, consider batch validation:
```al
// Validate once before loop
@requires all_indices_valid: max(indices) < len(items)

for index in indices {
    item = items[index];  // No per-iteration check needed
}
```

---

## See Also

- **[Positive Numbers](positive-numbers.md)** - Numeric bounds validation
- **[Non-Empty Strings](non-empty-strings.md)** - String validation
- **[Range Checking](range-checking.md)** - General min/max patterns
- **[Data Processing Example](../../../examples/real_world/03_data_processing_workflow/)** - Array transformations

---

**Next**: Try [Enum Validation](enum-validation.md) for value set checking →
