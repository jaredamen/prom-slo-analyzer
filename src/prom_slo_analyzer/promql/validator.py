"""Basic PromQL syntax validation utilities."""

import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of PromQL validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def __post_init__(self) -> None:
        """Ensure lists are properly initialized."""
        if not hasattr(self, "errors") or self.errors is None:
            self.errors = []
        if not hasattr(self, "warnings") or self.warnings is None:
            self.warnings = []


class PromQLValidator:
    """Basic PromQL syntax validator.

    Provides simple validation for common PromQL syntax errors.
    Not a complete parser, but catches common issues.
    """

    def __init__(self) -> None:
        """Initialize validator with common patterns."""
        self._function_names = {
            "rate",
            "increase",
            "sum",
            "avg",
            "max",
            "min",
            "count",
            "histogram_quantile",
            "avg_over_time",
            "max_over_time",
            "min_over_time",
            "count_over_time",
            "stddev",
            "stdvar",
            "topk",
            "bottomk",
            "sort",
            "sort_desc",
            "abs",
            "ceil",
            "floor",
            "round",
            "ln",
            "log2",
            "log10",
            "exp",
            "sqrt",
            "time",
            "timestamp",
            "vector",
            "scalar",
            "clamp_max",
            "clamp_min",
            "changes",
            "deriv",
            "predict_linear",
            "holt_winters",
            "irate",
            "resets",
            "delta",
        }

        self._operators = {
            "+",
            "-",
            "*",
            "/",
            "%",
            "^",
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "=~",
            "!~",
            "and",
            "or",
            "unless",
        }

    def validate(self, promql: str) -> ValidationResult:
        """Validate a PromQL expression.

        Args:
            promql: PromQL expression to validate

        Returns:
            ValidationResult with validation outcome
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not promql or not promql.strip():
            errors.append("Empty PromQL expression")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        promql = promql.strip()

        # Check for basic syntax issues
        errors.extend(self._check_parentheses(promql))
        errors.extend(self._check_brackets(promql))
        errors.extend(self._check_braces(promql))
        errors.extend(self._check_quotes(promql))

        # Check function syntax
        warnings.extend(self._check_functions(promql))

        # Check for common issues
        warnings.extend(self._check_common_issues(promql))

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _check_parentheses(self, promql: str) -> list[str]:
        """Check for balanced parentheses."""
        errors = []
        count = 0

        for i, char in enumerate(promql):
            if char == "(":
                count += 1
            elif char == ")":
                count -= 1
                if count < 0:
                    errors.append(f"Unmatched closing parenthesis at position {i}")
                    break

        if count > 0:
            errors.append(f"Unmatched opening parentheses: {count}")

        return errors

    def _check_brackets(self, promql: str) -> list[str]:
        """Check for balanced square brackets (time ranges)."""
        errors = []
        count = 0

        for i, char in enumerate(promql):
            if char == "[":
                count += 1
            elif char == "]":
                count -= 1
                if count < 0:
                    errors.append(f"Unmatched closing bracket at position {i}")
                    break

        if count > 0:
            errors.append(f"Unmatched opening brackets: {count}")

        return errors

    def _check_braces(self, promql: str) -> list[str]:
        """Check for balanced curly braces (label matchers)."""
        errors = []
        count = 0

        for i, char in enumerate(promql):
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
                if count < 0:
                    errors.append(f"Unmatched closing brace at position {i}")
                    break

        if count > 0:
            errors.append(f"Unmatched opening braces: {count}")

        return errors

    def _check_quotes(self, promql: str) -> list[str]:
        """Check for balanced quotes in label values."""
        errors = []

        # Check double quotes
        in_quotes = False
        escaped = False
        for _i, char in enumerate(promql):
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == '"' and not escaped:
                in_quotes = not in_quotes
            escaped = False

        if in_quotes:
            errors.append("Unclosed double quote")

        return errors

    def _check_functions(self, promql: str) -> list[str]:
        """Check for valid function usage."""
        warnings = []

        # Find function calls
        function_pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        matches = re.finditer(function_pattern, promql)

        for match in matches:
            func_name = match.group(1)
            if func_name not in self._function_names:
                warnings.append(f"Unknown function: {func_name}")

        return warnings

    def _check_common_issues(self, promql: str) -> list[str]:
        """Check for common PromQL issues and best practices."""
        warnings = []

        # Check for missing time ranges on range vectors
        if re.search(r"rate\([^)]+\)", promql) and "[" not in promql:
            warnings.append("rate() function typically requires a time range (e.g., [5m])")

        # Check for very short time ranges
        short_ranges = re.findall(r"\[(\d+)s\]", promql)
        for range_val in short_ranges:
            if int(range_val) < 30:
                warnings.append(f"Very short time range [{range_val}s] may be noisy")

        # Check for histogram_quantile without rate
        if "histogram_quantile" in promql and "rate(" not in promql:
            warnings.append("histogram_quantile() should typically use rate() for counters")

        # Check for potential label matcher issues
        if "==" in promql and "{" in promql:
            warnings.append("Use '=' not '==' for exact label matching in {}")

        return warnings

    def suggest_improvements(self, promql: str) -> list[str]:
        """Suggest improvements for a PromQL expression.

        Args:
            promql: PromQL expression to analyze

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Suggest aggregation for high-cardinality metrics
        if re.search(r"^\w+{[^}]+}$", promql.strip()):
            suggestions.append("Consider aggregating high-cardinality metrics with sum() or avg()")

        # Suggest rate for counters
        if "_total" in promql and "rate(" not in promql:
            suggestions.append("Counter metrics typically need rate() for meaningful values")

        # Suggest appropriate time ranges
        if "[1m]" in promql:
            suggestions.append("Consider using [5m] for better stability in production")

        return suggestions
