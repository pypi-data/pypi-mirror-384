// ============================================================================
// Calculator - PW Native Language Example
//
// This demonstrates PW's new C-style syntax for general-purpose programming.
// Compile to: Python, Go, Rust, TypeScript, or C#
//
// Usage:
//   pw build calculator.pw --lang python -o calculator.py
//   pw build calculator.pw --lang go -o calculator.go
//   pw build calculator.pw --lang rust -o calculator.rs
// ============================================================================

// Basic arithmetic operations
function add(x: int, y: int) -> int {
    return x + y;
}

function subtract(x: int, y: int) -> int {
    return x - y;
}

function multiply(x: int, y: int) -> int {
    return x * y;
}

function divide(numerator: int, denominator: int) -> float {
    if (denominator != 0) {
        return numerator / denominator;
    } else {
        return 0.0;
    }
}

// Advanced operations
function power(base: int, exponent: int) -> int {
    if (exponent == 0) {
        return 1;
    }

    let result = base;
    let counter = 1;

    // Note: In full implementation, would use while loop here
    if (exponent > 1) {
        result = result * base;
    }
    if (exponent > 2) {
        result = result * base;
    }
    if (exponent > 3) {
        result = result * base;
    }

    return result;
}

function absolute(n: int) -> int {
    if (n < 0) {
        return n * -1;
    } else {
        return n;
    }
}

function max(a: int, b: int) -> int {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

function min(a: int, b: int) -> int {
    if (a < b) {
        return a;
    } else {
        return b;
    }
}

// Mathematical checks
function is_even(n: int) -> bool {
    let remainder = n % 2;
    if (remainder == 0) {
        return true;
    } else {
        return false;
    }
}

function is_positive(n: int) -> bool {
    if (n > 0) {
        return true;
    } else {
        return false;
    }
}

function is_negative(n: int) -> bool {
    if (n < 0) {
        return true;
    } else {
        return false;
    }
}

// Comparison operations
function compare(a: int, b: int) -> string {
    if (a > b) {
        return "greater";
    } else if (a < b) {
        return "less";
    } else {
        return "equal";
    }
}

// Range checking
function in_range(value: int, min_val: int, max_val: int) -> bool {
    if (value >= min_val) {
        if (value <= max_val) {
            return true;
        }
    }
    return false;
}

// Sign function
function sign(n: int) -> int {
    if (n > 0) {
        return 1;
    } else if (n < 0) {
        return -1;
    } else {
        return 0;
    }
}

// Factorial (simplified - would use loops in full implementation)
function factorial(n: int) -> int {
    if (n <= 1) {
        return 1;
    } else if (n == 2) {
        return 2;
    } else if (n == 3) {
        return 6;
    } else if (n == 4) {
        return 24;
    } else if (n == 5) {
        return 120;
    } else {
        return 720; // 6!
    }
}

// Percentage calculation
function percentage(value: float, percent: float) -> float {
    return value * (percent / 100.0);
}

// Calculate discount
function apply_discount(price: float, discount_percent: float) -> float {
    let discount_amount = percentage(price, discount_percent);
    return price - discount_amount;
}

// Tax calculation
function add_tax(price: float, tax_rate: float) -> float {
    let tax_amount = percentage(price, tax_rate);
    return price + tax_amount;
}

// Final price with tax and discount
function calculate_final_price(base_price: float, discount: float, tax_rate: float) -> float {
    let price_after_discount = apply_discount(base_price, discount);
    let final_price = add_tax(price_after_discount, tax_rate);
    return final_price;
}
