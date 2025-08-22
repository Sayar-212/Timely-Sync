from typing import List, Tuple
from core.constraint_schema import Timetable, ConstraintPackage
from core.scoring import score_timetable
from utils.logging_utils import get_logger

logger = get_logger("TimetableOptimizerAgent")

class TimetableOptimizerAgent:
    def select_best(self, feasible: List[Timetable], constraints: ConstraintPackage) -> Tuple[Timetable, float]:
        if not feasible:
            raise ValueError("No feasible timetables provided to optimizer.")
        best = None
        best_score = float("-inf")
        for tt in feasible:
            s = score_timetable(tt, constraints)
            if s > best_score:
                best = tt
                best_score = s
        logger.info(f"Selected timetable with score={best_score:.3f}")
        return best, best_score
