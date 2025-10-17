# gurddy/variable.py (updated to fix NameError and recursion)
from typing import Union, Tuple, List, Optional
from .constraint import Constraint, LinearConstraint

class Variable:
    def __init__(self, name: str, low_bound: Optional[float] = None, up_bound: Optional[float] = None,
                 cat: str = 'Continuous', domain: Optional[List[int]] = None):
        self.name = name
        self.low_bound = low_bound
        self.up_bound = up_bound
        self.cat = cat  # 'Continuous', 'Integer', 'Binary', 'Domain'
        self.domain = tuple(domain) if domain else None

    def __hash__(self):
        # Variables are identified by name for hashing purposes
        return hash(self.name)

    def __repr__(self):
        return f"Variable({self.name})"

    def __add__(self, other):
        return Expression(self) + Expression(other)

    def __sub__(self, other):
        return Expression(self) - Expression(other)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Expression(self) * other
        else:
            return Expression(self) * Expression(other)

    def __truediv__(self, other):
        return Expression(self) / Expression(other)

    def __eq__(self, other):
        return Expression(self) == Expression(other)

    def __le__(self, other):
        return Expression(self) <= Expression(other)

    def __ge__(self, other):
        return Expression(self) >= Expression(other)

    def __lt__(self, other):
        return Expression(self) < Expression(other)

    def __gt__(self, other):
        return Expression(self) > Expression(other)

    def __ne__(self, other):
        return Expression(self) != Expression(other)
    
    def __rmul__(self, other):
        return self * other
    
    def __radd__(self, other):
        return self + other
    
    def __rsub__(self, other):
        return Expression(other) - Expression(self)


class Expression:
    def __init__(self, term: Union[Variable, float, int]):
        # If term is a numeric constant
        if isinstance(term, (int, float)):
            self.terms = {}
            self.constant = float(term)
        # If term is already an Expression, copy its contents
        elif isinstance(term, Expression):
            self.terms = dict(term.terms)
            self.constant = float(term.constant)
        else:
            # Assume term is a Variable-like object
            self.terms = {term: 1.0}
            self.constant = 0.0

    def __add__(self, other):
        expr = Expression(0)
        expr.terms = {**self.terms}
        expr.constant = self.constant
        if isinstance(other, Expression):
            for var, coeff in other.terms.items():
                expr.terms[var] = expr.terms.get(var, 0) + coeff
            expr.constant += other.constant
        else:
            expr.constant += other
        return expr

    def __sub__(self, other):
        return self + (-1 * other)

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise ValueError("Multiplication only supported with scalars.")
        expr = Expression(0)
        expr.terms = {var: coeff * other for var, coeff in self.terms.items()}
        expr.constant = self.constant * other
        return expr

    def __truediv__(self, other):
        if not isinstance(other, (int, float)):
            raise ValueError("Division only supported with scalars.")
        return self * (1 / other)

    def __rmul__(self, other):
        return self * other

    def __radd__(self, other):
        return self + other

    def __rsub__(self, other):
        return other + (-1 * self)

    def __eq__(self, other):
        return LinearConstraint(self - Expression(other), '==')

    def __le__(self, other):
        return LinearConstraint(self - Expression(other), '<=')

    def __ge__(self, other):
        return LinearConstraint(self - Expression(other), '>=')

    def __lt__(self, other):
        return LinearConstraint(self - Expression(other), '<')

    def __gt__(self, other):
        return LinearConstraint(self - Expression(other), '>')

    def __ne__(self, other):
        return LinearConstraint(self - Expression(other), '!=')