# gurddy/solver/lp_solver.py (no major changes, but confirm isinstance uses LinearConstraint if needed)
import pulp  # Assuming PuLP is installed, as per reference
from ..model import Model
from ..constraint import  LinearConstraint

class LPSolver:
    def __init__(self, model: Model):
        self.model = model
        self.pulp_model = pulp.LpProblem(model.name, pulp.LpMaximize if model.sense == "Maximize" else pulp.LpMinimize)
        self.var_map = {}

    def solve(self):
        # Map variables
        for var_name, var in self.model.variables.items():
            cat = pulp.LpContinuous if var.cat == 'Continuous' else pulp.LpInteger if var.cat == 'Integer' else pulp.LpBinary
            self.var_map[var_name] = pulp.LpVariable(var_name, lowBound=var.low_bound, upBound=var.up_bound, cat=cat)

        # Objective
        if self.model.objective:
            obj_expr = pulp.lpSum([coeff * self.var_map[var.name] for var, coeff in self.model.objective.terms.items()]) + self.model.objective.constant
            self.pulp_model += obj_expr

        # Constraints
        for constr in self.model.constraints:
            if isinstance(constr, LinearConstraint):
                lhs = pulp.lpSum([coeff * self.var_map[var.name] for var, coeff in constr.expr.terms.items()]) + constr.expr.constant
                if constr.sense == '<=':
                    self.pulp_model += lhs <= 0
                elif constr.sense == '>=':
                    self.pulp_model += lhs >= 0
                elif constr.sense == '==':
                    self.pulp_model += lhs == 0

        status = self.pulp_model.solve(pulp.PULP_CBC_CMD(msg=False))
        if status == pulp.LpStatusOptimal:
            return {var_name: v.varValue for var_name, v in self.var_map.items()}
        return None