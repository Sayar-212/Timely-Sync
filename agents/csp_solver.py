from typing import List, Dict, Tuple
from ortools.sat.python import cp_model
from core.constraint_schema import ConstraintPackage, Timetable, AssignedCell, SolverResult
from utils.logging_utils import get_logger
from config.settings import settings

logger = get_logger("CSPSolverAgent")

class CSPSolverAgent:
    def solve(self, constraints: ConstraintPackage, max_solutions: int = 5) -> SolverResult:
        hard = constraints.hard
        days = hard.days
        slot_names = hard.slot_names
        subjects = hard.subjects
        teachers = {t.id: t for t in hard.teachers}

        model = cp_model.CpModel()
        subject_ids = [s.id for s in subjects]

        x: Dict[Tuple[int, int, int], cp_model.IntVar] = {}
        for di, day in enumerate(days):
            for si, slot in enumerate(slot_names):
                for subi, subj in enumerate(subject_ids):
                    x[(di, si, subi)] = model.NewBoolVar(f"x_{day}_{slot}_{subj}")

        for di, day in enumerate(days):
            for si, slot in enumerate(slot_names):
                model.Add(sum(x[(di, si, subi)] for subi, _ in enumerate(subject_ids)) <= 1)

        for subi, subj in enumerate(subject_ids):
            req = next(s for s in subjects if s.id == subj).periods_per_week
            model.Add(sum(x[(di, si, subi)] for di, _ in enumerate(days) for si, _ in enumerate(slot_names)) == req)

        for di, day in enumerate(days):
            for si, slot in enumerate(slot_names):
                for subi, subj in enumerate(subject_ids):
                    subj_obj = next(s for s in subjects if s.id == subj)
                    teacher = teachers[subj_obj.teacher_id]
                    allowed = slot in teacher.availability.get(day, [])
                    if not allowed:
                        model.Add(x[(di, si, subi)] == 0)

        if hard.max_periods_per_day is not None:
            for di, _ in enumerate(days):
                model.Add(
                    sum(x[(di, si, subi)] for si, _ in enumerate(slot_names) for subi, _ in enumerate(subject_ids))
                    <= hard.max_periods_per_day
                )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = settings.CSP_MAX_TIME_SECONDS
        solutions: List[Timetable] = []

        class Collector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.count = 0
            def on_solution_callback(self):
                nonlocal solutions
                self.count += 1
                assignments = []
                for di, day in enumerate(days):
                    for si, slot in enumerate(slot_names):
                        for subi, subj in enumerate(subject_ids):
                            if self.Value(x[(di, si, subi)]) == 1:
                                subj_obj = next(s for s in subjects if s.id == subj)
                                assignments.append(AssignedCell(
                                    day=day, slot=slot, subject_id=subj_obj.id, teacher_id=subj_obj.teacher_id
                                ))
                tt = Timetable(
                    class_name=hard.class_name,
                    days=days,
                    slot_names=slot_names,
                    assignments=assignments
                )
                solutions.append(tt)
                if self.count >= max_solutions:
                    self.StopSearch()

        cb = Collector()
        status = solver.SearchForAllSolutions(model, cb)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        label = status_map.get(status, "UNKNOWN")
        logger.info(f"CSP search done: {label}, solutions={len(solutions)}")

        return SolverResult(feasible_timetables=solutions, status=label)
