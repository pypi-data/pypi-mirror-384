# gurddy/model.py
from typing import List, Optional, Dict
from .variable import Variable, Expression
from .constraint import Constraint
# Avoid importing solvers at module import time to prevent circular imports.

class Model:
    def __init__(self, name: str = "Model", problem_type: str = "LP"):  # "LP" or "CSP"
        self.name = name
        self.problem_type = problem_type
        self.variables: Dict[str, Variable] = {}
        self.constraints: List[Constraint] = []
        self.objective: Optional[Expression] = None
        self.sense: str = "Maximize"  # or "Minimize" for LP, "Satisfy" for CSP
        self.solver = None

    def addVar(self, name: str, low_bound: Optional[float] = None, up_bound: Optional[float] = None,
               cat: str = 'Continuous', domain: Optional[List[int]] = None) -> Variable:
        var = Variable(name, low_bound, up_bound, cat, domain)
        self.variables[name] = var
        return var

    def addVars(self, names: List[str], **kwargs) -> Dict[str, Variable]:
        vars = {}
        for name in names:
            vars[name] = self.addVar(name, **kwargs)
        return vars

    def addConstraint(self, constraint: Constraint, name: Optional[str] = None):
        self.constraints.append(constraint)

    def setObjective(self, expr: Expression, sense: str = "Maximize"):
        self.objective = expr
        self.sense = sense

    def solve(self):
        if self.problem_type == "CSP":
            # Local import to avoid circular import issues
            from .solver.csp_solver import CSPSolver
            self.solver = CSPSolver(self)
        elif self.problem_type == "LP":
            from .solver.lp_solver import LPSolver
            self.solver = LPSolver(self)
        else:
            raise ValueError("Unsupported problem type.")
        return self.solver.solve()