from typing import List, Dict, Any
from pydantic import ValidationError
from core.constraint_schema import ConstraintPackage, HardConstraints, SoftConstraints, Teacher, Subject
from config.settings import settings
from utils.logging_utils import get_logger

logger = get_logger("ConstraintParser")

def _fallback_rule_based_parser(nl_constraints: List[str]) -> ConstraintPackage:
    days = settings.DAYS
    slots_per_day = settings.SLOTS_PER_DAY
    slot_names = [f"S{i+1}" for i in range(slots_per_day)]

    teachers: Dict[str, Teacher] = {
        "T1": Teacher(id="T1", name="Prof. Sharma", availability={d: slot_names[:] for d in days}),
        "T2": Teacher(id="T2", name="Prof. Rao",     availability={d: slot_names[:] for d in days}),
        "T3": Teacher(id="T3", name="Prof. Iyer",    availability={d: slot_names[:] for d in days}),
    }
    subjects: Dict[str, Subject] = {
        "Math": Subject(id="Math", name="Mathematics", teacher_id="T1", periods_per_week=2),
        "Sci":  Subject(id="Sci",  name="Science",     teacher_id="T2", periods_per_week=2),
        "Eng":  Subject(id="Eng",  name="English",     teacher_id="T3", periods_per_week=2),
    }

    preferred_windows: Dict[str, List[str]] = {}

    for line in nl_constraints:
        l = line.strip()
        if "only available on" in l:
            name = l.split(" is only available on ")[0].replace("Prof. ", "").strip()
            teacher = next((t for t in teachers.values() if t.name.endswith(name)), None)
            if teacher:
                teacher.availability = {d: [] for d in days}
                rhs = l.split("only available on ")[1]
                parts = [p.strip() for p in rhs.replace(";", ",").split(",") if p.strip()]
                for p in parts:
                    toks = p.split()
                    if not toks:
                        continue
                    d = toks[0]
                    ss = [s for s in toks[1:] if s in slot_names]
                    if d in teacher.availability:
                        if ss:
                            teacher.availability[d].extend(ss)
        if "taught by" in l and "needs" in l and "period" in l:
            subj = l.split(" taught by ")[0].strip()
            rest = l.split(" taught by ")[1]
            tname = rest.split(" needs ")[0].replace("Prof. ", "").strip()
            periods_str = rest.split(" needs ")[1].split()[0]
            teacher = next((t for t in teachers.values() if t.name.endswith(tname)), None)
            if subj in subjects and teacher:
                subjects[subj] = Subject(
                    id=subj,
                    name=subjects[subj].name,
                    teacher_id=teacher.id,
                    periods_per_week=int(periods_str),
                )
        if l.lower().startswith("prefer "):
            rhs = l[7:]
            subj = rhs.split(" on ")[0].strip()
            windows_str = rhs.split(" on ")[1].strip()
            wins = [w.strip() for w in windows_str.split(",")]
            preferred_windows[subj] = wins

    hard = HardConstraints(
        days=days,
        slots_per_day=slots_per_day,
        slot_names=slot_names,
        teachers=list(teachers.values()),
        subjects=list(subjects.values()),
        class_name=settings.CLASS_NAME,
        max_periods_per_day=None,
    )
    soft = SoftConstraints(
        minimize_gaps_weight=1.0,
        balance_subjects_across_days_weight=0.5,
        preferred_windows=preferred_windows,
        prefer_mornings_weight=0.0,
    )
    return ConstraintPackage(hard=hard, soft=soft)

def _gemini_parse(nl_constraints: List[str]) -> ConstraintPackage:
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set; using fallback rule-based parser.")
        return _fallback_rule_based_parser(nl_constraints)
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.MODEL_NAME)
        system_prompt = (
            "You are a constraint parser. Convert the user's natural language timetable rules "
            "into a JSON object that validates against this exact Pydantic schema:\n"
            "ConstraintPackage: {hard: HardConstraints, soft: SoftConstraints}\n"
            "HardConstraints: {days: List[str], slots_per_day: int, slot_names: List[str], "
            "teachers: List[Teacher], subjects: List[Subject], class_name: str, max_periods_per_day: Optional[int]}\n"
            "Teacher: {id: str, name: str, availability: Dict[str, List[str]]}\n"
            "Subject: {id: str, name: str, teacher_id: str, periods_per_week: int}\n"
            "SoftConstraints: {minimize_gaps_weight: float, balance_subjects_across_days_weight: float, "
            "prefer_mornings_weight: float, preferred_windows: Dict[str, List[str]]}\n"
            f"Default context: days=[{','.join(settings.DAYS)}], slots_per_day={settings.SLOTS_PER_DAY}, "
            f"slot_names=[{','.join([f'S{i+1}' for i in range(settings.SLOTS_PER_DAY)])}], class_name='{settings.CLASS_NAME}'. "
            "For teachers not mentioned in constraints, assume full availability across all days/slots. "
            "Return ONLY valid JSON matching this schema exactly."
        )
        user_prompt = "\n".join(nl_constraints)
        resp = model.generate_content([system_prompt, user_prompt])
        text = resp.text
        logger.info(f"Gemini raw response: {repr(text)}")
        import json
        # Extract JSON from markdown code blocks if present
        if text.strip().startswith('```json') and text.strip().endswith('```'):
            text = text.strip()[7:-3].strip()  # Remove ```json and ```
        elif text.strip().startswith('```') and text.strip().endswith('```'):
            text = text.strip()[3:-3].strip()  # Remove ``` and ```
        parsed: Dict[str, Any] = json.loads(text)
        cp = ConstraintPackage.model_validate(parsed)
        logger.info("Parsed constraints via Gemini")
        return cp
    except Exception as e:
        logger.warning(f"Gemini parse failed ({e}); using fallback parser.")
        return _fallback_rule_based_parser(nl_constraints)

class ConstraintParserAgent:
    def parse(self, nl_constraints: List[str]) -> ConstraintPackage:
        try:
            cp = _gemini_parse(nl_constraints)
            _ = ConstraintPackage.model_validate(cp.model_dump())
            return cp
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            raise
