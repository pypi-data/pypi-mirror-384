#!/usr/bin/env python3
import ast
import sys
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Optional, Any
from pathlib import Path
from colorama import init, Fore, Style

# initialize colorama for cross-platform colored output
init()

@dataclass
class Complexity:
    expression: str
    is_approximate: bool = False
    details: List[str] = field(default_factory=list)
    
    @classmethod
    def constant(cls):
        return cls("O(1)", False, [])
    
    @classmethod
    def linear(cls, coefficient: int = 1):
        expr = f"O({coefficient}n)" if coefficient != 1 else "O(n)"
        return cls(expr, False, [])
    
    @classmethod
    def approximate(cls, expr: str):
        return cls(expr, True, [])
    
    def with_detail(self, detail: str):
        self.details.append(detail)
        return self
    
    def combine_sequential(self, other: 'Complexity') -> 'Complexity':
        """For sequential operations, we add complexities"""
        is_approx = self.is_approximate or other.is_approximate
        details = self.details + other.details
        
        # Extract inner expressions (remove O(...) wrapper)
        expr1_inner = self._extract_inner(self.expression)
        expr2_inner = other._extract_inner(other.expression)
        
        # Combine the inner expressions
        combined_inner = self._add_expressions(expr1_inner, expr2_inner)
        expr = f"O({combined_inner})"
        
        return Complexity(expr, is_approx, details)
    
    def combine_nested(self, other: 'Complexity') -> 'Complexity':
        """For nested operations, we multiply complexities"""
        is_approx = self.is_approximate or other.is_approximate
        details = self.details + other.details
        
        # Extract inner expressions (remove O(...) wrapper)
        expr1_inner = self._extract_inner(self.expression)
        expr2_inner = other._extract_inner(other.expression)
        
        # Multiply the inner expressions
        combined_inner = self._multiply_expressions(expr1_inner, expr2_inner)
        expr = f"O({combined_inner})"
        
        return Complexity(expr, is_approx, details)
    
    def max(self, other: 'Complexity') -> 'Complexity':
        """Return the maximum complexity (for if/else branches)"""
        # for branches, we should take the worse case
        # this is a simplified comparison
        self_weight = self._get_weight()
        other_weight = other._get_weight()
        
        if self_weight >= other_weight:
            return self
        else:
            return other

    def _extract_inner(self, expr: str) -> str:
        """Extract the inner expression from O(...) notation"""
        if expr.startswith("O(") and expr.endswith(")"):
            return expr[2:-1]
        return expr
    
    def _add_expressions(self, expr1: str, expr2: str) -> str:
        """Add two complexity expressions"""
        import re
        
        # Parse both expressions into term dictionaries
        terms = defaultdict(int)
        
        for expr in [expr1, expr2]:
            parsed = self._parse_expression(expr)
            for term_type, coef in parsed.items():
                terms[term_type] += coef
        
        return self._format_expression(terms)
    
    def _multiply_expressions(self, expr1: str, expr2: str) -> str:
        """Multiply two complexity expressions"""
        import re
        
        # Handle constant multiplication
        if expr1 == "1":
            return expr2
        if expr2 == "1":
            return expr1
        
        # Parse expressions
        terms1 = self._parse_expression(expr1)
        terms2 = self._parse_expression(expr2)
        
        # If both are single terms, multiply them
        if len(terms1) == 1 and len(terms2) == 1:
            term1_type, coef1 = list(terms1.items())[0]
            term2_type, coef2 = list(terms2.items())[0]
            
            # Multiply coefficients
            new_coef = coef1 * coef2
            
            # Combine term types
            new_term = self._multiply_term_types(term1_type, term2_type)
            
            result_terms = {new_term: new_coef}
            return self._format_expression(result_terms)
        else:
            # For complex expressions, use distributive property
            result_terms = defaultdict(int)
            for term1_type, coef1 in terms1.items():
                for term2_type, coef2 in terms2.items():
                    new_term = self._multiply_term_types(term1_type, term2_type)
                    result_terms[new_term] += coef1 * coef2
            return self._format_expression(result_terms)
    
    def _parse_expression(self, expr: str) -> Dict[str, int]:
        """Parse a complexity expression into term types and coefficients"""
        import re
        
        terms = defaultdict(int)
        
        if not expr or expr == "0":
            # O(0) means no operations
            return terms
        elif expr == "1":
            terms["1"] = 1
            return terms
        
        # Split by + (but not inside parentheses)
        parts = []
        current = ""
        depth = 0
        for char in expr:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == '+' and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            parts.append(current.strip())
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if this is a multiplication (e.g., n*n)
            if '*' in part and 'log' not in part:
                # Parse as multiplication and convert to power
                mult_result = self._parse_multiplication(part)
                for term_type, coef in mult_result.items():
                    terms[term_type] += coef
                continue
            
            # Match different patterns
            if part == "1":
                terms["1"] += 1
            elif match := re.match(r'^(\d+)$', part):
                terms["1"] += int(match.group(1))
            elif part == "n":
                terms["n"] += 1
            elif match := re.match(r'^(\d+)n$', part):
                terms["n"] += int(match.group(1))
            elif "n*log(n)" in part or "n log(n)" in part:
                if match := re.match(r'^(\d+)\s*n\*log\(n\)$', part):
                    terms["n*log(n)"] += int(match.group(1))
                else:
                    terms["n*log(n)"] += 1
            elif "log(n)" in part:
                if match := re.match(r'^(\d+)\s*log\(n\)$', part):
                    terms["log(n)"] += int(match.group(1))
                else:
                    terms["log(n)"] += 1
            elif "n²" in part or "n^2" in part:
                terms["n²"] += 1
            elif "n³" in part or "n^3" in part:
                terms["n³"] += 1
            elif "n⁴" in part or "n^4" in part:
                terms["n⁴"] += 1
            else:
                # Unknown term, keep as-is with coefficient 1
                terms[part] += 1
        
        if not terms:
            terms["1"] = 1
        
        return terms
    
    def _parse_multiplication(self, expr: str) -> Dict[str, int]:
        """Parse a multiplication expression like n*n into term dict"""
        parts = expr.split('*')
        result_term = "1"
        result_coef = 1
        
        for part in parts:
            part = part.strip()
            # Parse each part as a simple term
            if part == "n":
                result_term = self._multiply_term_types(result_term, "n")
            elif part == "1" or not part:
                continue
            else:
                # Try to parse as term
                import re
                if match := re.match(r'^(\d+)n$', part):
                    result_coef *= int(match.group(1))
                    result_term = self._multiply_term_types(result_term, "n")
                elif match := re.match(r'^(\d+)$', part):
                    result_coef *= int(match.group(1))
                elif "n²" in part or "n^2" in part:
                    result_term = self._multiply_term_types(result_term, "n²")
                elif "n³" in part or "n^3" in part:
                    result_term = self._multiply_term_types(result_term, "n³")
                elif part == "log(n)":
                    result_term = self._multiply_term_types(result_term, "log(n)")
                else:
                    result_term = self._multiply_term_types(result_term, part)
        
        return {result_term: result_coef}
    
    def _multiply_term_types(self, type1: str, type2: str) -> str:
        """Multiply two term types (e.g., n * n = n²)"""
        if type1 == "1":
            return type2
        if type2 == "1":
            return type1
        
        # Count the power of n in each term
        power1 = self._get_n_power(type1)
        power2 = self._get_n_power(type2)
        new_power = power1 + power2
        
        # Check for log terms
        has_log1 = "log" in type1
        has_log2 = "log" in type2
        
        if new_power == 0:
            if has_log1 and has_log2:
                return "log²(n)"
            elif has_log1 or has_log2:
                return "log(n)"
            else:
                return "1"
        elif new_power == 1:
            if has_log1 or has_log2:
                return "n*log(n)"
            else:
                return "n"
        elif new_power == 2:
            if has_log1 or has_log2:
                return "n²*log(n)"
            else:
                return "n²"
        elif new_power == 3:
            if has_log1 or has_log2:
                return "n³*log(n)"
            else:
                return "n³"
        elif new_power == 4:
            if has_log1 or has_log2:
                return "n⁴*log(n)"
            else:
                return "n⁴"
        else:
            log_part = "*log(n)" if (has_log1 or has_log2) else ""
            return f"n^{new_power}{log_part}"
    
    def _get_n_power(self, term: str) -> int:
        """Get the power of n in a term"""
        import re
        
        if term == "1" or "log" in term and "n" not in term:
            return 0
        elif term == "n" or (term == "n*log(n)"):
            return 1
        elif "n²" in term or "n^2" in term:
            return 2
        elif "n³" in term or "n^3" in term:
            return 3
        elif "n⁴" in term or "n^4" in term:
            return 4
        elif match := re.match(r'n\^(\d+)', term):
            return int(match.group(1))
        elif "n" in term:
            return 1
        else:
            return 0
    
    def _format_expression(self, terms: Dict[str, int]) -> str:
        """Format a term dictionary back to a string expression"""
        if not terms:
            return "1"
        
        # Order terms by complexity (highest first)
        order = ["n⁴", "n³", "n²", "n*log(n)", "n", "log(n)", "1"]
        result_parts = []
        
        for term_type in order:
            if term_type in terms and terms[term_type] > 0:
                coef = terms[term_type]
                if term_type == "1":
                    result_parts.append(str(coef))
                elif term_type == "n":
                    if coef == 1:
                        result_parts.append("n")
                    else:
                        result_parts.append(f"{coef}n")
                elif term_type == "log(n)":
                    if coef == 1:
                        result_parts.append("log(n)")
                    else:
                        result_parts.append(f"{coef}log(n)")
                else:
                    # Higher order terms typically don't show coefficient
                    if coef == 1:
                        result_parts.append(term_type)
                    else:
                        result_parts.append(f"{coef}{term_type}")
        
        # Add any unknown terms
        for term_type, coef in terms.items():
            if term_type not in order and coef > 0:
                if coef == 1:
                    result_parts.append(term_type)
                else:
                    result_parts.append(f"{coef}*{term_type}")
        
        return " + ".join(result_parts) if result_parts else "1"
    
    def _combine_similar_terms(self, expr1: str, expr2: str) -> Optional[str]:
        """Combine similar complexity terms with coefficients"""
        import re
        
        # parse expressions into a dict of complexity -> coefficient
        terms = defaultdict(int)
        
        for expr in [expr1, expr2]:
            # split by + if present
            parts = expr.split('+') if '+' in expr else [expr]
            for part in parts:
                part = part.strip()
                if part == "O(1)":
                    terms["1"] += 1
                elif part == "O(n)":
                    terms["n"] += 1
                elif match := re.match(r'O\((\d+)\)', part):
                    terms["1"] += int(match.group(1))
                elif match := re.match(r'O\((\d*)n\)', part):
                    coef = int(match.group(1)) if match.group(1) else 1
                    terms["n"] += coef
                elif "n*log(n)" in part:
                    terms["n*log(n)"] += 1
                elif "n²" in part:
                    terms["n²"] += 1
                elif "n³" in part:
                    terms["n³"] += 1
                else:
                    return None  # can't parse, return None
        
        # build result
        result_parts = []
        for complexity in ["n³", "n²", "n*log(n)", "n", "1"]:
            if complexity in terms and terms[complexity] > 0:
                coef = terms[complexity]
                result_parts.append(f"O({coef if coef > 1 else ''}{complexity})")
        
        return "+".join(result_parts) if result_parts else None
    
    
    def _get_weight(self) -> int:
        """Get a rough weight for complexity comparison"""
        expr = self.expression
        if 'n⁴' in expr or 'n^4' in expr:
            return 4
        elif 'n³' in expr or 'n^3' in expr:
            return 3
        elif 'n²' in expr or 'n^2' in expr:
            return 2
        elif 'n*log' in expr:
            return 1.5
        elif 'n' in expr:
            return 1
        elif 'log' in expr:
            return 0.5
        else:
            return 0
    
    def simplify(self) -> 'Complexity':
        """Simplify the complexity expression WITHOUT reducing to dominant term"""
        expr = self.expression
        
        # Extract inner expression
        inner = self._extract_inner(expr)
        
        # Parse and reformat to combine like terms
        terms = self._parse_expression(inner)
        formatted = self._format_expression(terms)
        
        # Handle edge cases
        if formatted == "0" or not formatted:
            formatted = "1"
        
        expr = f"O({formatted})"
        
        return Complexity(expr, self.is_approximate, self.details)
    
    def _simplify_multiplications(self, expr: str) -> str:
        """Simplify multiplication expressions"""
        import re
        
        # handle O(n²)*O(n²) -> O(n⁴) etc
        if "O(n²)*O(n²)" in expr:
            expr = expr.replace("O(n²)*O(n²)", "O(n⁴)")
        if "O(n³)*O(n)" in expr or "O(n)*O(n³)" in expr:
            expr = expr.replace("O(n³)*O(n)", "O(n⁴)")
            expr = expr.replace("O(n)*O(n³)", "O(n⁴)")
        if "O(n²)*O(n)" in expr or "O(n)*O(n²)" in expr:
            expr = expr.replace("O(n²)*O(n)", "O(n³)")
            expr = expr.replace("O(n)*O(n²)", "O(n³)")
        
        # count O(n) multiplications
        n_count = expr.count("O(n)*O(n)")
        if n_count > 0:
            power_notation = {1: "²", 2: "⁴"}
            if n_count in power_notation:
                expr = expr.replace("O(n)*O(n)", f"O(n{power_notation[n_count]})", 1)

        # count individual O(n) terms being multiplied
        parts = []
        current = ""
        depth = 0
        
        for char in expr:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == '*' and depth == 0:
                parts.append(current)
                current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        # count O(n) occurrences
        n_count = sum(1 for p in parts if p == "O(n)")
        other_parts = [p for p in parts if p != "O(n)" and p != "O(1)"]
        
        if n_count >= 2:
            power_notation = {2: "²", 3: "³", 4: "⁴"}
            if n_count in power_notation:
                result = f"O(n{power_notation[n_count]})"
            else:
                result = f"O(n^{n_count})"
            # add other multiplicative factors
            for part in other_parts:
                if "log" in part:
                    result = result.replace(")", "*log(n))")
                elif part and part != "O(1)":
                    result = f"{result}*{part}"
            
            expr = result
        elif n_count == 1:
            # single O(n) with other factors
            result = "O(n)"
            for part in other_parts:
                if "log" in part:
                    result = "O(n*log(n))"
                elif part and part != "O(1)":
                    result = f"{result}*{part}"
            expr = result
        
        return expr
    
    def _combine_additions(self, expr: str) -> str:
        """Combine similar terms in additions"""
        # Extract inner part of O(...)
        inner = self._extract_inner(expr)
        
        # Parse and reformat
        terms = self._parse_expression(inner)
        formatted = self._format_expression(terms)
        
        return f"O({formatted})"

@dataclass
class AntiPattern:
    line: int
    pattern_type: str
    description: str

@dataclass
class FunctionAnalysis:
    name: str
    complexity: Complexity
    anti_patterns: List[AntiPattern]

class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.functions: Dict[str, Complexity] = {}
        self.variable_types: Dict[str, str] = {}
        self.call_stack: List[str] = []  # Track call stack for recursion
        self.max_call_depth = 3
        self.current_class = None
        self.results: List[FunctionAnalysis] = []
        self.anti_patterns: List[AntiPattern] = []
        
    def analyze_file(self, content: str, filename: str = "<file>") -> List[FunctionAnalysis]:
        """Analyze Python file content"""
        try:
            tree = ast.parse(content, filename)
        except SyntaxError as e:
            raise ValueError(f"Parse error: {e}")
        
        self.visit(tree)
        return self.results
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition"""
        self.anti_patterns = []
        self.variable_types.clear()
        self.call_stack = []  # reset call stack for each function
        
        # extract type annotations from parameters
        for arg in node.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Subscript):
                    # handle List[int], Dict[str, int], etc.
                    if isinstance(arg.annotation.value, ast.Name):
                        self.variable_types[arg.arg] = arg.annotation.value.id
                elif isinstance(arg.annotation, ast.Name):
                    self.variable_types[arg.arg] = arg.annotation.id
        
        # analyze function body
        complexity = self.analyze_body(node.body)
        
        # store function name with class prefix if in a class
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name
        
        self.functions[func_name] = complexity
        
        analysis = FunctionAnalysis(
            name=func_name,
            complexity=complexity,
            anti_patterns=self.anti_patterns.copy()
        )
        self.results.append(analysis)
        
        # don't visit nested functions
        return
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def analyze_body(self, body: List[ast.stmt]) -> Complexity:
        """Analyze a list of statements"""
        # Track variable assignments for type inference
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Name):
                        if stmt.value.func.id == 'set':
                            # Variable is assigned a set
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    self.variable_types[target.id] = 'set'
                        elif stmt.value.func.id == 'list':
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    self.variable_types[target.id] = 'list'
        
        # Start with O(0) by using special marker
        total = None
        
        for stmt in body:
            stmt_complexity = self.analyze_statement(stmt)
            if total is None:
                total = stmt_complexity
            else:
                total = total.combine_sequential(stmt_complexity)
        
        # If empty body, return O(1)
        if total is None:
            total = Complexity.constant()
        
        return total.simplify()
    
    def analyze_statement(self, stmt: ast.stmt) -> Complexity:
        """Analyze a single statement"""
        if isinstance(stmt, ast.Pass):
            # Pass statements have no computational cost
            return Complexity("O(0)", False, [])
        elif isinstance(stmt, ast.For):
            return self.analyze_for_loop(stmt)
        elif isinstance(stmt, ast.While):
            return self.analyze_while_loop(stmt)
        elif isinstance(stmt, ast.If):
            return self.analyze_if(stmt)
        elif isinstance(stmt, (ast.Return, ast.Expr)):
            if isinstance(stmt, ast.Return) and stmt.value:
                return self.analyze_expr(stmt.value)
            elif isinstance(stmt, ast.Expr):
                return self.analyze_expr(stmt.value)
            return Complexity.constant()
        elif isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            if isinstance(stmt, ast.Assign):
                # Analyze the RHS expression
                value_complexity = self.analyze_expr(stmt.value)
                # If it's just a constant, the whole assignment is O(1)
                # Otherwise, we have the complexity of computing the value
                if value_complexity.expression == "O(1)":
                    return Complexity.constant()
                else:
                    # Assignment + value computation
                    return Complexity.constant().combine_sequential(value_complexity)
            elif isinstance(stmt, ast.AugAssign):
                value_complexity = self.analyze_expr(stmt.value)
                if value_complexity.expression == "O(1)":
                    return Complexity.constant()
                else:
                    return Complexity.constant().combine_sequential(value_complexity)
            elif isinstance(stmt, ast.AnnAssign) and stmt.value:
                value_complexity = self.analyze_expr(stmt.value)
                if value_complexity.expression == "O(1)":
                    return Complexity.constant()
                else:
                    return Complexity.constant().combine_sequential(value_complexity)
            return Complexity.constant()
        else:
            return Complexity.constant()
    
    def analyze_for_loop(self, node: ast.For) -> Complexity:
        """Analyze for loop complexity"""
        iter_complexity = self.estimate_iteration_count(node.iter)
        body_complexity = self.analyze_body(node.body)
        
        combined = iter_complexity.combine_nested(body_complexity)
        return combined.with_detail("for loop").simplify()
    
    def analyze_while_loop(self, node: ast.While) -> Complexity:
        """Analyze while loop complexity"""
        body_complexity = self.analyze_body(node.body)
        
        # while loops have unknown iterations in static analysis
        if body_complexity.expression == "O(1)":
            result = Complexity.linear(1)
            result.is_approximate = True
        else:
            result = body_complexity.combine_nested(Complexity.linear(1))
            result.is_approximate = True
        
        result = result.with_detail("while loop (unknown iterations)").simplify()
        result.is_approximate = True
        return result
    
    def analyze_if(self, node: ast.If) -> Complexity:
        """Analyze if statement - test condition plus max of branches"""
        # Analyze the test condition
        test_complexity = self.analyze_expr(node.test)
        
        # Analyze both branches
        if_body = self.analyze_body(node.body)
        else_body = self.analyze_body(node.orelse)
        
        # Take max of branches and add the test
        branch_complexity = if_body.max(else_body)
        return test_complexity.combine_sequential(branch_complexity)
    
    def estimate_iteration_count(self, iter_node: ast.expr) -> Complexity:
        """Estimate iteration count for loop iterator"""
        if isinstance(iter_node, ast.Call):
            if isinstance(iter_node.func, ast.Name):
                if iter_node.func.id == 'range':
                    return Complexity.linear(1)
                elif iter_node.func.id in ('enumerate', 'zip'):
                    # these iterate over their arguments
                    if iter_node.args:
                        return self.estimate_iteration_count(iter_node.args[0])
                    return Complexity.linear(1)
            return Complexity.approximate("O(n)")
        elif isinstance(iter_node, (ast.Name, ast.Attribute)):
            return Complexity.linear(1)
        elif isinstance(iter_node, (ast.List, ast.Tuple)):
            # literal list/tuple - count elements
            return Complexity.linear(1)
        else:
            return Complexity.approximate("O(n)")
    
    def analyze_expr(self, expr: ast.expr) -> Complexity:
        """Analyze expression complexity"""
        if isinstance(expr, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return self.analyze_comprehension(expr)
        elif isinstance(expr, ast.Call):
            return self.analyze_call(expr)
        elif isinstance(expr, ast.Compare):
            return self.analyze_compare(expr)
        elif isinstance(expr, ast.Lambda):
            # analyze lambda body as expression
            return self.analyze_expr(expr.body)
        elif isinstance(expr, ast.List):
            total = Complexity.constant()
            for el in expr.elts:
                total = total.combine_sequential(self.analyze_expr(el))
            return total
        else:
            return Complexity.constant()
    
    def analyze_comprehension(self, node) -> Complexity:
        """Analyze list/set/dict comprehension or generator expression"""
        complexity = Complexity.constant()
        
        # Analyze the iteration complexity
        for generator in node.generators:
            iter_complexity = self.estimate_iteration_count(generator.iter)
            complexity = complexity.combine_nested(iter_complexity)
        
        # Analyze the element expression (which might be another comprehension)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            elt_complexity = self.analyze_expr(node.elt)
            complexity = complexity.combine_nested(elt_complexity)
        elif isinstance(node, ast.DictComp):
            key_complexity = self.analyze_expr(node.key)
            value_complexity = self.analyze_expr(node.value)
            elt_complexity = key_complexity.combine_sequential(value_complexity)
            complexity = complexity.combine_nested(elt_complexity)
        
        # check for anti-pattern (using list comp where generator would work)
        if isinstance(node, ast.ListComp):
            self.anti_patterns.append(AntiPattern(
                line=node.lineno,
                pattern_type="list_comprehension",
                description="List comprehension could potentially be replaced with generator expression for memory efficiency"
            ))
        
        return complexity.with_detail("comprehension").simplify()
    
    def analyze_call(self, node: ast.Call) -> Complexity:
        """Analyze function call complexity"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # built-in functions with known complexity
            complexity_map = {
                'len': Complexity.constant(),
                'print': Complexity.constant(),
                'sum': Complexity.linear(1),
                'max': Complexity.linear(1),
                'min': Complexity.linear(1),
                'sorted': Complexity("O(n*log(n))", False),
                'reversed': Complexity.linear(1),
                'enumerate': Complexity.constant(),
                'zip': Complexity.constant(),
                'map': Complexity.constant(),
                'filter': Complexity.constant(),
                'list': Complexity.linear(1) if node.args else Complexity.constant(),
                'set': Complexity.linear(1) if node.args else Complexity.constant(),
                'dict': Complexity.constant(),
                'all': Complexity.linear(1),
                'any': Complexity.linear(1),
            }
            
            if func_name in complexity_map:
                complexity = complexity_map[func_name]
            elif func_name in self.functions:
                # check recursion depth
                if func_name in self.call_stack:
                    # already in call stack - check depth
                    depth = self.call_stack.count(func_name)
                    if depth >= self.max_call_depth:
                        known_complexity = self.functions.get(func_name, Complexity.approximate("O(?)"))
                        complexity = Complexity.approximate(f"at least {known_complexity.expression}")
                        complexity.with_detail(f"(maximum recursion depth {self.max_call_depth} reached)")
                    else:
                        # allow the recursive call but track it
                        self.call_stack.append(func_name)
                        complexity = self.functions[func_name]
                        self.call_stack.pop()
                else:
                    # first call to this function
                    self.call_stack.append(func_name)
                    complexity = self.functions[func_name]
                    self.call_stack.pop()
            else:
                complexity = Complexity.approximate("O(?)")
                complexity.with_detail(f"unknown function: {func_name}")
            
            # analyze arguments
            for arg in node.args:
                arg_complexity = self.analyze_expr(arg)
                complexity = complexity.combine_sequential(arg_complexity)
            
            return complexity
            
        elif isinstance(node.func, ast.Attribute):
            return self.analyze_method_call(node.func)
        else:
            return Complexity.approximate("O(?)")
    
    def analyze_method_call(self, attr: ast.Attribute) -> Complexity:
        """Analyze method call complexity"""
        method_complexity = {
            'append': Complexity.constant(),
            'pop': Complexity.constant(),
            'insert': Complexity.linear(1),
            'remove': Complexity.linear(1),
            'sort': Complexity("O(n*log(n))", False),
            'index': Complexity.linear(1),
            'count': Complexity.linear(1),
            'extend': Complexity.linear(1),
            'copy': Complexity.linear(1),
            'clear': Complexity.constant(),
            'get': Complexity.constant(),
            'items': Complexity.linear(1),
            'keys': Complexity.linear(1),
            'values': Complexity.linear(1),
            'update': Complexity.linear(1),
            'add': Complexity.constant(),  # set.add
            'discard': Complexity.constant(),  # set.discard
            'union': Complexity.linear(1),
            'intersection': Complexity.linear(1),
            'difference': Complexity.linear(1),
        }
        
        return method_complexity.get(attr.attr, Complexity.approximate("O(?)")).simplify()
    
    def analyze_compare(self, node: ast.Compare) -> Complexity:
        """Analyze comparison operations"""
        for i, op in enumerate(node.ops):
            if isinstance(op, (ast.In, ast.NotIn)):
                if i < len(node.comparators):
                    comparator = node.comparators[i]
                    
                    if isinstance(comparator, ast.List):
                        # list literal membership test - always O(n)
                        self.anti_patterns.append(AntiPattern(
                            line=node.lineno,
                            pattern_type="list_membership",
                            description="Membership test with list literal - use set for O(1) lookup instead of O(n)"
                        ))
                        return Complexity.linear(1).with_detail("list membership check")
                    
                    elif isinstance(comparator, ast.Set):
                        # set literal membership test - O(1)
                        return Complexity.constant().with_detail("set membership check")
                    
                    elif isinstance(comparator, ast.Name):
                        # check variable type if known
                        var_type = self.variable_types.get(comparator.id)
                        if var_type in ('List', 'list'):
                            self.anti_patterns.append(AntiPattern(
                                line=node.lineno,
                                pattern_type="membership_check",
                                description="Membership test with List type - consider using Set for O(1) lookup instead of O(n)"
                            ))
                            return Complexity.linear(1).with_detail("list membership check")
                        elif var_type in ('Set', 'set', 'Dict', 'dict'):
                            return Complexity.constant().with_detail("set/dict membership check")
                        else:
                            # unknown type - assume worst case (list)
                            self.anti_patterns.append(AntiPattern(
                                line=node.lineno,
                                pattern_type="membership_check",
                                description="Membership test with unknown type - if this is a list, consider using set for O(1) lookup"
                            ))
                            return Complexity.approximate("O(n)").with_detail("membership check (unknown type)")
                    
                    elif isinstance(comparator, ast.Attribute):
                        # accessing an attribute - assume list for worst case
                        self.anti_patterns.append(AntiPattern(
                            line=node.lineno,
                            pattern_type="membership_check",
                            description="Membership test with unknown type - if this is a list, consider using set for O(1) lookup"
                        ))
                        return Complexity.approximate("O(n)").with_detail("membership check (unknown type)")
        
        return Complexity.constant()

def main(files: List[Path], **kwargs) -> None:
    for file_path in files:
        if not file_path.exists():
            print(f"{Fore.RED}{Style.BRIGHT}Error:{Style.RESET_ALL} File does not exist: {file_path}")
            continue
        
        if not file_path.is_file():
            print(f"{Fore.RED}{Style.BRIGHT}Error:{Style.RESET_ALL} Not a file: {file_path}")
            continue
        
        try:
            content = file_path.read_text()
        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Error:{Style.RESET_ALL} Failed to read file: {e}")
            continue
        
        analyzer = Analyzer()
        
        try:
            results = analyzer.analyze_file(content, str(file_path))
        except ValueError as e:
            print(f"{Fore.RED}{Style.BRIGHT}Analysis failed:{Style.RESET_ALL} {e}")
            continue
        
        print(f"\n{Fore.CYAN}{'═' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}  Python Complexity Analysis: {file_path}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═' * 80}{Style.RESET_ALL}\n")
        
        has_approximate = any(r.complexity.is_approximate for r in results)
        
        for analysis in results:
            approx_marker = " *" if analysis.complexity.is_approximate else ""
            
            print(f"{Fore.GREEN}{Style.BRIGHT}Function/Method:{Style.RESET_ALL} {Fore.YELLOW}{analysis.name}{Style.RESET_ALL}")
            print(f"  {Fore.BLUE}{Style.BRIGHT}Complexity:{Style.RESET_ALL} {Fore.MAGENTA}{analysis.complexity.expression}{Style.RESET_ALL}{Fore.RED}{Style.BRIGHT}{approx_marker}{Style.RESET_ALL}")
            
            if analysis.anti_patterns:
                print(f"  {Fore.YELLOW}{Style.BRIGHT}⚠ Performance Issues:{Style.RESET_ALL}")
                for ap in analysis.anti_patterns:
                    print(f"    {Fore.RED}•{Style.RESET_ALL} [line {ap.line}]: {Fore.YELLOW}{ap.description}{Style.RESET_ALL}")
            
            print()
        
        if has_approximate:
            print(f"{Fore.YELLOW}{Style.BRIGHT}Note:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}*{Style.RESET_ALL} Complexity marked with * is approximate due to static analysis limitations")

