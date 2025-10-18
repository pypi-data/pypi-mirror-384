// Simple Math Contract - demonstrates contract enforcement
// Avoids complex features, focuses on preconditions/postconditions

function add(a: int, b: int) -> int {
    @requires both_positive: a > 0 && b > 0
    return a + b;
}

function divide(a: int, b: int) -> int {
    @requires non_zero_divisor: b != 0
    @requires positive_dividend: a >= 0
    return a / b;
}

function increment(count: int) -> int {
    @requires positive: count >= 0
    return count + 1;
}

function main() -> int {
    print("=== Simple Math Contract Tests ===");
    print("");

    print("Test 1: add(5, 3) - should succeed");
    let result1 = add(5, 3);
    print("Result:", result1);
    print("");

    print("Test 2: divide(10, 2) - should succeed");
    let result2 = divide(10, 2);
    print("Result:", result2);
    print("");

    print("Test 3: increment(5) - should succeed");
    let result3 = increment(5);
    print("Result:", result3);
    print("");

    print("=== All tests passed ===");
    return 0;
}
