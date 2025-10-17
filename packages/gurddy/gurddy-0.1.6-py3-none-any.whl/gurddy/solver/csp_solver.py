# gurddy/solver/csp_solver.py
from dataclasses import dataclass
from collections import deque
from functools import lru_cache
from typing import Dict, Tuple, Callable, List, Sequence, Optional, Set

# Small precomputed table for masks up to 32 bits to avoid repeated bit scanning in hot loops.
# We'll populate entries lazily on first use.
_MASK_TO_VALUES_TABLE: Dict[int, tuple] = {}
from ..model import Model
from ..constraint import AllDifferentConstraint, FunctionConstraint, LinearConstraint

# ----------------- bitmask helpers (for small integer domains like Sudoku 1..9) -----------------

def values_to_mask(values: Sequence[int]) -> int:
    """Convert iterable of 1-based small integers (1..N) to bitmask (bit 0 -> value 1)."""
    mask = 0
    for v in values:
        if v is None:
            continue
        mask |= 1 << (int(v) - 1)
    return mask

@lru_cache(maxsize=None)
def mask_to_values(mask: int) -> tuple:
    # Return a tuple of values (1-based) present in mask. Cached for repeated use.
    vals = []
    v = 1
    m = mask
    while m:
        if m & 1:
            vals.append(v)
        m >>= 1
        v += 1
    return tuple(vals)

def mask_to_values_cached(mask: int) -> tuple:
    # Fast path: check small table
    t = _MASK_TO_VALUES_TABLE.get(mask)
    if t is not None:
        return t
    t = mask_to_values(mask)
    _MASK_TO_VALUES_TABLE[mask] = t
    return t

def mask_count(mask: int) -> int:
    return mask.bit_count()

def mask_contains(mask: int, value: int) -> bool:
    return bool(mask & (1 << (int(value) - 1)))

def mask_remove(mask: int, value: int) -> int:
    return mask & ~(1 << (int(value) - 1))

# -----------------------------------------------------------------------------------------------

# ---------- 约束函数 ----------
def not_equal(a: int, b: int) -> bool:
    return a != b

# ---------- 数据容器（不可变域） ----------
@dataclass(frozen=True)
class CSPState:
    variables: Tuple[str, ...]
    constraints: Dict[Tuple[str, str], Callable[[int, int], bool]]
    neighbors: Dict[str, Tuple[str, ...]]
    arcs: Tuple[Tuple[str, str], ...]
    support_masks: Optional[Dict[Tuple[str, str], List[int]]] = None
    all_different: Optional[List[Tuple[str, ...]]] = None


# ---------- 域操作（返回新副本） ----------
def set_domain(domains: Dict[str, Tuple[int, ...]], var: str, values: Sequence[int]) -> Dict[str, Tuple[int, ...]]:
    """返回一个新 domains 字典，其中 var 的域被替换为 values（元组形式）。"""
    new = dict(domains)
    new[var] = tuple(values)
    return new

def remove_value(domains: Dict[str, Tuple[int, ...]], var: str, value: int) -> Tuple[Dict[str, Tuple[int, ...]], bool]:
    """从 var 的域中移除 value，返回 (new_domains, removed_flag)。"""
    current = domains[var]
    if value in current:
        new_vals = tuple(x for x in current if x != value)
        new = dict(domains)
        new[var] = new_vals
        return new, True
    return domains, False

# ---------- 一致性检查（对 assignment） ----------
def is_consistent_with_assignment(state: CSPState, domains: Dict[str, Tuple[int, ...]],
                                  var: str, value: int, assignment: Dict[str, int]) -> bool:
    """检查把 var=value 加入 assignment 后是否与已赋值变量一致（局部一致）。"""
    for oth, oth_val in assignment.items():
        # 检查是否存在约束 (var, oth)
        if (var, oth) in state.constraints:
            if not state.constraints[(var, oth)](value, oth_val):
                return False
        # 同时也可能约束以相反顺序定义
        if (oth, var) in state.constraints:
            if not state.constraints[(oth, var)](oth_val, value):
                return False
    return True

# ---------- revise（纯函数版） ----------
def revise(state: CSPState, domains: Dict[str, Tuple[int, ...]],
           xi: str, xj: str) -> Tuple[Dict[str, Tuple[int, ...]], bool, List[Tuple[str, int]]]:
    """
    如果 xj 的域是单值 v，而 xi 的域包含 v，则从 xi 的域中移除 v。
    返回 (new_domains, revised_flag, removals_list) 其中 removals_list 列出被移除的 (var, val)。
    （这个实现保留了你原来基于“邻居是单值时移除相同值”的简化策略）
    """
    removals: List[Tuple[str, int]] = []
    constraint = state.constraints.get((xi, xj))
    if constraint is None:
        # 没有约束或约束方向与这个调用无关 —— 不做任何修改
        return domains, False, removals

    domain_xj = domains[xj]
    if len(domain_xj) == 1:
        vj = domain_xj[0]
        if vj in domains[xi]:
            new_domains, removed = remove_value(domains, xi, vj)
            if removed:
                removals.append((xi, vj))
                return new_domains, True, removals
    return domains, False, removals


def revise_mask(state: CSPState, domains_mask: Dict[str, int], xi: str, xj: str) -> Tuple[Dict[str, int], bool, List[Tuple[str, int]]]:
    """Mask-based revise: remove values in Xi that have no supporting value in Xj."""
    removals: List[Tuple[str, int]] = []
    # Prefer precomputed support masks when available to avoid inner loops
    if state.support_masks and (xi, xj) in state.support_masks:
        domain_xi = domains_mask[xi]
        domain_xj = domains_mask[xj]
        new_mask = domain_xi
        support_list = state.support_masks[(xi, xj)]  # index by value (1-based)
        # iterate bits in domain_xi
        for val in mask_to_values_cached(domain_xi):
            support_mask = support_list[val] if val < len(support_list) else 0
            if support_mask & domain_xj == 0:
                new_mask = mask_remove(new_mask, val)
                removals.append((xi, val))
        if new_mask != domain_xi:
            new_domains = dict(domains_mask)
            new_domains[xi] = new_mask
            return new_domains, True, removals
        return domains_mask, False, removals

    # Fallback: compute supports on the fly
    constraint = state.constraints.get((xi, xj))
    if constraint is None:
        return domains_mask, False, removals

    domain_xi = domains_mask[xi]
    domain_xj = domains_mask[xj]
    new_mask = domain_xi
    # iterate bits of domain_xi directly to avoid mask_to_values call
    m = domain_xi
    val = 1
    while m:
        if m & 1:
            # check support in domain_xj by scanning bits
            supported = False
            my = domain_xj
            y = 1
            while my:
                if my & 1:
                    if constraint(val, y):
                        supported = True
                        break
                my >>= 1
                y += 1
            if not supported:
                new_mask = mask_remove(new_mask, val)
                removals.append((xi, val))
        m >>= 1
        val += 1
    if new_mask != domain_xi:
        new_domains = dict(domains_mask)
        new_domains[xi] = new_mask
        return new_domains, True, removals
    return domains_mask, False, removals

# ---------- AC-3（纯函数式：接受 domains，返回 (domains, success, removals)） ----------
def ac3(state: CSPState, domains: Dict[str, Tuple[int, ...]],
        arcs: Optional[Sequence[Tuple[str, str]]] = None) -> Tuple[Dict[str, Tuple[int, ...]], bool, List[Tuple[str, int]]]:
    """
    执行 AC-3。arcs 可选（默认使用 state.arcs）。
    返回 (new_domains, success_flag, all_removals)
    """
    if arcs is None:
        queue = deque(state.arcs)
    else:
        queue = deque(arcs)

    current_domains = dict(domains)
    all_removals: List[Tuple[str, int]] = []

    while queue:
        xi, xj = queue.popleft()
        current_domains, revised, removals = revise(state, current_domains, xi, xj)
        if revised:
            all_removals.extend(removals)
            if not current_domains[xi]:
                # xi 域为空 => 失败
                return current_domains, False, all_removals
            # 把 xi 的其他邻居加入队列
            for xk in state.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    return current_domains, True, all_removals


def ac3_mask(state: CSPState, domains_mask: Dict[str, int],
             arcs: Optional[Sequence[Tuple[str, str]]] = None) -> Tuple[Dict[str, int], bool, List[Tuple[str, int]]]:
    if arcs is None:
        queue = deque(state.arcs)
    else:
        queue = deque(arcs)

    current_domains = dict(domains_mask)
    all_removals: List[Tuple[str, int]] = []

    while queue:
        xi, xj = queue.popleft()
        current_domains, revised, removals = revise_mask(state, current_domains, xi, xj)
        if revised:
            all_removals.extend(removals)
            if current_domains[xi] == 0:
                return current_domains, False, all_removals
            for xk in state.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    return current_domains, True, all_removals


def revise_mask_inplace(state: CSPState, domains_mask: Dict[str, int], xi: str, xj: str, removals: List[Tuple[str, int]]) -> bool:
    """In-place revise: modify domains_mask and append removals; return True if revised."""
    if state.support_masks and (xi, xj) in state.support_masks:
        domain_xi = domains_mask[xi]
        domain_xj = domains_mask[xj]
        new_mask = domain_xi
        support_list = state.support_masks[(xi, xj)]
        for val in mask_to_values_cached(domain_xi):
            support_mask = support_list[val] if val < len(support_list) else 0
            if support_mask & domain_xj == 0:
                new_mask = mask_remove(new_mask, val)
                removals.append((xi, val))
        if new_mask != domain_xi:
            domains_mask[xi] = new_mask
            return True
        return False

    constraint = state.constraints.get((xi, xj))
    if constraint is None:
        return False

    domain_xi = domains_mask[xi]
    domain_xj = domains_mask[xj]
    new_mask = domain_xi
    for val in mask_to_values(domain_xi):
        supported = False
        for y in mask_to_values(domain_xj):
            if constraint(val, y):
                supported = True
                break
        if not supported:
            new_mask = mask_remove(new_mask, val)
            removals.append((xi, val))
    if new_mask != domain_xi:
        domains_mask[xi] = new_mask
        return True
    return False


def ac3_mask_inplace(state: CSPState, domains_mask: Dict[str, int], arcs: Optional[Sequence[Tuple[str, str]]] = None, removals_out: Optional[List[Tuple[str, int]]] = None) -> bool:
    if arcs is None:
        queue = deque(state.arcs)
    else:
        queue = deque(arcs)

    local_removals: List[Tuple[str, int]] = []
    while queue:
        xi, xj = queue.popleft()
        revised = revise_mask_inplace(state, domains_mask, xi, xj, local_removals)
        if revised:
            if domains_mask[xi] == 0:
                if removals_out is not None:
                    removals_out.extend(local_removals)
                return False
            for xk in state.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
        # After processing this arc, attempt AllDifferent propagation for any groups present
        if state.all_different:
            for group in state.all_different:
                # Conservative thresholds: skip large groups or many distinct values
                if len(group) > 6:
                    continue
                distinct_vals = 0
                # count distinct values conservatively by unioning small masks
                union_mask = 0
                for v in group:
                    union_mask |= domains_mask[v]
                distinct_vals = mask_count(union_mask)
                if distinct_vals > 12:
                    continue
                changed = alldiff_propagate_mask(state, domains_mask, group, local_removals)
                if changed:
                    # if any domain becomes empty, fail early
                    for v in group:
                        if domains_mask[v] == 0:
                            if removals_out is not None:
                                removals_out.extend(local_removals)
                            return False
                    # enqueue neighbors of changed variables
                    for v in group:
                        for nb in state.neighbors[v]:
                            queue.append((nb, v))
    if removals_out is not None:
        removals_out.extend(local_removals)
    return True


def alldiff_propagate_mask(state: CSPState, domains_mask: Dict[str, int], group: Tuple[str, ...], removals: List[Tuple[str, int]]) -> bool:
    """Apply AllDifferent propagation on bitmask domains by converting to temporary lists,
    reusing the list-based propagation, and reflecting removals back to masks.
    Returns True if any domain was reduced.
    """
    # Build temporary list-based domains for the group
    temp_domains: Dict[str, List[int]] = {v: list(mask_to_values_cached(domains_mask[v])) for v in group}
    temp_removals: List[Tuple[str, int]] = []
    changed = alldiff_propagate_list(state, temp_domains, group, temp_removals)
    if not changed:
        return False

    # Reflect removals into domains_mask and append to removals list
    for (var, val) in temp_removals:
        # compute bit and remove
        if mask_contains(domains_mask[var], val):
            domains_mask[var] = mask_remove(domains_mask[var], val)
            removals.append((var, val))
    return True


def select_unassigned_variable_mask(state: CSPState, domains_mask: Dict[str, int], assignment: Dict[str, int]) -> str:
    # Use a generator to avoid building an intermediate list
    unassigned = (v for v in state.variables if v not in assignment)
    return min(unassigned, key=lambda v: mask_count(domains_mask[v]))


def order_domain_values_mask(state: CSPState, domains_mask: Dict[str, int], var: str, assignment: Dict[str, int]) -> List[int]:
    if mask_count(domains_mask[var]) == 1:
        return mask_to_values(domains_mask[var])

    def conflict_count(value: int) -> int:
        count = 0
        for neigh in state.neighbors[var]:
            if neigh not in assignment:
                if mask_contains(domains_mask[neigh], value):
                    count += 1
        return count

    return sorted(mask_to_values(domains_mask[var]), key=conflict_count)


def backtrack_mask(state: CSPState, domains_mask: Dict[str, int], assignment: Dict[str, int]) -> Optional[Dict[str, int]]:
    if len(assignment) == len(state.variables):
        return dict(assignment)

    var = select_unassigned_variable_mask(state, domains_mask, assignment)

    for value in order_domain_values_mask(state, domains_mask, var, assignment):
        # check consistency
        consistent = True
        for oth, oth_val in assignment.items():
            if (var, oth) in state.constraints and not state.constraints[(var, oth)](value, oth_val):
                consistent = False
                break
            if (oth, var) in state.constraints and not state.constraints[(oth, var)](oth_val, value):
                consistent = False
                break
        if not consistent:
            continue

        # assign
        assignment[var] = value
        # record changes to restore later
        removed_vals: List[Tuple[str, int]] = []
        # set var to single value in-place
        prev_mask = domains_mask[var]
        domains_mask[var] = 1 << (value - 1)

        # prepare inference arcs
        # Only need to enqueue arcs (neigh, var) because var's domain became a single value;
        # neighbors need to be revised against var. Enqueueing both directions is redundant and
        # increases queue size and revise calls.
        inference_arcs = [(neigh, var) for neigh in state.neighbors[var]]

        success = ac3_mask_inplace(state, domains_mask, inference_arcs, removals_out=removed_vals)
        if success:
            result = backtrack_mask(state, domains_mask, assignment)
            if result is not None:
                return result

        # restore state
        domains_mask[var] = prev_mask
        for (v, val) in removed_vals:
            domains_mask[v] |= 1 << (val - 1)
        del assignment[var]

    return None

# ---------- 选择变量与域值排序（MRV 与 least-constraining-value 的简单组合） ----------
def select_unassigned_variable(state: CSPState, domains: Dict[str, Tuple[int, ...]],
                               assignment: Dict[str, int]) -> str:
    # MRV：选择域最小的变量。使用生成器避免中间列表分配。
    unassigned = (v for v in state.variables if v not in assignment)
    return min(unassigned, key=lambda v: len(domains[v]))

def order_domain_values(state: CSPState, domains: Dict[str, Tuple[int, ...]],
                        var: str, assignment: Dict[str, int]) -> List[int]:
    """对候选值排序：优先那些对未赋值邻居冲突最少的值（简单启发式）。"""
    if len(domains[var]) == 1:
        return list(domains[var])

    def conflict_count(value: int) -> int:
        count = 0
        for neigh in state.neighbors[var]:
            if neigh not in assignment:
                # 计算邻居当前域中是否包含该值（越多表示越冲突）
                if value in domains[neigh]:
                    count += 1
        return count

    return sorted(domains[var], key=conflict_count)

# ---------- 回溯搜索（纯函数式实现） ----------
def backtrack(state: CSPState, domains: Dict[str, Tuple[int, ...]],
              assignment: Dict[str, int]) -> Optional[Dict[str, int]]:
    """
    纯函数式回溯：传入当前 domains 和 assignment，返回完整 assignment 或 None。
    每次尝试分配都会产生新的 domains（不修改父 domains）。
    """
    # 完成条件
    if len(assignment) == len(state.variables):
        return dict(assignment)

    var = select_unassigned_variable(state, domains, assignment)
    for value in order_domain_values(state, domains, var, assignment):
        if is_consistent_with_assignment(state, domains, var, value, assignment):
            # 试探性分配：创建新的 assignment 和 domains
            new_assignment = dict(assignment)
            new_assignment[var] = value
            new_domains = set_domain(domains, var, (value,))

            # 构造推理用的弧：所有与 var 相连的有向弧
            # Only need to enqueue (neigh, var) when var is fixed to a single value.
            inference_arcs = [(neigh, var) for neigh in state.neighbors[var]]

            # 执行 AC-3 推理
            new_domains_after_ac3, success, removals = ac3(state, new_domains, inference_arcs)
            if success:
                result = backtrack(state, new_domains_after_ac3, new_assignment)
                if result is not None:
                    return result
            # 若失败则回溯（由于我们使用不可变副本，直接丢弃 new_domains 即可）
    return None

class CSPSolver:
    def __init__(self, model: Model):
        self.model = model
        # mask_threshold can be tuned; default 32
        self.mask_threshold = 32
        # allow forcing mask-optimized path (useful for benchmarking/experiments)
        self.force_mask = False
        self.state, self.domains, self.domains_mask = self._build_csp_state()

    def _build_csp_state(self):
        variables = tuple(self.model.variables.keys())
        domains: Dict[str, Tuple[int, ...]] = {name: var.domain for name, var in self.model.variables.items() if var.domain}

        # Handle equality constraints for fixed values (e.g., var == constant)
        for constr in self.model.constraints:
            if isinstance(constr, LinearConstraint):
                if constr.sense == '==':
                    terms = constr.expr.terms
                    if len(terms) == 1:
                        var = list(terms.keys())[0]
                        coeff = list(terms.values())[0]
                        if coeff == 1.0 and constr.expr.constant < 0:  # constant is -value
                            value = -constr.expr.constant
                            if value.is_integer():
                                domains[var.name] = (int(value),)

        constraints: Dict[Tuple[str, str], Callable[[int, int], bool]] = {}
        all_different_groups: List[Tuple[str, ...]] = []
        for constr in self.model.constraints:
            if isinstance(constr, AllDifferentConstraint):
                vars = [v.name for v in constr.vars]
                all_different_groups.append(tuple(vars))
                for i in range(len(vars)):
                    for j in range(i + 1, len(vars)):
                        v1, v2 = vars[i], vars[j]
                        constraints[(v1, v2)] = not_equal
                        constraints[(v2, v1)] = not_equal
            elif isinstance(constr, FunctionConstraint):
                # For pairwise, assume func is binary
                if len(constr.vars) == 2:
                    v1, v2 = constr.vars[0].name, constr.vars[1].name
                    constraints[(v1, v2)] = constr.func
                    # For symmetric constraints, both directions should use the same function
                    constraints[(v2, v1)] = constr.func
            # Skip handled LinearConstraint equalities

        # 邻居（无序去重、元组）
        neighbors: Dict[str, Tuple[str, ...]] = {v: tuple() for v in variables}
        neigh_sets: Dict[str, Set[str]] = {v: set() for v in variables}
        for (a, b) in constraints.keys():
            neigh_sets[a].add(b)
        for v in variables:
            neighbors[v] = tuple(sorted(neigh_sets[v]))

        arcs = tuple(constraints.keys())
        # Attempt to build support_masks when domains are small contiguous integer ranges (1..N)
        support_masks: Optional[Dict[Tuple[str, str], List[int]]] = None
        # Determine if domains are integer small ranges
        all_int_domains = True
        max_val = 0
        domains_mask: Dict[str, int] = {}
        for name, dom in domains.items():
            if not dom:
                all_int_domains = False
                break
            try:
                vals = [int(x) for x in dom]
            except Exception:
                all_int_domains = False
                break
            # allow domains that are subsets of 1..max_val (e.g., singleton 5)
            if any(v < 1 for v in vals):
                all_int_domains = False
                break
            max_val = max(max_val, max(vals))
            domains_mask[name] = values_to_mask(vals)

        if all_int_domains and max_val <= 32:
            support_masks = {}
            # For each directed constraint, precompute for each possible value v the support mask in xj
            # Precompute a mask of allowed y values per variable to avoid rebuilding lists
            domain_allowed_mask = {name: domains_mask[name] for name in domains_mask}
            for (xi, xj), func in constraints.items():
                # support list indexed by value (we'll make it length max_val+1, ignore index 0)
                supp_list = [0] * (max_val + 1)
                allowed_mask_xj = domain_allowed_mask.get(xj, 0)
                if func is not None and func == not_equal:
                    # Special-case AllDifferent / not_equal: support for v is allowed_mask_xj without v
                    for v in range(1, max_val + 1):
                        supp_list[v] = allowed_mask_xj & ~(1 << (v - 1))
                else:
                    # Generic case: iterate bits in allowed_mask_xj directly to avoid mask_to_values
                    for v in range(1, max_val + 1):
                        mask = 0
                        m = allowed_mask_xj
                        y = 1
                        while m:
                            if m & 1:
                                try:
                                    if func(v, y):
                                        mask |= 1 << (y - 1)
                                except Exception:
                                    pass
                            m >>= 1
                            y += 1
                        supp_list[v] = mask
                support_masks[(xi, xj)] = supp_list

        # 构造最终的不可变 CSPState（包括可能的 AllDifferent 组）
        state = CSPState(
            variables=variables,
            constraints=constraints,
            neighbors=neighbors,
            arcs=arcs,
            support_masks=support_masks,
            all_different=all_different_groups,
        )

        # 仅在构建了 mask 优化时返回 domains_mask
        if all_int_domains and max_val <= 32:
            return state, domains, domains_mask
        return state, domains, None

    def solve(self) -> Optional[Dict[str, int]]:
        # If domains are small contiguous ranges starting at 1 (e.g., Sudoku 1..9),
        # use mask-optimized path.
        can_use_mask = True
        max_val = 0
        for name, dom in self.domains.items():
            if not dom:
                can_use_mask = False
                break
            # check dom values are ints and within 1..32
            try:
                vals = [int(x) for x in dom]
            except Exception:
                can_use_mask = False
                break
            if not vals:
                can_use_mask = False
                break
            minv, maxv = min(vals), max(vals)
            if minv != 1 or maxv > 32:
                can_use_mask = False
                break
            max_val = max(max_val, maxv)

        # If caller explicitly requested mask path, use it when domains_mask is available.
        if getattr(self, 'force_mask', False) and self.domains_mask is not None:
            domains_mask: Dict[str, int] = self.domains_mask
            domains_after_ac3, ok, _ = ac3_mask(self.state, domains_mask)
            if not ok:
                return None
            return backtrack_mask(self.state, domains_after_ac3, {})

        if can_use_mask and max_val <= 32 and self.domains_mask is not None:
            # use the precomputed domains_mask if available
            domains_mask: Dict[str, int] = self.domains_mask if self.domains_mask is not None else {name: values_to_mask(dom) for name, dom in self.domains.items()}
            domains_after_ac3, ok, _ = ac3_mask(self.state, domains_mask)
            if not ok:
                return None
            return backtrack_mask(self.state, domains_after_ac3, {})

        # fallback to tuple-based implementation
        # Use an in-place tuple-list based AC-3/backtrack to avoid copying domains dicts repeatedly.
        # Convert tuple domains to lists for in-place modification and restore behavior via removals.
        domains_lists: Dict[str, List[int]] = {name: list(dom) for name, dom in self.domains.items()}
        ok = ac3_inplace(self.state, domains_lists)
        if not ok:
            return None
        return backtrack_inplace(self.state, domains_lists, {})


def revise_inplace(state: CSPState, domains_lists: Dict[str, List[int]], xi: str, xj: str, removals: List[Tuple[str, int]]) -> bool:
    """In-place revise for tuple/list domains. Remove unsupported values from xi when xj is singleton."""
    constraint = state.constraints.get((xi, xj))
    if constraint is None:
        return False
    domain_xj = domains_lists[xj]
    if len(domain_xj) != 1:
        return False
    vj = domain_xj[0]
    domain_xi = domains_lists[xi]
    if vj in domain_xi:
        domain_xi.remove(vj)
        removals.append((xi, vj))
        return True
    return False


def ac3_inplace(state: CSPState, domains_lists: Dict[str, List[int]], arcs: Optional[Sequence[Tuple[str, str]]] = None, removals_out: Optional[List[Tuple[str, int]]] = None) -> bool:
    if arcs is None:
        queue = deque(state.arcs)
    else:
        queue = deque(arcs)

    local_removals: List[Tuple[str, int]] = []
    while queue:
        xi, xj = queue.popleft()
        revised = revise_inplace(state, domains_lists, xi, xj, local_removals)
        if revised:
            if not domains_lists[xi]:
                if removals_out is not None:
                    removals_out.extend(local_removals)
                return False
            for xk in state.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
        # After processing this arc, attempt AllDifferent propagation for any groups present
        if state.all_different:
            for group in state.all_different:
                # Conservative heuristics to avoid expensive matching on large groups or many values.
                # Only run propagation when group size and total distinct values are small.
                if len(group) > 6:
                    continue
                distinct_vals = set()
                for v in group:
                    distinct_vals.update(domains_lists[v])
                if len(distinct_vals) > 12:
                    continue
                # only consider group if at least two vars still have domain > 1
                active = [v for v in group if len(domains_lists[v]) > 1]
                if len(active) < 2:
                    continue
                changed = alldiff_propagate_list(state, domains_lists, group, local_removals)
                if changed:
                    # if any domain becomes empty, fail early
                    for v in group:
                        if not domains_lists[v]:
                            if removals_out is not None:
                                removals_out.extend(local_removals)
                            return False
                    # enqueue neighbors of changed variables
                    for v in group:
                        for nb in state.neighbors[v]:
                            queue.append((nb, v))
    if removals_out is not None:
        removals_out.extend(local_removals)
    return True


def alldiff_propagate_list(state: CSPState, domains_lists: Dict[str, List[int]], group: Tuple[str, ...], removals: List[Tuple[str, int]]) -> bool:
    """Apply a simple Régin-like propagation on a list-based domains representation.
    Returns True if any domain was reduced.
    This implementation builds a bipartite graph vars->values and computes a maximum matching using DFS augmenting paths.
    It then removes values that cannot belong to any maximum matching for their variable.
    """
    # Build set of values present in group domains
    vals = set()
    for v in group:
        vals.update(domains_lists[v])
    if not vals:
        return False
    vals_list = sorted(vals)
    val_index = {val: i for i, val in enumerate(vals_list)}

    # adjacency: var_idx -> list of val_idx
    var_idx = {v: i for i, v in enumerate(group)}
    adj = [[] for _ in group]
    for v in group:
        i = var_idx[v]
        for val in domains_lists[v]:
            adj[i].append(val_index[val])

    # matching arrays: match_val[val_idx] = var_idx or -1; match_var[var_idx] = val_idx or -1
    m = len(vals_list)
    n = len(group)
    match_val = [-1] * m
    match_var = [-1] * n

    def dfs_aug(u: int, seen: List[bool]) -> bool:
        for w in adj[u]:
            if seen[w]:
                continue
            seen[w] = True
            if match_val[w] == -1 or dfs_aug(match_val[w], seen):
                match_val[w] = u
                match_var[u] = w
                return True
        return False

    # Greedy initial matching
    for u in range(n):
        for w in adj[u]:
            if match_val[w] == -1:
                match_val[w] = u
                match_var[u] = w
                break

    # Augment to maximum matching
    for u in range(n):
        if match_var[u] == -1:
            seen = [False] * m
            dfs_aug(u, seen)

    # If not perfect matching (size < number of variables with domain>0), we cannot fully satisfy AllDifferent now,
    # but we can still try to prune values that are not part of any alternating path leading to an augmenting solution for a variable.
    changed = False

    # For each variable, compute values that appear in some alternating tree rooted at unmatched variables
    # Simpler (but conservative) approach: for each var and each value in its domain, test whether there exists a matching that assigns that value to var by
    # temporarily forcing that assignment and attempting to find match for remaining vars.
    for u, var in enumerate(group):
        cur_domain = list(domains_lists[var])
        to_remove = []
        for val in cur_domain:
            # try to enforce var->val
            forced_w = val_index[val]
            # copy matching
            mv = match_val[:]
            mv_forced = mv[:]
            mv_forced[forced_w] = u
            # build match_var copy
            mv_var = match_var[:]
            mv_var[u] = forced_w

            # attempt to rematch other variables (excluding u)
            ok = True
            # create local match_val and match_var for augmentation
            local_match_val = mv_forced[:]
            local_match_var = mv_var[:]
            for uu in range(n):
                if uu == u:
                    continue
                if local_match_var[uu] != -1:
                    continue
                seen = [False] * m
                def dfs_local(x: int) -> bool:
                    for w in adj[x]:
                        if seen[w]:
                            continue
                        seen[w] = True
                        if local_match_val[w] == -1 or dfs_local(local_match_val[w]):
                            local_match_val[w] = x
                            local_match_var[x] = w
                            return True
                    return False
                if not dfs_local(uu):
                    ok = False
                    break

            if not ok:
                to_remove.append(val)

        if to_remove:
            for val in to_remove:
                if val in domains_lists[var]:
                    domains_lists[var].remove(val)
                    removals.append((var, val))
                    changed = True

    return changed


def backtrack_inplace(state: CSPState, domains_lists: Dict[str, List[int]], assignment: Dict[str, int]) -> Optional[Dict[str, int]]:
    if len(assignment) == len(state.variables):
        return dict(assignment)

    # MRV on current lists
    unassigned = (v for v in state.variables if v not in assignment)
    var = min(unassigned, key=lambda v: len(domains_lists[v]))

    # order domain values by least constraining heuristic
    vals = domains_lists[var][:]
    def conflict_count(value: int) -> int:
        count = 0
        for neigh in state.neighbors[var]:
            if neigh not in assignment and value in domains_lists[neigh]:
                count += 1
        return count
    for value in sorted(vals, key=conflict_count):
        # consistency check with current assignment
        ok = True
        for oth, oth_val in assignment.items():
            if (var, oth) in state.constraints and not state.constraints[(var, oth)](value, oth_val):
                ok = False
                break
            if (oth, var) in state.constraints and not state.constraints[(oth, var)](oth_val, value):
                ok = False
                break
        if not ok:
            continue

        # assign and record changes
        assignment[var] = value
        prev_list = domains_lists[var][:]
        domains_lists[var] = [value]
        removed_vals: List[Tuple[str, int]] = []

        # prepare inference arcs (only neighbors -> var)
        inference_arcs = [(neigh, var) for neigh in state.neighbors[var]]
        success = ac3_inplace(state, domains_lists, inference_arcs, removals_out=removed_vals)
        if success:
            result = backtrack_inplace(state, domains_lists, assignment)
            if result is not None:
                return result

        # restore
        domains_lists[var] = prev_list
        for (v, val) in removed_vals:
            if val not in domains_lists[v]:
                domains_lists[v].append(val)
        del assignment[var]

    return None