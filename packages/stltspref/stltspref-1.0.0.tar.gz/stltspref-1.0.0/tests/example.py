import gurobipy as gp
from stltspref.preferential_synthesis import benchmark_pref_synth, diversity_finder
from stltspref.linear_expression import LinearExpression as L
from stltspref.problem import create_stl_milp_problem
from stltspref.stl import (
    Alw,
    And,
    Atomic,
    BoundedAlw,
    BoundedEv,
    BoundedUntil,
    Ev,
    Implies,
    Or,
    Until,
    StlFormula,
    make_unique,
)


# ---- PARAMETERS ----

benchmark_name = "rnc1"
diversity_mode = "random"
N = 10
numsols = 5
time_limit = 10000
gap = 0.01
absolute_gap = 3
export_traces = False
export_path = ""

# ---- EXAMPLE USING BENCHMARK ----

# benchmark_pref_synth(benchmark_name, diversity_mode, N, numsols, 
#                     time_limit=time_limit, gap=gap, absolute_gap=absolute_gap, 
#                     export_path=export_path, export_traces=export_traces)

# ---- EXAMPLE USING CUSTOM PROBLEM ----

milp = gp.Model()
prob = create_stl_milp_problem(
        milp,
        N=N,
        delta=0.1,
        gamma_N=20.0,
        gamma_unit_length=0.005,
        use_binary_expansion=True,
    )

elevator = prob.create_system_model()

elevator.add_state('z', 0, 40)
elevator.add_state('v', -5, 5)
elevator.add_state('a', -3, 3)

elevator.set_initial_state(z=(0,0), v=(0,0), a=(0,0))
elevator.add_dynamics('a', -3, 3, constant=True)
elevator.add_double_integrator_dynamics('z', 'v', 'a')

spec = make_unique(
    Ev(And(
        Atomic(L.unit('z') >= 20), 
        Ev(And(
            Atomic(L.unit('z') <= 1),
            Atomic(L.unit('v') >= 0)
            ))
    ))
)
prob.initialize_milp_formulation(spec)

diversity_finder(prob, diversity_mode, N, numsols, time_limit, 
                 gap, absolute_gap, export_traces, export_path)
