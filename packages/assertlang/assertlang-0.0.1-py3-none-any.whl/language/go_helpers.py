"""
Go Helper Functions Generator

Automatically generates helper functions that Go needs but doesn't have built-in.
These helpers are injected into the generated Go code when needed.

Examples:
- enumerate() - Python's enumerate doesn't exist in Go
- contains() - Check if slice contains element
- set operations - Go uses map[T]bool idiom
- tuple unpacking - Go needs explicit struct unpacking
"""

from typing import Set, List, Dict

# Track which helpers are needed
needed_helpers: Set[str] = set()


def get_enumerate_helper() -> str:
    """
    Generate Go enumerate helper function.

    Python:
        for i, item in enumerate(items):
            ...

    Go equivalent:
        for i, item := range items {
            ...
        }

    Note: Go's range already provides index, so enumerate is unnecessary.
    This is just a marker for translation.
    """
    return """
// enumerate is not needed in Go - use range with index
// for i, item := range items { ... }
""".strip()


def get_contains_helper() -> str:
    """
    Generate Go contains helper for slices.

    Python:
        if x in items:
            ...

    Go equivalent:
        if contains(items, x) {
            ...
        }
    """
    return """
// contains checks if a slice contains an element
func contains(slice []interface{}, elem interface{}) bool {
	for _, item := range slice {
		if item == elem {
			return true
		}
	}
	return false
}
""".strip()


def get_set_helper() -> str:
    """
    Generate Go set operations using map[T]bool idiom.

    Python:
        s = set()
        s.add(item)
        if item in s:
            ...

    Go equivalent:
        s := make(map[interface{}]bool)
        s[item] = true
        if s[item] {
            ...
        }
    """
    return """
// Set type using Go's map idiom
type Set map[interface{}]bool

// NewSet creates a new set
func NewSet() Set {
	return make(Set)
}

// Add adds an element to the set
func (s Set) Add(elem interface{}) {
	s[elem] = true
}

// Contains checks if set contains element
func (s Set) Contains(elem interface{}) bool {
	return s[elem]
}

// Remove removes an element from the set
func (s Set) Remove(elem interface{}) {
	delete(s, elem)
}

// Len returns the number of elements
func (s Set) Len() int {
	return len(s)
}
""".strip()


def get_tuple_helper() -> str:
    """
    Generate Go tuple helper (generic pair struct).

    Python:
        t = (x, y)
        a, b = t

    Go equivalent:
        t := Tuple{x, y}
        a, b := t.First, t.Second
    """
    return """
// Tuple is a generic pair type
type Tuple struct {
	First  interface{}
	Second interface{}
}

// NewTuple creates a new tuple
func NewTuple(first, second interface{}) Tuple {
	return Tuple{First: first, Second: second}
}
""".strip()


def get_zip_helper() -> str:
    """
    Generate Go zip helper.

    Python:
        for a, b in zip(list1, list2):
            ...

    Go equivalent:
        for _, pair := range zip(list1, list2) {
            a, b := pair.First, pair.Second
            ...
        }
    """
    return """
// zip combines two slices into slice of tuples
func zip(a, b []interface{}) []Tuple {
	minLen := len(a)
	if len(b) < minLen {
		minLen = len(b)
	}

	result := make([]Tuple, minLen)
	for i := 0; i < minLen; i++ {
		result[i] = Tuple{a[i], b[i]}
	}
	return result
}
""".strip()


def get_map_helper() -> str:
    """
    Generate Go map helper (not the data structure, the function).

    Python:
        result = map(lambda x: x*2, items)

    Go equivalent:
        result := mapFunc(items, func(x interface{}) interface{} { return x*2 })
    """
    return """
// mapFunc applies a function to each element of a slice
func mapFunc(slice []interface{}, fn func(interface{}) interface{}) []interface{} {
	result := make([]interface{}, len(slice))
	for i, item := range slice {
		result[i] = fn(item)
	}
	return result
}
""".strip()


def get_filter_helper() -> str:
    """
    Generate Go filter helper.

    Python:
        result = filter(lambda x: x > 0, items)

    Go equivalent:
        result := filterFunc(items, func(x interface{}) bool { return x > 0 })
    """
    return """
// filterFunc filters a slice by a predicate
func filterFunc(slice []interface{}, pred func(interface{}) bool) []interface{} {
	result := []interface{}{}
	for _, item := range slice {
		if pred(item) {
			result = append(result, item)
		}
	}
	return result
}
""".strip()


def get_reverse_helper() -> str:
    """Generate Go reverse helper."""
    return """
// reverse reverses a slice in place
func reverse(slice []interface{}) {
	for i, j := 0, len(slice)-1; i < j; i, j = i+1, j-1 {
		slice[i], slice[j] = slice[j], slice[i]
	}
}
""".strip()


def get_sum_helper() -> str:
    """Generate Go sum helper."""
    return """
// sum calculates the sum of numeric slice
func sum(slice []interface{}) float64 {
	total := 0.0
	for _, item := range slice {
		switch v := item.(type) {
		case int:
			total += float64(v)
		case float64:
			total += v
		case float32:
			total += float64(v)
		}
	}
	return total
}
""".strip()


def get_any_helper() -> str:
    """Generate Go any helper."""
    return """
// any checks if any element satisfies the predicate
func any(slice []interface{}, pred func(interface{}) bool) bool {
	for _, item := range slice {
		if pred(item) {
			return true
		}
	}
	return false
}
""".strip()


def get_all_helper() -> str:
    """Generate Go all helper."""
    return """
// all checks if all elements satisfy the predicate
func all(slice []interface{}, pred func(interface{}) bool) bool {
	for _, item := range slice {
		if !pred(item) {
			return false
		}
	}
	return true
}
""".strip()


# Map function names to their generators
def get_choice_helper() -> str:
    """
    Generate Go Choice helper for random.choice() (generic version).

    Python:
        item = random.choice(items)

    Go equivalent:
        item := Choice(items)
    """
    return """
// Choice returns a random element from a slice
func Choice(slice []interface{}) interface{} {
    if len(slice) == 0 {
        return nil
    }
    return slice[rand.Intn(len(slice))]
}
""".strip()

def get_choice_string_helper() -> str:
    """Generate ChoiceString helper for typed string arrays."""
    return """
// ChoiceString returns a random string from a slice
func ChoiceString(slice []string) string {
    if len(slice) == 0 {
        return ""
    }
    return slice[rand.Intn(len(slice))]
}
""".strip()

def get_choice_int_helper() -> str:
    """Generate ChoiceInt helper for typed int arrays."""
    return """
// ChoiceInt returns a random int from a slice
func ChoiceInt(slice []int) int {
    if len(slice) == 0 {
        return 0
    }
    return slice[rand.Intn(len(slice))]
}
""".strip()


HELPER_GENERATORS = {
    "contains": get_contains_helper,
    "set": get_set_helper,
    "tuple": get_tuple_helper,
    "zip": get_zip_helper,
    "map": get_map_helper,
    "filter": get_filter_helper,
    "reverse": get_reverse_helper,
    "sum": get_sum_helper,
    "any": get_any_helper,
    "all": get_all_helper,
    "choice": get_choice_helper,
    "choice_string": get_choice_string_helper,
    "choice_int": get_choice_int_helper,
}


def mark_helper_needed(helper_name: str):
    """Mark a helper function as needed for this generation."""
    needed_helpers.add(helper_name)


def generate_needed_helpers() -> str:
    """
    Generate all marked helper functions.

    Returns:
        Go code with all needed helper functions
    """
    if not needed_helpers:
        return ""

    helpers = []
    helpers.append("// ============================================================================")
    helpers.append("// Helper Functions (auto-generated)")
    helpers.append("// ============================================================================")
    helpers.append("")

    for helper_name in sorted(needed_helpers):
        if helper_name in HELPER_GENERATORS:
            helpers.append(HELPER_GENERATORS[helper_name]())
            helpers.append("")

    return "\n".join(helpers)


def reset_helpers():
    """Reset the needed helpers set (call between generations)."""
    global needed_helpers
    needed_helpers = set()


def detect_needed_helpers(code: str) -> Set[str]:
    """
    Analyze generated code to detect which helpers are needed.

    Args:
        code: Generated Go code

    Returns:
        Set of helper function names that should be included
    """
    needed = set()

    # Check for function calls
    if "contains(" in code:
        needed.add("contains")
    if "set(" in code or "Set{" in code:
        needed.add("set")
    if "tuple(" in code or "Tuple{" in code:
        needed.add("tuple")
    if "zip(" in code:
        needed.add("zip")
    if "mapFunc(" in code:
        needed.add("map")
    if "filterFunc(" in code:
        needed.add("filter")
    if "reverse(" in code:
        needed.add("reverse")
    if "sum(" in code:
        needed.add("sum")
    if "any(" in code:
        needed.add("any")
    if "all(" in code:
        needed.add("all")
    # Detect choice helpers individually (only generate what's used)
    if "Choice(" in code:
        needed.add("choice")
    if "ChoiceString(" in code:
        needed.add("choice_string")
    if "ChoiceInt(" in code:
        needed.add("choice_int")

    return needed
