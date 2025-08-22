from timetable_backend.agents.constraint_parser import ConstraintParserAgent
from timetable_backend.agents.csp_solver import CSPSolverAgent
from timetable_backend.agents.timetable_optimizer import TimetableOptimizerAgent
from timetable_backend.agents.constraint_verifier import ConstraintVerifierAgent

def test_verifier_pass():
    parser = ConstraintParserAgent()
    solver = CSPSolverAgent()
    opt = TimetableOptimizerAgent()
    ver = ConstraintVerifierAgent()

    nl = [
        "Prof. Sharma is only available on Mon S1,S2, Tue S1",
        "Math taught by Prof. Sharma needs 2 periods",
        "Sci taught by Prof. Rao needs 2 periods",
        "Eng taught by Prof. Iyer needs 2 periods",
    ]
    cp = parser.parse(nl)
    res = solver.solve(cp, max_solutions=3)
    tt, score = opt.select_best(res.feasible_timetables, cp)
    vr = ver.verify(tt, cp)
    assert vr.passed
