"""
Promptware Context Analyzer

This module provides context-aware analysis for the universal code translation system.
It tracks cross-function dependencies, data flow, and variable usage patterns to enable
more accurate type inference and code generation.

Key Capabilities:
1. Call Graph Construction - Track which functions call which
2. Data Flow Analysis - Track how values flow between functions
3. Variable Scope Tracking - Track variable lifetime and visibility
4. Cross-Function Type Inference - Infer types based on usage across functions
5. Return Type Analysis - Infer return types from how values are used

Design Principles:
- Conservative analysis (safe over aggressive)
- Confidence scoring for inferred information
- Handle cycles and recursion gracefully
- Support inter-procedural analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from dsl.ir import (
    IRAssignment,
    IRBinaryOp,
    IRCall,
    IRClass,
    IRExpression,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRModule,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRType,
)
from dsl.type_system import TypeInfo


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class CallSite:
    """Represents a function call location."""

    caller_function: str  # Name of function making the call
    callee_function: str  # Name of function being called
    arguments: List[IRExpression]  # Arguments passed
    line_number: int = 0  # Source location
    confidence: float = 1.0  # Confidence this is correct


@dataclass
class VariableUsage:
    """Tracks how a variable is used."""

    variable_name: str
    function_name: str
    assignment_count: int = 0  # Number of times assigned
    read_count: int = 0  # Number of times read
    property_accesses: List[str] = field(default_factory=list)  # e.g., ["name", "email"]
    method_calls: List[str] = field(default_factory=list)  # e.g., ["get", "set"]
    operators_used: Set[str] = field(default_factory=set)  # Operators applied to variable


@dataclass
class FunctionContext:
    """Rich context about a function."""

    name: str
    parameters: List[str]  # Parameter names
    local_variables: Set[str] = field(default_factory=set)
    calls_made: List[CallSite] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    return_expressions: List[IRExpression] = field(default_factory=list)
    variable_usage: Dict[str, VariableUsage] = field(default_factory=dict)


@dataclass
class CallGraph:
    """Represents the call graph of a module."""

    nodes: Dict[str, FunctionContext] = field(default_factory=dict)  # function_name -> context
    edges: Dict[str, List[str]] = field(default_factory=dict)  # caller -> [callees]


@dataclass
class DataFlow:
    """Tracks data flow between variables and functions."""

    from_variable: str
    to_variable: str
    from_function: str
    to_function: str
    flow_type: str  # "parameter", "return", "assignment"
    confidence: float = 1.0


# ============================================================================
# Context Analyzer Core
# ============================================================================


class ContextAnalyzer:
    """
    Analyzes code context to enable cross-function type inference.

    This analyzer builds a call graph, tracks data flow, and identifies
    usage patterns that help infer types more accurately.
    """

    def __init__(self):
        self.call_graph = CallGraph()
        self.data_flows: List[DataFlow] = []
        self.global_variables: Dict[str, TypeInfo] = {}

    # ========================================================================
    # Main Analysis Entry Point
    # ========================================================================

    def analyze_module(self, module: IRModule) -> None:
        """
        Perform complete context analysis on a module.

        Args:
            module: IR module to analyze

        This builds the call graph and tracks all data flows.
        """
        # Clear previous analysis
        self.call_graph = CallGraph()
        self.data_flows = []

        # Build function contexts
        for func in module.functions:
            self._build_function_context(func)

        # Build class method contexts
        for cls in module.classes:
            for method in cls.methods:
                self._build_function_context(method, class_name=cls.name)

        # Build call graph edges
        self._build_call_edges()

        # Analyze data flows
        self._analyze_data_flows()

    # ========================================================================
    # Function Context Building
    # ========================================================================

    def _build_function_context(self, func: IRFunction, class_name: Optional[str] = None) -> None:
        """
        Build rich context for a single function.

        Args:
            func: Function to analyze
            class_name: Name of containing class (if method)
        """
        func_name = func.name
        if class_name:
            func_name = f"{class_name}.{func.name}"

        context = FunctionContext(
            name=func_name,
            parameters=[p.name for p in func.params],
        )

        # Analyze function body
        for stmt in func.body:
            self._analyze_statement(stmt, context)

        self.call_graph.nodes[func_name] = context

    def _analyze_statement(self, stmt: IRStatement, context: FunctionContext) -> None:
        """
        Analyze a statement and update context.

        Args:
            stmt: Statement to analyze
            context: Function context to update
        """
        # Assignment
        if isinstance(stmt, IRAssignment):
            target = stmt.target
            context.local_variables.add(target)

            # Track variable usage
            if target not in context.variable_usage:
                context.variable_usage[target] = VariableUsage(
                    variable_name=target,
                    function_name=context.name
                )
            context.variable_usage[target].assignment_count += 1

            # Analyze right-hand side
            self._analyze_expression(stmt.value, context)

        # Return statement
        elif isinstance(stmt, IRReturn):
            if stmt.value:
                context.return_expressions.append(stmt.value)
                self._analyze_expression(stmt.value, context)

        # If statement
        elif isinstance(stmt, IRIf):
            self._analyze_expression(stmt.condition, context)
            for s in stmt.then_body:
                self._analyze_statement(s, context)
            for s in stmt.else_body:
                self._analyze_statement(s, context)

        # Other statement types (for, while, try, etc.)
        # Handle recursively based on type
        # (simplified for this implementation)

    def _analyze_expression(self, expr: IRExpression, context: FunctionContext) -> None:
        """
        Analyze an expression and update context.

        Args:
            expr: Expression to analyze
            context: Function context to update
        """
        # Identifier (variable reference)
        if isinstance(expr, IRIdentifier):
            var_name = expr.name
            if var_name not in context.variable_usage:
                context.variable_usage[var_name] = VariableUsage(
                    variable_name=var_name,
                    function_name=context.name
                )
            context.variable_usage[var_name].read_count += 1

        # Function call
        elif isinstance(expr, IRCall):
            callee = expr.function
            if isinstance(callee, IRIdentifier):
                call_site = CallSite(
                    caller_function=context.name,
                    callee_function=callee.name,
                    arguments=expr.args
                )
                context.calls_made.append(call_site)

            # Analyze arguments
            for arg in expr.args:
                self._analyze_expression(arg, context)

        # Property access (e.g., user.name)
        elif isinstance(expr, IRPropertyAccess):
            obj = expr.object
            if isinstance(obj, IRIdentifier):
                var_name = obj.name
                if var_name not in context.variable_usage:
                    context.variable_usage[var_name] = VariableUsage(
                        variable_name=var_name,
                        function_name=context.name
                    )
                context.variable_usage[var_name].property_accesses.append(expr.property)
                context.variable_usage[var_name].read_count += 1

        # Binary operation
        elif isinstance(expr, IRBinaryOp):
            self._analyze_expression(expr.left, context)
            self._analyze_expression(expr.right, context)

            # Track operator usage on left operand
            if isinstance(expr.left, IRIdentifier):
                var_name = expr.left.name
                if var_name in context.variable_usage:
                    context.variable_usage[var_name].operators_used.add(expr.op.value)

        # Other expression types handled recursively
        # (simplified for this implementation)

    # ========================================================================
    # Call Graph Construction
    # ========================================================================

    def _build_call_edges(self) -> None:
        """Build call graph edges from call sites."""
        for func_name, context in self.call_graph.nodes.items():
            callees = []
            for call_site in context.calls_made:
                callee = call_site.callee_function
                callees.append(callee)

                # Update reverse edge (called_by)
                if callee in self.call_graph.nodes:
                    self.call_graph.nodes[callee].called_by.append(func_name)

            self.call_graph.edges[func_name] = callees

    def get_callers(self, function_name: str) -> List[str]:
        """
        Get all functions that call the given function.

        Args:
            function_name: Name of function

        Returns:
            List of caller function names
        """
        if function_name not in self.call_graph.nodes:
            return []
        return self.call_graph.nodes[function_name].called_by

    def get_callees(self, function_name: str) -> List[str]:
        """
        Get all functions called by the given function.

        Args:
            function_name: Name of function

        Returns:
            List of callee function names
        """
        return self.call_graph.edges.get(function_name, [])

    def find_call_chain(self, from_func: str, to_func: str, max_depth: int = 5) -> Optional[List[str]]:
        """
        Find a call chain from one function to another.

        Args:
            from_func: Starting function
            to_func: Target function
            max_depth: Maximum chain length

        Returns:
            List of function names forming the chain, or None if no chain exists
        """
        if from_func == to_func:
            return [from_func]

        visited = set()
        queue = [(from_func, [from_func])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            for callee in self.get_callees(current):
                if callee == to_func:
                    return path + [callee]
                queue.append((callee, path + [callee]))

        return None

    # ========================================================================
    # Data Flow Analysis
    # ========================================================================

    def _analyze_data_flows(self) -> None:
        """Analyze data flows between functions."""
        for func_name, context in self.call_graph.nodes.items():
            # Track parameter flows
            for call_site in context.calls_made:
                callee_context = self.call_graph.nodes.get(call_site.callee_function)
                if not callee_context:
                    continue

                # Match arguments to parameters
                for i, arg in enumerate(call_site.arguments):
                    if i < len(callee_context.parameters):
                        param_name = callee_context.parameters[i]

                        # Extract variable name from argument
                        if isinstance(arg, IRIdentifier):
                            self.data_flows.append(DataFlow(
                                from_variable=arg.name,
                                to_variable=param_name,
                                from_function=func_name,
                                to_function=call_site.callee_function,
                                flow_type="parameter",
                                confidence=1.0
                            ))

    def get_data_flows_to(self, function_name: str, variable_name: str) -> List[DataFlow]:
        """
        Get all data flows into a variable in a function.

        Args:
            function_name: Name of function
            variable_name: Name of variable

        Returns:
            List of data flows targeting this variable
        """
        return [
            flow for flow in self.data_flows
            if flow.to_function == function_name and flow.to_variable == variable_name
        ]

    def get_data_flows_from(self, function_name: str, variable_name: str) -> List[DataFlow]:
        """
        Get all data flows from a variable in a function.

        Args:
            function_name: Name of function
            variable_name: Name of variable

        Returns:
            List of data flows originating from this variable
        """
        return [
            flow for flow in self.data_flows
            if flow.from_function == function_name and flow.from_variable == variable_name
        ]

    # ========================================================================
    # Cross-Function Type Inference
    # ========================================================================

    def infer_return_type(self, function_name: str) -> Optional[TypeInfo]:
        """
        Infer return type of a function based on how its return value is used.

        Args:
            function_name: Name of function

        Returns:
            TypeInfo with inferred return type, or None

        Strategy:
        1. Look at how return value is used in callers
        2. Check property accesses on return value
        3. Check operations performed on return value
        4. Combine evidence with confidence scoring
        """
        if function_name not in self.call_graph.nodes:
            return None

        context = self.call_graph.nodes[function_name]
        evidence = []

        # Check what callers do with the return value
        for caller in context.called_by:
            caller_context = self.call_graph.nodes.get(caller)
            if not caller_context:
                continue

            # Find call sites in caller
            for call_site in caller_context.calls_made:
                if call_site.callee_function != function_name:
                    continue

                # TODO: Track what caller does with return value
                # This would require tracking assignments to see how the result is used

        # Analyze return expressions in the function itself
        if context.return_expressions:
            # If all returns are consistent, we can infer the type
            # (simplified - could do more sophisticated analysis)
            pass

        return None

    def infer_parameter_type(self, function_name: str, parameter_name: str) -> Optional[TypeInfo]:
        """
        Infer parameter type based on how it's passed and used.

        Args:
            function_name: Name of function
            parameter_name: Name of parameter

        Returns:
            TypeInfo with inferred type, or None

        Strategy:
        1. Check what types are passed by callers
        2. Check how parameter is used in function body
        3. Combine evidence with confidence scoring
        """
        if function_name not in self.call_graph.nodes:
            return None

        context = self.call_graph.nodes[function_name]

        # Check usage patterns
        if parameter_name in context.variable_usage:
            usage = context.variable_usage[parameter_name]

            # Property accesses suggest object type
            if usage.property_accesses:
                # Has properties like 'name', 'email' -> likely custom object
                return TypeInfo(
                    pw_type="object",
                    confidence=0.7,
                    source="inferred_from_usage"
                )

            # Operators suggest primitive types
            if "+" in usage.operators_used:
                # Could be string concatenation or numeric addition
                return TypeInfo(
                    pw_type="any",  # Ambiguous
                    confidence=0.3,
                    source="inferred_from_usage"
                )

        # Check what callers pass
        flows = self.get_data_flows_to(function_name, parameter_name)
        if flows:
            # Could analyze the types of variables being passed
            # (simplified for now)
            pass

        return None

    def get_variable_scope(self, function_name: str, variable_name: str) -> str:
        """
        Determine the scope of a variable.

        Args:
            function_name: Name of function
            variable_name: Name of variable

        Returns:
            Scope type: "parameter", "local", "global", "unknown"
        """
        if function_name not in self.call_graph.nodes:
            return "unknown"

        context = self.call_graph.nodes[function_name]

        if variable_name in context.parameters:
            return "parameter"
        elif variable_name in context.local_variables:
            return "local"
        elif variable_name in self.global_variables:
            return "global"
        else:
            return "unknown"

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_function_context(self, function_name: str) -> Optional[FunctionContext]:
        """
        Get the context for a function.

        Args:
            function_name: Name of function

        Returns:
            FunctionContext or None
        """
        return self.call_graph.nodes.get(function_name)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the analyzed code.

        Returns:
            Dictionary with various metrics
        """
        total_functions = len(self.call_graph.nodes)
        total_calls = sum(len(ctx.calls_made) for ctx in self.call_graph.nodes.values())
        total_variables = sum(len(ctx.variable_usage) for ctx in self.call_graph.nodes.values())

        return {
            "total_functions": total_functions,
            "total_call_sites": total_calls,
            "total_variables": total_variables,
            "total_data_flows": len(self.data_flows),
            "average_calls_per_function": total_calls / total_functions if total_functions > 0 else 0,
            "average_variables_per_function": total_variables / total_functions if total_functions > 0 else 0,
        }

    def visualize_call_graph(self) -> str:
        """
        Generate a text visualization of the call graph.

        Returns:
            String representation of call graph
        """
        lines = ["Call Graph:", "=" * 60]

        for func_name in sorted(self.call_graph.nodes.keys()):
            callees = self.get_callees(func_name)
            if callees:
                lines.append(f"{func_name}:")
                for callee in callees:
                    lines.append(f"  → {callee}")
            else:
                lines.append(f"{func_name}: (no calls)")

        return "\n".join(lines)


# ============================================================================
# Utility Functions
# ============================================================================


def create_context_analyzer() -> ContextAnalyzer:
    """Create and return a ContextAnalyzer instance."""
    return ContextAnalyzer()
