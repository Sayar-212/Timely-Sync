from typing import List
from agents.constraint_parser import ConstraintParserAgent
from agents.csp_solver import CSPSolverAgent
from agents.timetable_optimizer import TimetableOptimizerAgent
from agents.constraint_verifier import ConstraintVerifierAgent
from agents.formatter import FormatterAgent
from core.constraint_schema import ConstraintPackage, Timetable, SolverResult, VerificationResult
from utils.logging_utils import get_logger
from config.settings import settings

logger = get_logger("Orchestrator")

class Orchestrator:
    def __init__(self):
        self.parser = ConstraintParserAgent()
        self.solver = CSPSolverAgent()
        self.optimizer = TimetableOptimizerAgent()
        self.verifier = ConstraintVerifierAgent()
        self.formatter = FormatterAgent()

    def run(self, nl_constraints: List[str], max_solver_solutions: int = 6, allow_soft_relaxation: bool = True) -> dict:
        for attempt in range(settings.MAX_RETRIES + 1):
            try:
                cp: ConstraintPackage = self.parser.parse(nl_constraints)
                logger.info("Constraints parsed and validated.")
                break
            except Exception as e:
                logger.warning(f"Parse attempt {attempt+1} failed: {e}")
                if attempt >= settings.MAX_RETRIES:
                    raise

        for attempt in range(settings.MAX_RETRIES + 1):
            sr: SolverResult = self.solver.solve(cp, max_solutions=max_solver_solutions)
            if sr.status in ("FEASIBLE", "OPTIMAL") and sr.feasible_timetables:
                break
            logger.warning(f"CSP solve attempt {attempt+1} -> {sr.status}")
            if attempt >= settings.MAX_RETRIES:
                if allow_soft_relaxation:
                    logger.error("Hard constraints unsatisfiable after retries. Aborting.")
                raise RuntimeError("Unsatisfiable hard constraints.")

        best_tt, score = self.optimizer.select_best(sr.feasible_timetables, cp)
        logger.info(f"Best timetable soft score: {score:.3f}")

        for attempt in range(settings.MAX_RETRIES + 1):
            vr: VerificationResult = self.verifier.verify(best_tt, cp)
            if vr.passed and not vr.warnings:
                logger.info("Verification passed with no warnings.")
                break
            elif vr.passed and vr.warnings:
                logger.warning(f"Verification warnings found: {vr.warnings}")
                logger.info(f"Trying alternative timetable (attempt {attempt+1})")
                remaining = [t for t in sr.feasible_timetables if t is not best_tt]
                if not remaining:
                    logger.warning("No alternative timetables available, accepting with warnings.")
                    break
                best_tt, score = self.optimizer.select_best(remaining, cp)
            else:
                logger.error(f"Verification errors: {vr.errors}")
                if attempt >= settings.MAX_RETRIES:
                    raise RuntimeError("Final verification failed.")
                remaining = [t for t in sr.feasible_timetables if t is not best_tt]
                if not remaining:
                    raise RuntimeError("No alternative feasible timetable to try after verification failure.")
                best_tt, score = self.optimizer.select_best(remaining, cp)

        outputs = self.formatter.export(best_tt, base_filename="timetable")
        return {
            "constraints": cp.model_dump(),
            "timetable": best_tt.model_dump(),
            "verification": vr.model_dump(),
            "outputs": outputs,
        }
