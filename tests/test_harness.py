"""Tests for the eval harness structure (no live LLM calls)."""
import json
from pathlib import Path


def test_golden_dataset_exists():
    p = Path("evals/golden_dataset.json")
    assert p.exists()
    data = json.loads(p.read_text())
    assert len(data) >= 5


def test_golden_cases_have_required_fields():
    cases = json.loads(Path("evals/golden_dataset.json").read_text())
    for c in cases:
        assert "id" in c
        assert "company" in c
        assert "expected_sections" in c
        assert "expected_themes" in c
        assert "expected_min_threat_score" in c
