"""
Type Inference Engine

Infers types for untyped IR nodes by analyzing usage patterns, literals,
and context. This improves generated code quality by reducing generic
types (interface{}, any, etc.) in favor of specific types.

Strategy:
1. Literal analysis - Infer from literal values
2. Assignment tracking - Track variable types across assignments
3. Function signature analysis - Infer from function calls and returns
4. Constraint propagation - Propagate type information through expressions
"""

from typing import Dict, Optional, Set
from dsl.ir import (
    IRModule,
    IRFunction,
    IRParameter,
    IRStatement,
    IRExpression,
    IRAssignment,
    IRReturn,
    IRIf,
    IRFor,
    IRWhile,
    IRCall,
    IRLiteral,
    IRIdentifier,
    IRBinaryOp,
    IRArray,
    IRMap,
    IRType,
    LiteralType,
    BinaryOperator,
)


class TypeInferenceEngine:
    """Infer types for IR nodes."""

    def __init__(self):
        # Track inferred types: variable_name -> IRType
        self.type_env: Dict[str, IRType] = {}
        # Track function return types: function_name -> IRType
        self.function_types: Dict[str, IRType] = {}
        # Track array element types from append operations: array_name -> Set[IRType]
        self.array_element_types: Dict[str, Set[str]] = {}

    def infer_module_types(self, module: IRModule):
        """
        Run type inference on entire module.

        Modifies IR nodes in-place to add type annotations.
        """
        # Phase 0: Infer module-level variable types
        for var_assignment in module.module_vars:
            target_name = None
            if isinstance(var_assignment.target, str):
                target_name = var_assignment.target
            elif isinstance(var_assignment.target, IRIdentifier):
                target_name = var_assignment.target.name

            if target_name:
                var_type = self._infer_expression_type(var_assignment.value)
                if var_type:
                    self.type_env[target_name] = var_type

        # Phase 1: Collect function signatures
        for func in module.functions:
            if func.return_type:
                self.function_types[func.name] = func.return_type

        # Phase 2: Infer types within each function
        for func in module.functions:
            self._infer_function_types(func)

    def _infer_function_types(self, func: IRFunction):
        """Infer types within a function."""
        # Add parameters to type environment
        for param in func.params:
            if param.param_type and param.param_type.name != "any":
                # Use explicit type if available and not 'any'
                self.type_env[param.name] = param.param_type
            elif param.default_value:
                # Infer from default value if type is 'any' or missing
                inferred_type = self._infer_expression_type(param.default_value)
                if inferred_type:
                    self.type_env[param.name] = inferred_type
                    # Update the param type in the IR
                    param.param_type = inferred_type

        # Pass 1: Do initial type inference (for variables, literals, etc.)
        for stmt in func.body:
            self._infer_statement_types(stmt)

        # Pass 2: Collect array element types from append operations
        # (now that variables have types)
        for stmt in func.body:
            self._collect_array_element_types(stmt)

        # Pass 3: Re-infer array types with element type information
        for stmt in func.body:
            self._update_array_types(stmt)

    def _update_array_types(self, stmt: IRStatement):
        """Update array types based on collected element types."""
        if isinstance(stmt, IRAssignment):
            # Check if this is an empty array assignment
            if isinstance(stmt.value, IRArray) and not stmt.value.elements:
                target_name = None
                if isinstance(stmt.target, str):
                    target_name = stmt.target
                elif isinstance(stmt.target, IRIdentifier):
                    target_name = stmt.target.name

                if target_name and target_name in self.array_element_types:
                    element_types = self.array_element_types[target_name]
                    if len(element_types) == 1:
                        # All appends use same type - update it
                        elem_type_name = list(element_types)[0]
                        new_type = IRType(
                            name="array",
                            generic_args=[IRType(name=elem_type_name)]
                        )
                        self.type_env[target_name] = new_type

        elif isinstance(stmt, IRIf):
            for s in stmt.then_body:
                self._update_array_types(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._update_array_types(s)
        elif isinstance(stmt, IRFor):
            for s in stmt.body:
                self._update_array_types(s)
        elif isinstance(stmt, IRWhile):
            for s in stmt.body:
                self._update_array_types(s)

    def _collect_array_element_types(self, stmt: IRStatement):
        """
        Collect array element types from append operations.

        Looks for patterns like:
        - array.append(value) - standalone call
        - array = append(array, value) - Go-style assignment
        """
        from dsl.ir import IRPropertyAccess

        # Check for standalone append call (Python style: output.append(x))
        if isinstance(stmt, IRCall):
            self._analyze_append_call(stmt)
        # Check for append in assignment (Go style: output = append(output, x))
        elif isinstance(stmt, IRAssignment):
            if isinstance(stmt.value, IRCall):
                self._analyze_append_call(stmt.value, target_array=stmt.target)
        elif isinstance(stmt, IRIf):
            # Recurse into if branches
            for s in stmt.then_body:
                self._collect_array_element_types(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._collect_array_element_types(s)
        elif isinstance(stmt, IRFor):
            # Recurse into for body
            for s in stmt.body:
                self._collect_array_element_types(s)
        elif isinstance(stmt, IRWhile):
            # Recurse into while body
            for s in stmt.body:
                self._collect_array_element_types(s)

    def _analyze_append_call(self, call: IRCall, target_array=None):
        """Analyze an append call to infer element type."""
        from dsl.ir import IRPropertyAccess

        # Pattern 1: array.append(value) - Python style
        if isinstance(call.function, IRPropertyAccess):
            if call.function.property == "append" and call.args:
                array_name = None
                if isinstance(call.function.object, IRIdentifier):
                    array_name = call.function.object.name

                if array_name:
                    # Infer type of appended value
                    value_type = self._infer_expression_type(call.args[0])
                    if value_type:
                        if array_name not in self.array_element_types:
                            self.array_element_types[array_name] = set()
                        self.array_element_types[array_name].add(value_type.name)

        # Pattern 2: array = append(array, value) - Go style
        elif isinstance(call.function, IRIdentifier):
            if call.function.name == "append" and len(call.args) >= 2:
                # First arg is the array
                if isinstance(call.args[0], IRIdentifier):
                    array_name = call.args[0].name
                    # Second arg is the value
                    value_type = self._infer_expression_type(call.args[1])
                    if value_type:
                        if array_name not in self.array_element_types:
                            self.array_element_types[array_name] = set()
                        self.array_element_types[array_name].add(value_type.name)

    def _infer_statement_types(self, stmt: IRStatement):
        """Infer types from a statement."""
        if isinstance(stmt, IRAssignment):
            # Get the target variable name
            target_name = None
            if isinstance(stmt.target, str):
                target_name = stmt.target
            elif isinstance(stmt.target, IRIdentifier):
                target_name = stmt.target.name

            # Infer type from value expression
            value_type = self._infer_expression_type(stmt.value)

            if value_type:
                # Store inferred type
                if target_name:
                    self.type_env[target_name] = value_type

        elif isinstance(stmt, IRReturn):
            # Infer return type
            if stmt.value:
                return_type = self._infer_expression_type(stmt.value)
                # Could update function return type here

        elif isinstance(stmt, IRIf):
            # Recurse into branches
            for s in stmt.then_body:
                self._infer_statement_types(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._infer_statement_types(s)

        elif isinstance(stmt, IRFor):
            # Infer iterator type from iterable
            iterable_type = self._infer_expression_type(stmt.iterable)
            # For array, iterator is element type
            # TODO: Extract element type from array type
            for s in stmt.body:
                self._infer_statement_types(s)

        elif isinstance(stmt, IRWhile):
            for s in stmt.body:
                self._infer_statement_types(s)

    def _infer_expression_type(self, expr: IRExpression) -> Optional[IRType]:
        """Infer type from an expression."""
        # Import here to avoid circular dependency
        from dsl.ir import IRIndex

        if isinstance(expr, IRLiteral):
            # Literal types are known
            return self._literal_to_type(expr)

        elif isinstance(expr, IRIdentifier):
            # Look up in type environment
            return self.type_env.get(expr.name)

        elif isinstance(expr, IRArray):
            # Array type - infer element type from first element
            if expr.elements:
                elem_type = self._infer_expression_type(expr.elements[0])
                if elem_type:
                    return IRType(
                        name="array",
                        generic_args=[elem_type]
                    )
            return IRType(name="array", generic_args=[IRType(name="any")])

        elif isinstance(expr, IRMap):
            # Map type - infer from first entry
            if expr.entries:
                first_key = list(expr.entries.keys())[0]
                first_val = expr.entries[first_key]
                val_type = self._infer_expression_type(first_val)
                # Assuming string keys for now
                if val_type:
                    return IRType(
                        name="map",
                        generic_args=[IRType(name="string"), val_type]
                    )
            return IRType(name="map", generic_args=[IRType(name="string"), IRType(name="any")])

        elif isinstance(expr, IRIndex):
            # Array/map indexing - infer from container type
            container_type = self._infer_expression_type(expr.object)
            if container_type:
                # If container is array, return element type
                if container_type.name == "array" and container_type.generic_args:
                    return container_type.generic_args[0]
                # If container is map, return value type
                elif container_type.name == "map" and len(container_type.generic_args) >= 2:
                    return container_type.generic_args[1]
            return None

        elif isinstance(expr, IRBinaryOp):
            # Infer from operands and operator
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)

            # Arithmetic operators -> numeric type
            if expr.op in [BinaryOperator.ADD, BinaryOperator.SUBTRACT,
                          BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE,
                          BinaryOperator.POWER]:
                # Power operator always returns float
                if expr.op == BinaryOperator.POWER:
                    return IRType(name="float")
                # If either is float, result is float
                if (left_type and left_type.name == "float") or \
                   (right_type and right_type.name == "float"):
                    return IRType(name="float")
                return IRType(name="int")

            # Comparison operators -> bool
            elif expr.op in [BinaryOperator.EQUAL, BinaryOperator.NOT_EQUAL,
                            BinaryOperator.LESS_THAN, BinaryOperator.GREATER_THAN,
                            BinaryOperator.LESS_EQUAL, BinaryOperator.GREATER_EQUAL]:
                return IRType(name="bool")

            # Logical operators -> bool
            elif expr.op in [BinaryOperator.AND, BinaryOperator.OR]:
                return IRType(name="bool")

        elif isinstance(expr, IRCall):
            # Import here to avoid circular dependency
            from dsl.ir import IRPropertyAccess

            # Look up function return type
            if isinstance(expr.function, IRIdentifier):
                func_name = expr.function.name
                if func_name in self.function_types:
                    return self.function_types[func_name]

                # Built-in function types
                builtin_types = {
                    "len": IRType(name="int"),
                    "str": IRType(name="string"),
                    "int": IRType(name="int"),
                    "float": IRType(name="float"),
                    "bool": IRType(name="bool"),
                    # Helper functions (auto-generated by generators)
                    "Choice": IRType(name="any"),  # Generic
                    "ChoiceString": IRType(name="string"),
                    "ChoiceInt": IRType(name="int"),
                    "ChoiceFloat": IRType(name="float"),
                }
                if func_name in builtin_types:
                    return builtin_types[func_name]

            # Handle module.function calls (e.g., math.sqrt, random.random)
            elif isinstance(expr.function, IRPropertyAccess):
                if isinstance(expr.function.object, IRIdentifier):
                    module_name = expr.function.object.name
                    func_name = expr.function.property
                    full_name = f"{module_name}.{func_name}"

                    # Standard library function return types
                    stdlib_types = {
                        # Math functions
                        "math.sqrt": IRType(name="float"),
                        "math.pow": IRType(name="float"),
                        "math.abs": IRType(name="float"),
                        "math.floor": IRType(name="int"),
                        "math.ceil": IRType(name="int"),
                        "math.round": IRType(name="int"),
                        "math.sin": IRType(name="float"),
                        "math.cos": IRType(name="float"),
                        "math.tan": IRType(name="float"),
                        "math.asin": IRType(name="float"),
                        "math.acos": IRType(name="float"),
                        "math.atan": IRType(name="float"),
                        "math.atan2": IRType(name="float"),
                        "math.log": IRType(name="float"),
                        "math.log10": IRType(name="float"),
                        "math.exp": IRType(name="float"),

                        # Random functions
                        "random.random": IRType(name="float"),
                        "random.randint": IRType(name="int"),
                        "random.choice": IRType(name="any"),  # Depends on input
                        "random.shuffle": IRType(name="none"),

                        # String methods
                        "str.upper": IRType(name="string"),
                        "str.lower": IRType(name="string"),
                        "str.strip": IRType(name="string"),
                        "str.split": IRType(name="array", generic_args=[IRType(name="string")]),
                        "str.join": IRType(name="string"),
                        "str.replace": IRType(name="string"),

                        # List methods (most return None in Python)
                        "list.append": IRType(name="none"),
                        "list.extend": IRType(name="none"),
                        "list.pop": IRType(name="any"),
                        "list.reverse": IRType(name="none"),
                        "list.sort": IRType(name="none"),
                    }

                    if full_name in stdlib_types:
                        result_type = stdlib_types[full_name]

                        # Special case: random.choice - infer from argument type
                        if full_name == "random.choice" and expr.args:
                            arg_type = self._infer_expression_type(expr.args[0])
                            if arg_type and arg_type.name == "array" and arg_type.generic_args:
                                # Return the element type of the array
                                return arg_type.generic_args[0]

                        return result_type

        # Default: unknown type
        return None

    def _literal_to_type(self, lit: IRLiteral) -> IRType:
        """Convert literal to type."""
        type_map = {
            LiteralType.STRING: "string",
            LiteralType.INTEGER: "int",
            LiteralType.FLOAT: "float",
            LiteralType.BOOLEAN: "bool",
            LiteralType.NULL: "null",
        }
        type_name = type_map.get(lit.literal_type, "any")
        return IRType(name=type_name)


def infer_types(module: IRModule):
    """
    Run type inference on a module.

    This is a convenience function that creates an engine and runs inference.
    """
    engine = TypeInferenceEngine()
    engine.infer_module_types(module)
    return engine.type_env
