from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, validator

SlotName = str
DayName = str

class Teacher(BaseModel):
    id: str
    name: str
    availability: Dict[DayName, List[SlotName]] = Field(default_factory=dict)

class Subject(BaseModel):
    id: str
    name: str
    teacher_id: str
    periods_per_week: int

class Room(BaseModel):
    id: str
    name: str
    capacity: Optional[int] = None

class HardConstraints(BaseModel):
    days: List[DayName]
    slots_per_day: int
    slot_names: List[SlotName]
    teachers: List[Teacher]
    subjects: List[Subject]
    rooms: Optional[List[Room]] = None
    class_name: str = "Class A"
    max_periods_per_day: Optional[int] = None

    @validator("slot_names")
    def validate_slot_names(cls, v, values):
        spd = values.get("slots_per_day")
        if spd and len(v) != spd:
            raise ValueError("slot_names length must equal slots_per_day")
        return v

class SoftConstraints(BaseModel):
    minimize_gaps_weight: float = 1.0
    balance_subjects_across_days_weight: float = 0.5
    prefer_mornings_weight: float = 0.0
    preferred_windows: Dict[str, List[str]] = Field(default_factory=dict)

class ConstraintPackage(BaseModel):
    hard: HardConstraints
    soft: SoftConstraints

class AssignedCell(BaseModel):
    day: DayName
    slot: SlotName
    subject_id: str
    teacher_id: str

class Timetable(BaseModel):
    class_name: str
    days: List[DayName]
    slot_names: List[SlotName]
    assignments: List[AssignedCell]

    def as_grid(self) -> Dict[DayName, Dict[SlotName, AssignedCell]]:
        grid: Dict[DayName, Dict[SlotName, AssignedCell]] = {}
        for d in self.days:
            grid[d] = {}
        for a in self.assignments:
            grid[a.day][a.slot] = a
        return grid

class VerificationResult(BaseModel):
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class SolverResult(BaseModel):
    feasible_timetables: List[Timetable]
    status: Literal["FEASIBLE", "OPTIMAL", "INFEASIBLE", "UNKNOWN"]
