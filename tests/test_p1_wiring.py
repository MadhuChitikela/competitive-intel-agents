"""Verify P2 can import P1's tracer + judge."""


def test_p1_tracer_importable():
    from app.tracer import Tracer  # noqa: F401
    assert Tracer is not None


def test_p1_judge_importable():
    from app.judge import grade
    assert callable(grade)
