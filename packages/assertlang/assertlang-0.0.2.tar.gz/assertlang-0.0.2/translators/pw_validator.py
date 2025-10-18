#!/usr/bin/env python3
"""
PW MCP Validator - Real-time validation for 99%+ accuracy

Validates PW MCP trees with detailed error messages and auto-fix suggestions.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from difflib import get_close_matches


@dataclass
class ValidationResult:
    """Result of PW validation."""
    valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]

    def __str__(self):
        if self.valid:
            msg = "✅ Valid PW MCP tree"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
            return msg
        else:
            return f"❌ Invalid PW MCP tree ({len(self.errors)} errors)"


class PWValidator:
    """Real-time PW MCP tree validator with detailed feedback."""

    VALID_TOOLS = {
        "pw_module", "pw_function", "pw_parameter", "pw_type",
        "pw_assignment", "pw_if", "pw_for", "pw_while",
        "pw_return", "pw_call", "pw_binary_op",
        "pw_identifier", "pw_literal", "pw_import",
        "pw_class", "pw_method", "pw_property",
        "pw_try_except", "pw_except_handler",
        "pw_dict_literal", "pw_list_literal",
        "pw_attribute_access", "pw_index_access",
        "pw_module_var", "pw_f_string"
    }

    REQUIRED_PARAMS = {
        "pw_module": ["name"],
        "pw_function": ["name", "params", "body"],
        "pw_parameter": ["name"],
        "pw_type": ["name"],
        "pw_assignment": ["target", "value"],
        "pw_if": ["condition", "then_body"],
        "pw_for": ["iterator", "iterable", "body"],
        "pw_while": ["condition", "body"],
        "pw_return": ["value"],
        "pw_call": ["function", "args"],
        "pw_binary_op": ["op", "left", "right"],
        "pw_identifier": ["name"],
        "pw_literal": ["value", "literal_type"],
        "pw_import": ["module"],
    }

    PARAM_TYPES = {
        "pw_function.name": str,
        "pw_function.params": list,
        "pw_function.body": list,
        "pw_parameter.name": str,
        "pw_parameter.param_type": dict,
        "pw_assignment.target": str,
        "pw_assignment.value": dict,
        "pw_if.condition": dict,
        "pw_if.then_body": list,
        "pw_if.else_body": list,
        "pw_for.iterator": str,
        "pw_for.iterable": dict,
        "pw_for.body": list,
        "pw_return.value": dict,
        "pw_binary_op.op": str,
        "pw_binary_op.left": dict,
        "pw_binary_op.right": dict,
        "pw_identifier.name": str,
        "pw_literal.value": (str, int, float, bool),
        "pw_literal.literal_type": str,
        "pw_call.function": str,
        "pw_call.args": list,
    }

    VALID_OPERATORS = {
        "+", "-", "*", "/", "//", "%", "**",
        "==", "!=", "<", ">", "<=", ">=",
        "and", "or", "not",
        "&", "|", "^", "<<", ">>"
    }

    LITERAL_TYPES = {
        "integer", "float", "string", "boolean", "null", "any"
    }

    def validate(self, pw_tree: Dict) -> ValidationResult:
        """Validate a PW MCP tree and return detailed feedback."""
        errors = []
        warnings = []

        if not isinstance(pw_tree, dict):
            errors.append({
                "type": "invalid_structure",
                "message": f"PW tree must be a dict, got {type(pw_tree).__name__}",
                "fix": "Ensure pw_tree is a dictionary with 'tool' and 'params' keys"
            })
            return ValidationResult(False, errors, warnings)

        # Rule 1: Must have 'tool' field
        if "tool" not in pw_tree:
            errors.append({
                "type": "missing_tool",
                "message": "PW tree must have 'tool' field",
                "fix": "Add: {\"tool\": \"pw_...\", \"params\": {...}}",
                "example": "{\"tool\": \"pw_function\", \"params\": {\"name\": \"my_func\", ...}}"
            })
            return ValidationResult(False, errors, warnings)

        tool_name = pw_tree["tool"]

        # Rule 2: Tool must be valid
        if tool_name not in self.VALID_TOOLS:
            suggestion = self._suggest_tool(tool_name)
            errors.append({
                "type": "invalid_tool",
                "message": f"Unknown tool: '{tool_name}'",
                "fix": f"Use one of: {', '.join(sorted(self.VALID_TOOLS)[:5])}...",
                "suggestion": suggestion
            })
            return ValidationResult(False, errors, warnings)

        # Rule 3: Must have 'params' field
        if "params" not in pw_tree:
            errors.append({
                "type": "missing_params",
                "message": f"'{tool_name}' requires 'params' field",
                "fix": "Add: \"params\": {...}",
                "example": self._get_params_example(tool_name)
            })
            return ValidationResult(False, errors, warnings)

        params = pw_tree["params"]

        if not isinstance(params, dict):
            errors.append({
                "type": "invalid_params_type",
                "message": f"'params' must be a dict, got {type(params).__name__}",
                "fix": "Ensure params is a dictionary"
            })
            return ValidationResult(False, errors, warnings)

        # Rule 4: Check required parameters
        required = self.REQUIRED_PARAMS.get(tool_name, [])
        for field in required:
            if field not in params:
                errors.append({
                    "type": "missing_required_param",
                    "message": f"'{tool_name}' requires '{field}' parameter",
                    "fix": f"Add: \"{field}\": ...",
                    "example": self._get_field_example(tool_name, field)
                })

        # Rule 5: Type checking for parameters
        for field, value in params.items():
            expected_type = self.PARAM_TYPES.get(f"{tool_name}.{field}")
            if expected_type:
                if isinstance(expected_type, tuple):
                    # Multiple allowed types
                    if not isinstance(value, expected_type):
                        errors.append({
                            "type": "param_type_mismatch",
                            "message": f"'{tool_name}.{field}' expects {expected_type}, got {type(value).__name__}",
                            "fix": self._suggest_type_fix(expected_type, value)
                        })
                else:
                    # Single expected type
                    if not isinstance(value, expected_type):
                        errors.append({
                            "type": "param_type_mismatch",
                            "message": f"'{tool_name}.{field}' expects {expected_type.__name__}, got {type(value).__name__}",
                            "fix": self._suggest_type_fix(expected_type, value)
                        })

        # Rule 6: Tool-specific validation
        tool_errors, tool_warnings = self._validate_tool_specific(tool_name, params)
        errors.extend(tool_errors)
        warnings.extend(tool_warnings)

        # Rule 7: Recursive validation
        for field, value in params.items():
            if isinstance(value, dict) and "tool" in value:
                nested_result = self.validate(value)
                errors.extend([{**e, "path": f"{tool_name}.{field}.{e.get('path', '')}"} for e in nested_result.errors])
                warnings.extend(nested_result.warnings)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict) and "tool" in item:
                        nested_result = self.validate(item)
                        errors.extend([{**e, "path": f"{tool_name}.{field}[{i}].{e.get('path', '')}"} for e in nested_result.errors])
                        warnings.extend(nested_result.warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_tool_specific(self, tool_name: str, params: Dict) -> Tuple[List, List]:
        """Tool-specific validation rules."""
        errors = []
        warnings = []

        if tool_name == "pw_binary_op":
            op = params.get("op")
            if op and op not in self.VALID_OPERATORS:
                errors.append({
                    "type": "invalid_operator",
                    "message": f"Unknown operator: '{op}'",
                    "fix": f"Use one of: {', '.join(sorted(self.VALID_OPERATORS))}",
                    "suggestion": self._suggest_operator(op)
                })

        elif tool_name == "pw_literal":
            literal_type = params.get("literal_type")
            if literal_type and literal_type not in self.LITERAL_TYPES:
                errors.append({
                    "type": "invalid_literal_type",
                    "message": f"Unknown literal type: '{literal_type}'",
                    "fix": f"Use one of: {', '.join(self.LITERAL_TYPES)}",
                    "suggestion": self._suggest_literal_type(literal_type)
                })

        elif tool_name == "pw_function":
            body = params.get("body", [])
            if not body:
                warnings.append({
                    "type": "empty_function_body",
                    "message": "Function has empty body",
                    "suggestion": "Add at least one statement (pw_return, pw_assignment, etc.)"
                })

            # Check for return statement
            has_return = any(
                isinstance(stmt, dict) and stmt.get("tool") == "pw_return"
                for stmt in body
            )
            if not has_return and params.get("return_type"):
                warnings.append({
                    "type": "missing_return",
                    "message": "Function declares return type but has no return statement",
                    "suggestion": "Add pw_return(...) to body"
                })

        elif tool_name == "pw_identifier":
            name = params.get("name", "")
            if name and not self._is_valid_identifier(name):
                errors.append({
                    "type": "invalid_identifier",
                    "message": f"'{name}' is not a valid identifier",
                    "fix": "Use only letters, numbers, and underscores; must start with letter or underscore"
                })

        elif tool_name == "pw_assignment":
            target = params.get("target")
            if target and not isinstance(target, str):
                errors.append({
                    "type": "invalid_assignment_target",
                    "message": f"Assignment target must be string, got {type(target).__name__}",
                    "fix": f"Change to: \"{target}\""
                })

        return errors, warnings

    def _suggest_tool(self, wrong_tool: str) -> str:
        """Suggest correct tool using fuzzy matching."""
        matches = get_close_matches(wrong_tool, self.VALID_TOOLS, n=3, cutoff=0.6)
        if matches:
            return f"Did you mean: {', '.join(matches)}?"
        return ""

    def _suggest_operator(self, wrong_op: str) -> str:
        """Suggest correct operator."""
        op_map = {
            "add": "+", "plus": "+", "sum": "+",
            "sub": "-", "subtract": "-", "minus": "-",
            "mul": "*", "multiply": "*", "times": "*",
            "div": "/", "divide": "/",
            "eq": "==", "equal": "==", "equals": "==",
            "ne": "!=", "notequal": "!=",
            "lt": "<", "lessthan": "<",
            "gt": ">", "greaterthan": ">",
            "and": "and", "AND": "and",
            "or": "or", "OR": "or",
        }
        if wrong_op in op_map:
            return f"Did you mean: '{op_map[wrong_op]}'?"
        return ""

    def _suggest_literal_type(self, wrong_type: str) -> str:
        """Suggest correct literal type."""
        matches = get_close_matches(wrong_type, self.LITERAL_TYPES, n=2, cutoff=0.6)
        if matches:
            return f"Did you mean: {', '.join(matches)}?"
        type_map = {
            "int": "integer", "number": "integer",
            "str": "string", "text": "string",
            "bool": "boolean", "true": "boolean", "false": "boolean",
            "none": "null", "nil": "null",
        }
        if wrong_type.lower() in type_map:
            return f"Use: '{type_map[wrong_type.lower()]}'"
        return ""

    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is a valid identifier."""
        if not name:
            return False
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        return all(c.isalnum() or c == '_' for c in name)

    def _get_params_example(self, tool_name: str) -> str:
        """Get example params for a tool."""
        examples = {
            "pw_function": "{\"name\": \"my_func\", \"params\": [...], \"body\": [...]}",
            "pw_parameter": "{\"name\": \"x\", \"param_type\": pw_type('int')}",
            "pw_assignment": "{\"target\": \"result\", \"value\": pw_literal(0, 'integer')}",
            "pw_if": "{\"condition\": pw_binary_op('>', ...), \"then_body\": [...]}",
            "pw_return": "{\"value\": pw_identifier('x')}",
            "pw_binary_op": "{\"op\": \"+\", \"left\": pw_identifier('x'), \"right\": pw_literal(1, 'integer')}",
        }
        return examples.get(tool_name, "{}")

    def _get_field_example(self, tool_name: str, field: str) -> str:
        """Get example for a specific field."""
        examples = {
            "pw_function.name": "\"calculate_total\"",
            "pw_function.params": "[pw_parameter('x', pw_type('int'))]",
            "pw_function.body": "[pw_return(pw_identifier('x'))]",
            "pw_parameter.name": "\"x\"",
            "pw_assignment.target": "\"result\"",
            "pw_assignment.value": "pw_literal(0, 'integer')",
            "pw_if.condition": "pw_binary_op('>', pw_identifier('x'), pw_literal(0, 'integer'))",
            "pw_if.then_body": "[pw_return(pw_literal(True, 'boolean'))]",
            "pw_for.iterator": "\"item\"",
            "pw_for.iterable": "pw_identifier('items')",
            "pw_for.body": "[pw_call('print', [pw_identifier('item')])]",
        }
        return examples.get(f"{tool_name}.{field}", "...")

    def _suggest_type_fix(self, expected_type, actual_value) -> str:
        """Suggest how to fix type mismatch."""
        if expected_type == str:
            return f"Wrap in quotes: \"{actual_value}\""
        elif expected_type == dict:
            return "This should be a PW tree (dict with 'tool' and 'params')"
        elif expected_type == list:
            return f"Wrap in list: [{actual_value}]"
        return f"Convert to {expected_type.__name__}"


# Convenience function
def validate_pw(pw_tree: Dict) -> ValidationResult:
    """Validate a PW MCP tree."""
    validator = PWValidator()
    return validator.validate(pw_tree)


if __name__ == "__main__":
    # Test validation
    print("PW Validator Test\n" + "="*60)

    # Test 1: Valid PW
    from pw_composer import pw_function, pw_parameter, pw_type, pw_return, pw_binary_op, pw_identifier

    valid_func = pw_function(
        name="add",
        params=[
            pw_parameter("x", pw_type("int")),
            pw_parameter("y", pw_type("int"))
        ],
        return_type=pw_type("int"),
        body=[
            pw_return(
                pw_binary_op("+", pw_identifier("x"), pw_identifier("y"))
            )
        ]
    )

    result = validate_pw(valid_func)
    print(f"\nTest 1 (Valid): {result}")

    # Test 2: Missing params
    invalid_func = {
        "tool": "pw_function",
        "params": {
            "name": "broken"
            # Missing params and body!
        }
    }

    result = validate_pw(invalid_func)
    print(f"\nTest 2 (Invalid): {result}")
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ❌ {error['message']}")
            print(f"     Fix: {error['fix']}")

    # Test 3: Wrong operator
    invalid_op = {
        "tool": "pw_binary_op",
        "params": {
            "op": "add",  # Should be "+"
            "left": pw_identifier("x"),
            "right": pw_identifier("y")
        }
    }

    result = validate_pw(invalid_op)
    print(f"\nTest 3 (Invalid operator): {result}")
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ❌ {error['message']}")
            if 'suggestion' in error:
                print(f"     {error['suggestion']}")
