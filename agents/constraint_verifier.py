from typing import List
from core.constraint_schema import Timetable, ConstraintPackage, VerificationResult
from utils.logging_utils import get_logger
from config.settings import settings

logger = get_logger("ConstraintVerifierAgent")

def _semantic_check_with_gemini(tt: Timetable, constraints: ConstraintPackage) -> List[str]:
    if not settings.GEMINI_API_KEY:
        warnings = []
        pref = constraints.soft.preferred_windows
        grid = tt.as_grid()
        for subj, wins in pref.items():
            if not any((w.split(":")[0] in grid and w.split(":")[1] in grid[w.split(":")[0]] and
                        grid[w.split(":")[0]][w.split(":")[1]].subject_id == subj) for w in wins):
                warnings.append(f"Preferred window unmet for subject {subj}.")
        return warnings
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.MODEL_NAME)
        prompt = (
            "You are verifying a timetable against human-meaning rules. "
            "Identify any semantic issues not captured by strict CSP rules. "
            "Return a JSON list of warning strings only."
        )
        payload = {
            "timetable": tt.model_dump(),
            "constraints": constraints.model_dump(),
        }
        import json
        resp = model.generate_content([prompt, json.dumps(payload)])
        text = resp.text
        logger.info(f"Gemini verification response: {repr(text)}")
        # Extract JSON from markdown code blocks if present
        if text.strip().startswith('```json') and text.strip().endswith('```'):
            text = text.strip()[7:-3].strip()
        elif text.strip().startswith('```') and text.strip().endswith('```'):
            text = text.strip()[3:-3].strip()
        warnings = json.loads(text)
        if isinstance(warnings, list):
            return [str(w) for w in warnings]
        return ["AI semantic check returned unexpected format."]
    except Exception as e:
        logger.warning(f"Gemini semantic check failed: {e}")
        return []

class ConstraintVerifierAgent:
    def verify(self, tt: Timetable, constraints: ConstraintPackage) -> VerificationResult:
        hard = constraints.hard
        errors: List[str] = []

        from collections import Counter
        counts = Counter(a.subject_id for a in tt.assignments)
        for s in hard.subjects:
            if counts.get(s.id, 0) != s.periods_per_week:
                errors.append(f"Subject {s.id} has {counts.get(s.id,0)} periods; requires {s.periods_per_week}.")

        teachers = {t.id: t for t in hard.teachers}
        for a in tt.assignments:
            if a.slot not in teachers[a.teacher_id].availability.get(a.day, []):
                errors.append(f"Teacher {a.teacher_id} not available on {a.day} {a.slot}.")

        seen = set()
        for a in tt.assignments:
            key = (a.day, a.slot)
            if key in seen:
                errors.append(f"Duplicate assignment in {a.day} {a.slot}.")
            seen.add(key)

        warnings = _semantic_check_with_gemini(tt, constraints)
        return VerificationResult(passed=(len(errors) == 0), errors=errors, warnings=warnings)
