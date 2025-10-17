# gurddy/constraint.py
from typing import List, Callable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    # Imports here are only for type checking to avoid circular imports at runtime
    from .variable import Expression, Variable
else:
    Expression = object  # placeholder for runtime; actual code should not rely on it at import time
    Variable = object

class Constraint:
    def __init__(self, expr, sense: str = '<='):
        # Use untyped expr at runtime to avoid circular import. For static typing, see TYPE_CHECKING above.
        self.expr = expr
        self.sense = sense  # '<=', '>=', '==', '!=' for CSP

class LinearConstraint(Constraint):
    pass

class AllDifferentConstraint(Constraint):
    def __init__(self, vars: List[Variable]):
        self.vars = vars
        self.expr = None
        self.sense = 'AllDifferent'

class FunctionConstraint(Constraint):
    def __init__(self, func: Callable, vars: Tuple[Variable, ...]):
        self.func = func
        self.vars = vars
        self.expr = None
        self.sense = 'Function'