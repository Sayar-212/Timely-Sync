import os
from timetable_backend.agents.constraint_parser import ConstraintParserAgent
from timetable_backend.agents.csp_solver import CSPSolverAgent
from timetable_backend.agents.timetable_optimizer import TimetableOptimizerAgent
from timetable_backend.agents.formatter import FormatterAgent

def test_formatter_exports(tmp_path):
    parser = ConstraintParserAgent()
    solver = CSPSolverAgent()
    opt = TimetableOptimizerAgent()
    fmt = FormatterAgent()

    nl = [
        "Prof. Sharma is only available on Mon S1,S2, Tue S1",
        "Math taught by Prof. Sharma needs 2 periods",
        "Sci taught by Prof. Rao needs 2 periods",
        "Eng taught by Prof. Iyer needs 2 periods",
    ]
    cp = parser.parse(nl)
    res = solver.solve(cp, max_solutions=2)
    tt, score = opt.select_best(res.feasible_timetables, cp)

    from timetable_backend.config.settings import settings as global_settings
    old = global_settings.OUTPUT_DIR
    global_settings.OUTPUT_DIR = str(tmp_path)

    paths = fmt.export(tt, base_filename="test_tt")

    global_settings.OUTPUT_DIR = old

    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["pdf"])
