import gurobipy as gp
import json
from random import randint
from stltspref.problem import StlMilpProblem
from stltspref.benchmarks import get_benchmark
import matplotlib.pyplot as plt
from stltspref.linear_expression import *
from stltspref.stl import make_unique


def random_dist(prob: StlMilpProblem):
    """
    Creates a random objective function based on a Hamming distance 
    to a randomly chosen point in solution space.
    """
    obj = 0
    for var in prob.milp_variables.stl_sat.values():
        for v in var.values():
            if randint(0, 1):
                obj += 1-v
            else:
                obj += v
    return obj


def hamm_dist(prob: StlMilpProblem, coeffs: dict[gp.Var, int], constant: int):
    """
    Given a dictionary `coeffs` of previous coefficients of variables in problem `prob`,
    and a constant value (to ensure the objective is nonnegative),
    creates a new objective function based on a Hamming distance to the previous solutions.
    """
    obj = 0
    for var in prob.milp_variables.stl_sat.values():
        for v in var.values():
            if v.Xn == 1:
                constant += 1
                coeffs[v] -= 1 
            else:
                coeffs[v] += 1 
            obj += coeffs[v]*v
    return obj + constant, constant


def val_dist(prob: StlMilpProblem, i: int, milp: gp.Model):
    """
    Adds variables and constraints to encode absolute values
    and creates an objective function based on a value distance to the previous solutions.
    """
    obj = 0
    state = prob.system_model.state
    for var in state:
        for v in state[var].tolist():
            v_subs = milp.addVar(name=v.VarName+f"_subs_{i}", lb=-float('inf'))
            milp.addConstr(v_subs == v - v.Xn, name=v.VarName+f"_subs_{i}")
            v_abs = milp.addVar(name=v.VarName+f"_abs_{i}", lb=0)
            milp.addConstr(v_abs == gp.abs_(v_subs), name=v.VarName+f"_abs_{i}")
            obj += v_abs
    return obj


def encode_row(sample):
    """
    Puts trace values into rows for json encoding.
    """
    row = {}
    row['time'] = float(sample['t'])
    row['value'] = {k: float(v) for k, v in sample.items() if k != 't'}
    return row


def diversity_finder(
    prob: StlMilpProblem, 
    diversity_mode: str, 
    N: int, 
    numsols: int, 
    time_limit: float = 10000, 
    gap: float = 0.00001, 
    absolute_gap: float = 0.0001,
    export_traces: bool = False,
    export_path: str = ""
):
    """
    Generates `numsols` solutions to the STL trace 
    synthesis problem `prob` using a diversity heuristic.

    Args:
        `prob` (StlMilpProblem): The STL trace synthesis problem object,
            generated beforehand with system variables and a system model.
        `diversity_mode` (str): Identifier for the diversity method to use.
            Possible values are 
            - `'gurobi'` for the Solution Pool method,
            - `'hamming'` for the Hamming Distance Maximization method,
            - `'random'` for the Randomized Hamming Distance Maximization method,
            - `'value'` for the Value Distance Maximization method.
        `N` (int): Number of intervals of linearity in the generated traces.
        `numsols` (int): Number of different solutions to generate.
        `time_limit` (float): Maximum computation time in seconds.
        `gap` (float): Relative gap between incumbent solutions and
            known upper bounds to end trace search.
        `absolute_gap` (float): Absolute gap between incumbent solutions and
            known upper bounds to end trace search.
        `export_traces` (bool): Whether to export `json` files containing 
            the generated trace values.
        `export_path` (str): File path used when exporting trace value data.
    
    Raises:
        `ValueError`: Whenever `diversity_mode` is not one of its four possible values.
    """
    milp = prob.milp
    milp.Params.IntegralityFocus = 1
    # set chosen parameters
    milp.Params.TimeLimit = time_limit
    milp.Params.MIPGap = gap
    milp.Params.MIPGapAbs = absolute_gap
    if diversity_mode == "gurobi":
        prob.search_satisfaction(numsols, 2)
        if prob.has_solution:
            # get trace values, plot them and save them
            traces_continuous = prob.get_trace_result(interpolation=True)
            traces_raw = prob.get_trace_result(interpolation=False)
            for i in range(milp.SolCount):
                traces_continuous[i].df.plot(x='t')
                if export_traces:
                    rows = [encode_row(sample) for sample in traces_raw[i].samples]
                    with open(export_path+f'output_{i+1}.json', 'w') as f:
                        json.dump(rows, f, indent=2)
            plt.show()
        else:
            print(f'No trace found with N {N}')

    elif diversity_mode == "hamming" or diversity_mode == "value":
        prob.search_satisfaction(1, 0)
        if prob.has_solution:
            # get trace values, plot them and save them
            traces_continuous = prob.get_trace_result(interpolation=True)
            traces_continuous[0].df.plot(x='t')
            if export_traces:
                rows = [encode_row(sample) for sample in prob.get_trace_result(interpolation=False)[0].samples]
                with open(export_path+f'output_{1}.json', 'w') as f:
                    json.dump(rows, f, indent=2)
        obj = 0
        if diversity_mode == "value":
            # ensure to have the same time sequence
            g = prob.get_gamma_result()
            milp.addConstrs(
                (prob.milp_variables.gamma[i] == g[i] for i in range(prob.N+1)), 
                name="gamma_equality"
            )
        else:
            # initialize coeffs and constant value in hamming objective 
            coeffs = {v: 0 for var in prob.milp_variables.stl_sat.values() for v in var.values()}
            constant = 0
        for sol in range(1, numsols):
            # update objective
            if diversity_mode == "hamming":
                obj, constant = hamm_dist(prob, coeffs, constant)
            else:
                obj += val_dist(prob, sol, milp)
            milp.setObjective(obj, gp.GRB.MAXIMIZE)
            # search sol
            prob.search_satisfaction(1, 0)
            if prob.has_solution:
                # get trace values, plot them and save them
                traces_continuous = prob.get_trace_result(interpolation=True)
                traces_continuous[0].df.plot(x='t')
                if export_traces:
                    rows = [encode_row(sample) for sample in prob.get_trace_result(interpolation=False)[0].samples]
                    with open(export_path+f'output_{sol+1}.json', 'w') as f:
                        json.dump(rows, f, indent=2)
        plt.show()

    elif diversity_mode == "random":
        for sol in range(numsols):
            # create a random objective
            obj = random_dist(prob)
            milp.setObjective(obj, gp.GRB.MAXIMIZE)
            # solve
            prob.search_satisfaction(1, 0)
            if prob.has_solution:
                # get trace values, plot them and save them
                traces_continuous = prob.get_trace_result(interpolation=True)
                traces_continuous[0].df.plot(x='t')
                if export_traces:
                    rows = [encode_row(sample) for sample in prob.get_trace_result(interpolation=False)[0].samples]
                    with open(export_path+f'output_{sol+1}.json', 'w') as f:
                        json.dump(rows, f, indent=2)
        plt.show()
    
    else:
        raise ValueError(f"Unsupported method name: {diversity_mode}.")


def pn_pair_finder(
    benchmark_name: str,
    N: int, 
    time_limit: float = 10000, 
    gap: float = 0.00001, 
    absolute_gap: float = 0.0001,
    export_traces: bool = False,
    export_path: str = ""
):
    """
    Generates two solutions to two STL trace 
    synthesis problems, one with a positive spec and one negative.

    Args:
        `benchmark_name` (str): Identifier for the benchmark to use.
            Possible values are
            - `'dstop'`,
            - `'rnc1'` to `'rnc3'`,
            - `'nav1'` or `'nav2'`,
            - `'iso1'` to `'iso8'`.
        `N` (int): Number of intervals of linearity in the generated traces.
        `numsols` (int): Number of different solutions to generate.
        `time_limit` (float): Maximum computation time in seconds.
        `gap` (float): Relative gap between incumbent solutions and
            known upper bounds to end trace search.
        `absolute_gap` (float): Absolute gap between incumbent solutions and
            known upper bounds to end trace search.
        `export_traces` (bool): Whether to export `json` files containing 
            the generated trace values.
        `export_path` (str): File path used when exporting trace value data.
    """
    milp = gp.Model()
    milp.Params.IntegralityFocus = 1
    # set chosen parameters
    milp.Params.TimeLimit = time_limit
    milp.Params.MIPGap = gap
    milp.Params.MIPGapAbs = absolute_gap
    # initialize problem
    prob = get_benchmark(milp, benchmark_name, N=N, delta=0.1)
    milp.update()
    # rename all positive vars and constrs in milp to distinguish pos and neg vars
    for var in milp.getVars():
        var.VarName += "_posver"
    for constr in milp.getConstrs():
        constr.ConstrName += "_posver"
    # initialize the negative problem
    neg_spec = make_unique(prob.stl_spec.negation())
    prob2 = get_benchmark(milp, benchmark_name, N=N, custom_spec=neg_spec, delta=0.1)
    milp.update()
    # rename all negative vars and constrs in milp for clarity
    for var in milp.getVars():
        if not var.VarName.endswith("_posver"):
            var.VarName += "_negver"
    for constr in milp.getConstrs():
        if not constr.ConstrName.endswith("_posver"):
            constr.ConstrName += "_negver"
    # create the objective function (adding absolute value constraints)
    obj = 0
    milp.update()
    for v in prob.state:
        for i in range(prob.N + 1):
            var1 = prob.state[v][i].item()
            var2 = prob2.state[v][i].item()
            v_sub = milp.addVar(name=v+"_sub")
            milp.addConstr(v_sub == var1 - var2, name=v+f"[{i}]_sub")
            v_abs = milp.addVar(name=v+f"[{i}]_abs")
            milp.addConstr(v_abs == gp.abs_(v_sub), name=v+f"[{i}]_abs")
            obj += v_abs
    # add constraints to have identical time sequences in pos and neg problems
    milp.addConstrs(
        (prob.milp_variables.gamma[i] == prob2.milp_variables.gamma[i] for i in range(prob.N+1)),
        name="gamma_equality"
    )
    milp.setObjective(obj, gp.GRB.MINIMIZE)
    # solve prob2 (or prob1, it uses the same milp solve)
    prob2.search_satisfaction()
    if prob2.has_solution:
        # get trace values, plot them and save them for positive prob
        prob.get_trace_result(interpolation=True)[0].df.plot(x='t')
        if export_traces:
            rows = [encode_row(sample) for sample in prob.get_trace_result(interpolation=False)[0].samples]
            with open(export_path+f'output_pos.json', 'w') as f:
                json.dump(rows, f, indent=2)
        # same for negative prob, in case they differ
        prob2.get_trace_result(interpolation=True)[0].df.plot(x='t')
        if export_traces:
            rows = [encode_row(sample) for sample in prob.get_trace_result(interpolation=False)[0].samples]
            with open(export_path+f'output_neg.json', 'w') as f:
                json.dump(rows, f, indent=2)
        plt.show()


def benchmark_pref_synth(
    benchmark_name: str, 
    diversity_mode: str, 
    N: int, 
    numsols: int,
    **kwargs
):
    """
    Uses preferential synthesis method identified by `diversity_mode`
    on the benchmark identified by `benchmark_name`.

    Args:
        `benchmark_name` (str): Identifier for the benchmark to use.
            Possible values are
            - `'dstop'`,
            - `'rnc1'` to `'rnc3'`,
            - `'nav1'` or `'nav2'`,
            - `'iso1'` to `'iso8'`.
        `diversity_mode` (str): Identifier for the diversity method to use.
            Possible values are 
            - `'gurobi'` for the Solution Pool method,
            - `'hamming'` for the Hamming Distance Maximization method,
            - `'random'` for the Randomized Hamming Distance Maximization method,
            - `'value'` for the Value Distance Maximization method,
            - `'pn_pair'` for the Positive-Negative Pair method.
        `N` (int): Number of intervals of linearity in the generated traces.
        `numsols` (int): Number of different solutions to generate.
        `time_limit` (float): Maximum computation time in seconds. 
            Defaults to `10000`.
        `gap` (float): Relative gap between incumbent solutions and
            known upper bounds to end trace search. Defaults to `0.00001`.
        `absolute_gap` (float): Absolute gap between incumbent solutions and
            known upper bounds to end trace search. Defaults to `0.0001`.
        `export_traces` (bool): Whether to export `json` files containing 
            the generated trace values. Defaults to `False`.
        `export_path` (str): File path used when exporting trace value data. 
            Defaults to `''`.
    """
    if diversity_mode == "pn_pair":
        pn_pair_finder(benchmark_name, N, **kwargs)
    else:
        milp = gp.Model()
        prob = get_benchmark(milp, benchmark_name, N=N, delta=0.1)
        diversity_finder(prob, diversity_mode, N, numsols, **kwargs)
