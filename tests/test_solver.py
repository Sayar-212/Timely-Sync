from timetable_backend.agents.constraint_parser import ConstraintParserAgent
from timetable_backend.agents.csp_solver import CSPSolverAgent

def test_solver_feasible():
    parser = ConstraintParserAgent()
    solver = CSPSolverAgent()
    nl = [
        "Prof. Sharma is only available on Mon S1,S2, Tue S1",
        "Math taught by Prof. Sharma needs 2 periods",
        "Sci taught by Prof. Rao needs 2 periods",
        "Eng taught by Prof. Iyer needs 2 periods",
    ]
    cp = parser.parse(nl)
    res = solver.solve(cp, max_solutions=3)
    assert res.status in ("FEASIBLE", "OPTIMAL")
    assert len(res.feasible_timetables) >= 1
