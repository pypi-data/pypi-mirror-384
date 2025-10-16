### Gurddy
Gurddy is a lightweight Python package designed to model and solve Constraint Satisfaction Problems (CSP) and Linear Programming (LP) problems with ease. Built for researchers, engineers, and optimization enthusiasts, Gurddy provides a unified interface to define variables, constraints, and objectives—then leverages powerful solvers under the hood to deliver optimal or feasible solutions.

Features
- 🧩 CSP Support: Define discrete variables, domains, and logical constraints.
- 📈 LP Support: Formulate linear objectives and inequality/equality constraints.
- 🔌 Extensible Solver Backend: Integrates with industry-standard solvers (e.g., Gurobi, CBC, or GLPK via compatible interfaces).
- 📦 Simple API: Intuitive syntax for rapid prototyping and experimentation.
- 🧪 Type-Hinted & Tested: Robust codebase with unit tests and clear documentation.


Installation (PyPI)
-------------------

Install the package from PyPI:

```powershell
pip install gurddy
```

For LP/MIP examples you also need PuLP (the LP backend used by the built-in `LPSolver`):

```powershell
pip install pulp
```

If you publish optional extras you may use something like `pip install gurddy[lp]` if configured; otherwise install `pulp` separately as shown above.


Usage — Core concepts
---------------------

After installing from PyPI you can import the public API from the `gurddy` package. The library exposes a small Model/Variable/Constraint API used by both CSP and LP solvers.

- Model: container for variables, constraints, and objective. Use `Model(...)` and then `addVar`, `addConstraint`, `setObjective` or call `solve()` which will dispatch to the appropriate solver based on `problem_type`.
- Variable: create with `Model.addVar(name, low_bound=None, up_bound=None, cat='Continuous', domain=None)`; for CSP use `domain` (tuple of ints), for LP use numeric bounds and category ('Continuous', 'Integer', 'Binary').
- Expression: arithmetic expressions are created implicitly by operations on `Variable` objects or explicitly via `Expression(variable_or_value)`.
- Constraint types: `LinearConstraint`, `AllDifferentConstraint`, `FunctionConstraint`.

Usage — CSP (example)
---------------------

Simple CSP example (map to `CSPSolver`):

```python
from gurddy.model import Model
from gurddy.variable import Expression
from gurddy.constraint import AllDifferentConstraint

# Build CSP model
model = Model('sudoku', problem_type='CSP')
# Add discrete variables with domains (1..9)
model.addVar('A1', domain=[1,2,3,4,5,6,7,8,9])
model.addVar('A2', domain=[1,2,3,4,5,6,7,8,9])

# Add AllDifferent constraint across a group
model.addConstraint(AllDifferentConstraint([model.variables['A1'], model.variables['A2']]))

# Solve (uses internal CSPSolver)
solution = model.solve()
print(solution)  # dict of variable name -> assigned int, or None if unsatisfiable
```

Notes about CSP API
- CSPSolver automatically builds an internal graph of constraints and will attempt mask-based optimizations when domains are small contiguous integer sets (e.g., Sudoku 1..9).
- You can force the mask-optimized path by setting `solver.force_mask = True` after creating the solver (if you instantiate `CSPSolver` directly).

Usage — LP / MIP (example)
--------------------------

The LP solver wraps PuLP. A basic LP/MIP example:

```python
from gurddy.model import Model

# Build an LP model
m = Model('demo', problem_type='LP')
# addVar(name, low_bound=None, up_bound=None, cat='Continuous')
x = m.addVar('x', low_bound=0, cat='Continuous')
y = m.addVar('y', low_bound=0, cat='Integer')

# Objective: maximize 3*x + 5*y
m.setObjective(x * 3 + y * 5, sense='Maximize')

# Add linear constraints (using Expression objects implicitly via Variable operations)
m.addConstraint((x * 2 + y * 1) <= 10)

# Solve (uses LPSolver which wraps PuLP)
sol = m.solve()
print(sol)  # dict var name -> numeric value or None
```

Advanced LP demo
----------------
See `examples/optimized_lp.py` (simple demo) and `examples/advanced_lp.py` (LP relaxation vs MIP, timings, simple sensitivity analysis).

Developer notes
---------------
- The CSP code includes several internal optimizations: precomputed support masks, mask-based AC-3, and an optional AllDifferent matching propagation for small groups to strengthen pruning.
- The LP solver uses PuLP. If you want to use another solver backend (ORTOOLS, Gurobi), you can either modify `src/gurddy/solver/lp_solver.py` to wrap that backend or add a new solver class and dispatch via `Model.solve()`.

Running tests
-------------
Run unit tests with pytest:

```powershell
python -m pytest
```

Contributing
------------
PRs welcome. If you add a new solver backend, please include configuration and a small example demonstrating usage.

API Reference (concise)
-----------------------

This section lists the most commonly used classes and functions with signatures and short descriptions.

Model
- - -
- Model(name: str = "Model", problem_type: str = "LP")
	- Container for variables, constraints, objective and solver selection.
	- Attributes: variables: Dict[str, Variable], constraints: List[Constraint], objective: Optional[Expression], sense: str

- addVar(name: str, low_bound: Optional[float] = None, up_bound: Optional[float] = None,
				 cat: str = 'Continuous', domain: Optional[list] = None) -> Variable
	- Create and register a Variable. For CSP use `domain` (list/tuple of ints). For LP use numeric bounds and `cat`.

- addVars(names: List[str], **kwargs) -> Dict[str, Variable]
	- Convenience to create multiple variables with the same kwargs.

- addConstraint(constraint: Constraint, name: Optional[str] = None) -> None
	- Register a Constraint object (LinearConstraint, AllDifferentConstraint, FunctionConstraint).

- setObjective(expr: Expression, sense: str = "Maximize") -> None
	- Set the objective expression and sense for LP problems.

- solve() -> Optional[Dict[str, Union[int, float]]]
	- Dispatch to the appropriate solver (CSPSolver or LPSolver) and return a mapping from variable name to value, or None if unsatisfiable/no optimal found.

Variable
- - -
- Variable(name: str, low_bound: Optional[float] = None, up_bound: Optional[float] = None,
					 cat: str = 'Continuous', domain: Optional[list] = None)
	- Represents a decision variable. For CSP set `domain` (discrete values). For LP set numeric bounds and `cat` in {'Continuous','Integer','Binary'}.
	- Supports arithmetic operator overloads to build `Expression` objects (e.g., `x * 3 + y`).

Expression
- - -
- Expression(term: Union[Variable, int, float, Expression])
	- Arithmetic expression type used to build linear objectives and constraints.
	- Operators: +, -, *, / with scalars; comparisons (==, <=, >=, <, >) produce `LinearConstraint` instances.

Constraint types
- - -
- LinearConstraint(expr: Expression, sense: str)
	- General linear constraint wrapper (sense in {'<=','>=','==', '!='}).

- AllDifferentConstraint(vars: List[Variable])
	- Global constraint enforcing all variables in the list take pairwise distinct values (used primarily for CSPs).

- FunctionConstraint(func: Callable[[int,int], bool], vars: Tuple[Variable, ...])
	- Custom binary (or n-ary) constraint defined by a Python callable.

Solvers
- - -
- class CSPSolver
	- CSPSolver(model: Model)
	- Attributes: mask_threshold: int (domain size under which mask optimization is used), force_mask: bool
	- Methods: solve() -> Optional[Dict[str, int]]  (returns assignment mapping or None)

- class LPSolver
	- LPSolver(model: Model)
	- Methods: solve() -> Optional[Dict[str, float]]  (returns variable values mapping or None). Uses PuLP by default; requires `pulp` installed.

Notes
- The API intentionally keeps model construction separate from solver execution. Use `Model.solve()` for convenience or instantiate solver classes directly for advanced control (e.g., change `CSPSolver.force_mask`).
- For more examples see `examples/optimized_csp.py`, `examples/optimized_lp.py`, and `examples/advanced_lp.py`.

