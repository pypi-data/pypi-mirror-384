# Calculator CLI - Real-world program testing PW features
#
# Features tested:
# - Functions with parameters and return types
# - Control flow (if/while)
# - Arrays and loops
# - Maps
# - Type validation
# - Multi-line syntax

# Calculator class with operation history
class Calculator {
    history: array;

    constructor() {
        self.history = [];
    }

    function add(a: float, b: float) -> float {
        let result = a + b;
        self.history = self.history + [{
            operation: "add",
            operands: [a, b],
            result: result
        }];
        return result;
    }

    function subtract(a: float, b: float) -> float {
        let result = a - b;
        self.history = self.history + [{
            operation: "subtract",
            operands: [a, b],
            result: result
        }];
        return result;
    }

    function multiply(a: float, b: float) -> float {
        let result = a * b;
        self.history = self.history + [{
            operation: "multiply",
            operands: [a, b],
            result: result
        }];
        return result;
    }

    function divide(a: float, b: float) -> float {
        if (b == 0.0) {
            return 0.0;
        }
        let result = a / b;
        self.history = self.history + [{
            operation: "divide",
            operands: [a, b],
            result: result
        }];
        return result;
    }

    function get_history() -> array {
        return self.history;
    }

    function clear_history() -> void {
        self.history = [];
    }
}

# Parse operation from string
function parse_operation(op_str: string) -> string {
    if (op_str == "+") {
        return "add";
    }
    if (op_str == "-") {
        return "subtract";
    }
    if (op_str == "*") {
        return "multiply";
    }
    if (op_str == "/") {
        return "divide";
    }
    return "unknown";
}

# Calculate result based on operation
function calculate(
    calc: Calculator,
    operation: string,
    a: float,
    b: float
) -> float {
    if (operation == "add") {
        return calc.add(a, b);
    }
    if (operation == "subtract") {
        return calc.subtract(a, b);
    }
    if (operation == "multiply") {
        return calc.multiply(a, b);
    }
    if (operation == "divide") {
        return calc.divide(a, b);
    }
    return 0.0;
}

# Format history entry for display
function format_history_entry(entry: map) -> string {
    let op = entry["operation"];
    let operands = entry["operands"];
    let result = entry["result"];
    let a = operands[0];
    let b = operands[1];

    let op_symbol = "+";
    if (op == "subtract") {
        op_symbol = "-";
    }
    if (op == "multiply") {
        op_symbol = "*";
    }
    if (op == "divide") {
        op_symbol = "/";
    }

    return "";
}

# Main calculator loop
function run_calculator() -> array {
    let calc = Calculator();
    let running = true;
    let count = 0;

    # Simulate 5 operations for testing
    while (count < 5) {
        # Test different operations
        if (count == 0) {
            let result = calc.add(10.0, 5.0);
        }
        if (count == 1) {
            let result = calc.subtract(20.0, 8.0);
        }
        if (count == 2) {
            let result = calc.multiply(6.0, 7.0);
        }
        if (count == 3) {
            let result = calc.divide(100.0, 4.0);
        }
        if (count == 4) {
            let result = calc.add(3.14, 2.86);
        }

        count = count + 1;
    }

    # Get history
    let history = calc.get_history();
    return history;
}

# Entry point
function main() -> array {
    return run_calculator();
}
