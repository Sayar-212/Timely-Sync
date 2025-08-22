from timetable_backend.agents.constraint_parser import ConstraintParserAgent

def test_parser_basic():
    agent = ConstraintParserAgent()
    nl = [
        "Prof. Sharma is only available on Mon S1,S2, Tue S1",
        "Math taught by Prof. Sharma needs 2 periods",
        "Sci taught by Prof. Rao needs 2 periods",
        "Eng taught by Prof. Iyer needs 2 periods",
        "Prefer Math on Mon:S1, Tue:S1"
    ]
    cp = agent.parse(nl)
    assert cp.hard.days
    assert len(cp.hard.teachers) >= 3
    assert any(s.id == "Math" for s in cp.hard.subjects)
    assert "Math" in cp.soft.preferred_windows
