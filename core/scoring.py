from typing import Dict, List
from core.constraint_schema import Timetable, ConstraintPackage

def score_minimize_gaps(tt: Timetable) -> float:
    grid = tt.as_grid()
    penalty = 0
    for day, row in grid.items():
        taken = sorted([i for i, s in enumerate(tt.slot_names) if s in row])
        if not taken:
            continue
        if len(taken) > 1:
            first, last = taken[0], taken[-1]
            occupied = set(taken)
            for i in range(first, last + 1):
                if i not in occupied:
                    penalty += 1
    return -float(penalty)

def score_balance_subjects_across_days(tt: Timetable) -> float:
    from collections import defaultdict
    subj_daily: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a in tt.assignments:
        subj_daily[a.subject_id][a.day] += 1
    import statistics
    total = 0.0
    for subj, counts in subj_daily.items():
        arr: List[int] = []
        for d in tt.days:
            arr.append(counts.get(d, 0))
        if len(arr) > 1:
            try:
                var = statistics.pvariance(arr)
            except statistics.StatisticsError:
                var = 0.0
        else:
            var = 0.0
        total += var
    return -float(total)

def score_preferred_windows(tt: Timetable, preferred_windows: Dict[str, List[str]]) -> float:
    grid = tt.as_grid()
    reward = 0
    for subj, windows in preferred_windows.items():
        for w in windows:
            try:
                day, slot = w.split(":")
            except ValueError:
                continue
            if day in grid and slot in grid[day] and grid[day][slot].subject_id == subj:
                reward += 1
    return float(reward)

def score_timetable(tt: Timetable, constraints: ConstraintPackage) -> float:
    soft = constraints.soft
    s = 0.0
    s += soft.minimize_gaps_weight * score_minimize_gaps(tt)
    s += soft.balance_subjects_across_days_weight * score_balance_subjects_across_days(tt)
    if soft.preferred_windows:
        s += score_preferred_windows(tt, soft.preferred_windows)
    if soft.prefer_mornings_weight > 0:
        grid = tt.as_grid()
        bonus = 0.0
        for day in tt.days:
            if tt.slot_names and tt.slot_names[0] in grid[day]:
                bonus += 1.0
        s += soft.prefer_mornings_weight * bonus
    return s
