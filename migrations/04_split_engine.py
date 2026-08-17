"""One-off migration: decompose engine/simulate.py's single run_simulation() function
into a Simulation class with state as explicit self.X attributes, methods distributed
across engine/{state,resolve,priority,randomness,events,run}.py.

Safety approach: every nested function inside the original run_simulation() is a Python
closure, and Python's own compiler records exactly which outer-scope names each one
reads/writes as that function code object's `co_freevars` -- this is authoritative
(computed by CPython's real scoping rules), not a guess. This script:
  1. Imports the CURRENT (already-lifted, already-verified) simulate.py and asks each
     nested function object for its co_freevars.
  2. Parses simulate.py's source with `ast`, extracts every nested FunctionDef (however
     deeply nested), and for each one, adds `self` as the first parameter and rewrites
     every bare `ast.Name` reference matching that function's own co_freevars into
     `self.<name>` (an ast.Attribute) -- never touching already-qualified attribute
     accesses, and never touching a name that isn't in that specific function's freevar
     set (i.e. never touching a genuinely local variable/parameter, since Python's
     compiler already told us it's NOT a free variable of that function).
  3. Splits run_simulation's own top-level body (with all nested defs removed) into
     config/state setup (-> __init__) and the main loop + reporting (-> run()). Names
     assigned in the first half and read in the second need explicit `self.X = X`
     seeding since __init__ and run() are separate methods with no shared local scope
     (unlike the original single function) -- handled generously (over-inclusion is
     harmless; under-inclusion is a NameError, so this errs toward including too much).
  4. Assembles everything as real ast.ClassDef / ast.Module trees (not string
     concatenation with manual indentation), distributed across files by role and
     combined via multiple inheritance -- ast.unparse() handles correct indentation.

Verify with `pytest tests/` after running. Not meant to be re-run against a
subsequently-hand-edited simulate.py.
"""
import ast
import sys

sys.path.insert(0, "src")
import iidsim.engine.simulate as sim_mod  # noqa: E402

SRC = "src/iidsim/engine/simulate.py"
OUT = "src/iidsim/engine"


def collect_code_freevars():
    def walk(code):
        yield code
        for c in code.co_consts:
            if hasattr(c, "co_name"):
                yield from walk(c)

    out = {}
    for code in walk(sim_mod.run_simulation.__code__):
        if code.co_name in ("run_simulation",) or code.co_name.startswith("<"):
            continue
        out[code.co_name] = set(code.co_freevars)
    return out


FREEVARS = collect_code_freevars()

# 'json' is a genuine freevar of total_schedule_to_json per co_freevars (it reads a
# *local* `import json` statement inside the original run_simulation's own body, which
# shadowed the top-level module import of the same name) -- but every generated file
# already does its own top-level `import json`, so self-ifying it would just look for a
# self.json attribute that's never set. Treat it as a plain module reference everywhere
# instead of a shared-state attribute.
NEVER_SELFIFY = {"json"}
FREEVARS = {name: fv - NEVER_SELFIFY for name, fv in FREEVARS.items()}


def collect_nesting_children(run_sim_def):
    out = {}

    def walk(node, owner):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.FunctionDef):
                        out.setdefault(owner, []).append(item.name)
                        walk(item, item.name)
                    elif isinstance(item, ast.AST):
                        walk(item, owner)
            elif isinstance(value, ast.AST):
                walk(value, owner)

    walk(run_sim_def, "run_simulation")
    return out


def _comprehension_bound_names(node):
    """Names bound by any `for x in ...` clause of a list/set/dict comp or genexpr --
    these get their OWN scope in Python 3 (PEP 289+), shadowing an outer variable of
    the same name for the comprehension's duration. A bare rename pass that doesn't
    know this would corrupt e.g. `[t for t in xs]` into `[self.t for t in xs]` if `t`
    happens to be a real free variable elsewhere in the same enclosing function.
    """
    names = set()

    def add_target(t):
        if isinstance(t, ast.Name):
            names.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for elt in t.elts:
                add_target(elt)

    for gen in node.generators:
        add_target(gen.target)
    return names


class SelfifyRenamer(ast.NodeTransformer):
    def __init__(self, targets):
        self.targets = targets

    def _visit_comprehension(self, node):
        shadowed = _comprehension_bound_names(node)
        if not shadowed & self.targets:
            return self.generic_visit(node)
        # temporarily exclude the shadowed names for this comprehension's subtree only
        # (its elt/key/value/ifs/nested-for iterables all share its scope; only the
        # first generator's own iterable is evaluated in the enclosing scope, but
        # excluding it there too is the safe direction -- worst case a rare real outer
        # reference stays unrenamed, causing a loud NameError, never silent corruption)
        saved = self.targets
        self.targets = saved - shadowed
        try:
            return self.generic_visit(node)
        finally:
            self.targets = saved

    visit_ListComp = _visit_comprehension
    visit_SetComp = _visit_comprehension
    visit_DictComp = _visit_comprehension
    visit_GeneratorExp = _visit_comprehension

    def visit_Name(self, node):
        if node.id in self.targets:
            return ast.copy_location(
                ast.Attribute(
                    value=ast.copy_location(ast.Name(id="self", ctx=ast.Load()), node),
                    attr=node.id,
                    ctx=node.ctx,
                ),
                node,
            )
        return node


def make_method(funcdef: ast.FunctionDef, extra_targets=()) -> ast.FunctionDef:
    freevars = FREEVARS.get(funcdef.name, set()) | set(extra_targets)
    stripped_body = [s for s in funcdef.body if not isinstance(s, (ast.Nonlocal, ast.Global))]
    new_body = [SelfifyRenamer(freevars).visit(ast.fix_missing_locations(stmt)) for stmt in stripped_body]
    new_args = ast.arguments(
        posonlyargs=[], args=[ast.arg(arg="self")] + list(funcdef.args.args),
        vararg=funcdef.args.vararg, kwonlyargs=funcdef.args.kwonlyargs,
        kw_defaults=funcdef.args.kw_defaults, kwarg=funcdef.args.kwarg,
        defaults=funcdef.args.defaults,
    )
    new_def = ast.FunctionDef(name=funcdef.name, args=new_args, body=new_body, decorator_list=[], returns=None)
    return ast.fix_missing_locations(new_def)


def extract_all_nested_funcdefs(node, out):
    if isinstance(node, ast.FunctionDef):
        kept_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                extract_all_nested_funcdefs(stmt, out)
                out[stmt.name] = stmt
            else:
                extract_all_nested_funcdefs(stmt, out)
                kept_body.append(stmt)
        node.body = kept_body
    else:
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, ast.AST):
                        if isinstance(item, ast.FunctionDef):
                            extract_all_nested_funcdefs(item, out)
                            out[item.name] = item
                            continue
                        extract_all_nested_funcdefs(item, out)
                    new_list.append(item)
                setattr(node, field, new_list)
            elif isinstance(value, ast.AST):
                extract_all_nested_funcdefs(value, out)
    return node


def collect_name_targets(stmt_list):
    targets = set()

    def add_target(t):
        if isinstance(t, ast.Name):
            targets.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for elt in t.elts:
                add_target(elt)

    for stmt in ast.walk(ast.Module(body=stmt_list, type_ignores=[])):
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                add_target(t)
        elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)):
            add_target(stmt.target)
    return targets


# ---------------------------------------------------------------------------
# Phase 1: extract + rewrite every nested function, split run_simulation's own body
# ---------------------------------------------------------------------------

source = open(SRC, encoding="utf-8").read()

nesting_tree = ast.parse(source)
nesting_run_sim = next(n for n in nesting_tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_simulation")
nesting_children = collect_nesting_children(nesting_run_sim)

tree = ast.parse(source)
run_sim_def = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_simulation")

nested = {}
extract_all_nested_funcdefs(run_sim_def, nested)
print(f"extracted {len(nested)} nested function defs")
assert set(nested) == set(FREEVARS), (set(nested) ^ set(FREEVARS))

methods = {
    name: make_method(fdef, extra_targets=nesting_children.get(name, ()))
    for name, fdef in nested.items()
}

body = run_sim_def.body
split_idx = next(i for i, stmt in enumerate(body) if isinstance(stmt, ast.While))
init_stmts = body[:split_idx]
run_stmts = body[split_idx:]

assign_targets = collect_name_targets(init_stmts)
run_reads = {
    n.id for n in ast.walk(ast.Module(body=run_stmts, type_ignores=[]))
    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
}
run_local_targets = collect_name_targets(run_stmts)
param_names = [a.arg for a in run_sim_def.args.args] + [a.arg for a in run_sim_def.args.kwonlyargs]

top_level_targets = (
    assign_targets
    | set(methods)
    | set().union(*FREEVARS.values())
    | ((run_reads & set(param_names)) - run_local_targets)
    | ((run_reads & assign_targets) - run_local_targets)
)

colliding_params = [p for p in param_names if p in top_level_targets]
print("parameters seeded onto self:", colliding_params)
seed_stmts = [ast.parse(f"self.{p} = {p}").body[0] for p in colliding_params]

init_stmts = [SelfifyRenamer(top_level_targets).visit(ast.fix_missing_locations(s)) for s in init_stmts]
run_stmts = [SelfifyRenamer(top_level_targets).visit(ast.fix_missing_locations(s)) for s in run_stmts]
init_stmts = seed_stmts + init_stmts

init_def = ast.FunctionDef(
    name="__init__",
    args=ast.arguments(
        posonlyargs=[], args=[ast.arg(arg="self")] + list(run_sim_def.args.args),
        vararg=None, kwonlyargs=list(run_sim_def.args.kwonlyargs),
        kw_defaults=list(run_sim_def.args.kw_defaults), kwarg=None,
        defaults=list(run_sim_def.args.defaults),
    ),
    body=init_stmts, decorator_list=[], returns=None,
)
init_def = ast.fix_missing_locations(init_def)

run_def = ast.fix_missing_locations(
    ast.FunctionDef(name="run", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")],
                                                     vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                     body=run_stmts, decorator_list=[], returns=None)
)

print(f"__init__: {len(init_stmts)} statements, run(): {len(run_stmts)} statements")

# ---------------------------------------------------------------------------
# Phase 2: assemble into class-based files
# ---------------------------------------------------------------------------

IMPORTS_SRC = '''import json
import time

import numpy as np
import pandas as pd
from pandas import Timestamp
from scipy import stats as _halt_dev_stats
from openpyxl.styles import Alignment, Font

import iidsim.network as _network
from iidsim import schedules
from iidsim.data import geography, halt_deviation, timing
from iidsim.reporting.chart import plot_railway_chart
from iidsim.reporting.extract import filter_df_by_date_window, get_formatted_data_from_df
'''

FILE_OF = {}
for name in [
    "get_queue_end_time", "find_free_sibling_blsec", "blsec_id", "find_stn3",
    "check_next_blse_stn_occupancy", "stn_line_assign", "get_min_endtime",
    "outgoing_blsec_name", "conn_base", "conn_exists",
    "get_train_stnline_for_arrival_delay", "get_train_stnline_for_departure_delay",
    "train_direction",
]:
    FILE_OF[name] = "resolve"
for name in [
    "update_blsec_queue_priority", "autoblsec_check", "get_pass_train_stnline_endtimes",
    "get_prev_blsec_obj", "get_prev_pass_train_arr_time", "goods_delay_due_to_passenger",
    "check_if_all_goods",
]:
    FILE_OF[name] = "priority"
for name in [
    "_sample_halt_dev", "_generate_halt_deviation", "add_halt_randomness",
    "_sample_blsec_time", "add_speed_randomness", "new_arr_by_speed_randomness",
]:
    FILE_OF[name] = "randomness"
for name in [
    "build_event_list", "term_crit_calc", "get_station_event", "get_earliest_time",
    "compute_start_dt", "sched_updt", "tr_sched_updt",
]:
    FILE_OF[name] = "events"
for name in [
    "resource_update_event", "build_deviation_rows", "avg_sd_str", "remove_outliers_iqr",
    "avg_sd_str_no_outliers", "get_max_dev", "get_distance", "clean_stn",
    "compute_train_avg_speed", "dev_list", "r2", "master_time_distance_chart",
    "total_schedule_to_json",
]:
    FILE_OF[name] = "run"

assert set(FILE_OF) == set(methods), set(methods) ^ set(FILE_OF)

by_file = {"resolve": [], "priority": [], "randomness": [], "events": [], "run": []}
for name in sorted(FILE_OF):
    by_file[FILE_OF[name]].append(name)

MIXIN_CLASS = {
    "resolve": "ResolveMixin", "priority": "PriorityMixin",
    "randomness": "RandomnessMixin", "events": "EventsMixin",
}


def write_module(path, docstring, import_src, class_nodes):
    mod_body = []
    if import_src:
        mod_body.extend(ast.parse(import_src).body)
    mod_body.extend(class_nodes)
    mod = ast.Module(body=mod_body, type_ignores=[])
    ast.fix_missing_locations(mod)
    src = f'"""{docstring}"""\n\n' + ast.unparse(mod)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"wrote {path}")


for key, class_name in MIXIN_CLASS.items():
    class_def = ast.ClassDef(
        name=class_name, bases=[], keywords=[],
        body=[methods[n] for n in by_file[key]], decorator_list=[],
    )
    write_module(
        f"{OUT}/{key}.py",
        f"Part of the simulation engine -- see docs/restructure-notes.md and "
        f"docs/simulation-engine.md. Mixed into Simulation (engine/run.py); every "
        f"method here reads/writes shared per-run state via self.X (see "
        f"SimulationState in engine/state.py).",
        IMPORTS_SRC, [class_def],
    )

state_class = ast.ClassDef(name="SimulationState", bases=[], keywords=[], body=[init_def], decorator_list=[])
write_module(
    f"{OUT}/state.py",
    "Per-run simulation state, set up once in __init__ -- everything the other "
    "mixins (resolve/priority/randomness/events) and run() read/write via self.X. "
    "See docs/restructure-notes.md for how this was derived (Python's own "
    "co_freevars, not guesswork).",
    IMPORTS_SRC, [state_class],
)

run_class_body = [methods["resource_update_event"], run_def] + [methods[n] for n in by_file["run"] if n != "resource_update_event"]
run_class = ast.ClassDef(
    name="Simulation",
    bases=[ast.Name(id=n, ctx=ast.Load()) for n in ("SimulationState", "ResolveMixin", "PriorityMixin", "RandomnessMixin", "EventsMixin")],
    keywords=[], body=run_class_body, decorator_list=[],
)
run_imports = (
    "from iidsim.engine.state import SimulationState\n"
    "from iidsim.engine.resolve import ResolveMixin\n"
    "from iidsim.engine.priority import PriorityMixin\n"
    "from iidsim.engine.randomness import RandomnessMixin\n"
    "from iidsim.engine.events import EventsMixin\n\n" + IMPORTS_SRC
)
write_module(
    f"{OUT}/run.py",
    "The Simulation class: combines every mixin, the main event loop (run()), "
    "resource_update_event() (the core per-event state transition -- by far the "
    "largest single method, deliberately kept as one function rather than further "
    "split, see docs/restructure-notes.md for why), and the Excel/chart/JSON "
    "report-generation helpers.\n\n"
    "run_simulation() below is the public entry point: build a Simulation, run it, "
    "return the result dict -- unchanged from before this split, just delegating to "
    "the class now instead of executing one large function body.",
    run_imports, [run_class],
)

# top-level run_simulation() wrapper, appended to run.py
wrapper_src = '''

def run_simulation(
    corridor_dataset,
    network_section,
    *,
    trains_override=None,
    output_dir="output_files",
    start_dt_mode="planned",
    start_dt_manual=None,
    start_dt_buffer_minutes=10,
    chart_duration_hrs=23,
    headway_distance=3.6,
    goods_max_priority_wait_hours=20,
    autoblock_stations=("alm", "kuk", "vzm"),
    use_halt_deviation=True,
    use_speed_randomness=True,
    halt_deviation_seed=1234,
    speed_randomness_seed=1234,
):
    """Run one end-to-end simulation and write the Excel report, time-distance
    chart PDF, and animator JSON for `corridor_dataset` on `network_section`.

    corridor_dataset: a name from iidsim.schedules.available_corridors(), e.g.
        'p_g_sprd_vzm_2days' -- replaces the old hardcoded per-corridor import. Still
        used to derive output filenames even when `trains_override` is given.
    network_section: one of 'psa_ktv', 'sprd_vzm', 'krdl_ktv' -- which corridor's
        station order / segment distances to use for the output chart.
    trains_override: optional list[iidsim.domain.train] to simulate directly instead of
        loading `corridor_dataset` from iidsim.schedules -- for synthetic/targeted test
        scenarios built against the real network (see tests/scenarios.py).

    Returns a dict with the three output file paths plus the in-memory
    total_schedule and trains the run produced.
    """
    sim = Simulation(
        corridor_dataset,
        network_section,
        trains_override=trains_override,
        output_dir=output_dir,
        start_dt_mode=start_dt_mode,
        start_dt_manual=start_dt_manual,
        start_dt_buffer_minutes=start_dt_buffer_minutes,
        chart_duration_hrs=chart_duration_hrs,
        headway_distance=headway_distance,
        goods_max_priority_wait_hours=goods_max_priority_wait_hours,
        autoblock_stations=autoblock_stations,
        use_halt_deviation=use_halt_deviation,
        use_speed_randomness=use_speed_randomness,
        halt_deviation_seed=halt_deviation_seed,
        speed_randomness_seed=speed_randomness_seed,
    )
    return sim.run()
'''
with open(f"{OUT}/run.py", "a", encoding="utf-8") as f:
    f.write(wrapper_src)
print("appended run_simulation() wrapper to run.py")
