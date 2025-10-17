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
            obj_terms = [coeff * self.var_map[var.name] for var, coeff in self.model.objective.terms.items()]
            obj_expr = pulp.lpSum(obj_terms)
            # Add constant if it's a number
            if isinstance(self.model.objective.constant, (int, float)):
                obj_expr += self.model.objective.constant
            self.pulp_model += obj_expr

        # Constraints
        for constr in self.model.constraints:
            if isinstance(constr, LinearConstraint):
                lhs_terms = [coeff * self.var_map[var.name] for var, coeff in constr.expr.terms.items()]
                lhs = pulp.lpSum(lhs_terms)
                # Add constant if it's a number
                if isinstance(constr.expr.constant, (int, float)):
                    lhs += constr.expr.constant
                
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