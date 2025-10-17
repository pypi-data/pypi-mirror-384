// Error Handling Example - PW Native Syntax
// Demonstrates try/catch with C-style brace syntax

function safe_divide(a: int, b: int) -> int {
    try {
        if (b == 0) {
            throw "Division by zero";
        }
        return a / b;
    } catch (error) {
        return 0;
    }
}

function validate_user_input(age: int, name: string) -> string {
    try {
        if (age < 0) {
            throw "Age cannot be negative";
        }
        if (age > 150) {
            throw "Age too high";
        }
        if (name == "") {
            throw "Name cannot be empty";
        }
        return "Valid user: " + name;
    } catch (e) {
        return "Error: " + e;
    }
}

function process_with_cleanup(value: int) -> string {
    try {
        if (value < 0) {
            throw "Negative value not allowed";
        }
        return "Processed: " + value;
    } catch (error) {
        return "Failed: " + error;
    } finally {
        // Cleanup code here
        // This runs regardless of success or failure
    }
}

function nested_error_handling(x: int, y: int) -> int {
    try {
        try {
            if (y == 0) {
                throw "Inner: Division by zero";
            }
            return x / y;
        } catch (inner_error) {
            throw "Outer: " + inner_error;
        }
    } catch (outer_error) {
        return -1;
    }
}
