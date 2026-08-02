import pytest
from fastapi.testclient import TestClient
from smartkcet.main import app
from smartkcet.student.rank_suggestions import (
    generate_personalized_suggestions,
    redact_string
)

def test_redact_string():
    text = "Focus on Physics"
    redacted = redact_string(text)
    assert redacted != text
    assert len(redacted.split()) == len(text.split())
    # Preserves first and last letter of each word
    words = redacted.split()
    assert words[0].startswith("F") and words[0].endswith("s")
    assert words[1].startswith("o")
    assert words[2].startswith("P") and words[2].endswith("s")

def test_generate_suggestions_already_reached():
    # User is rank 5, desires rank 10
    suggestions = generate_personalized_suggestions(
        current_rank=5,
        desired_rank=10,
        avg_score=85.0,
        attempts=5,
        scores=[80.0, 90.0, 85.0, 82.0, 88.0],
        std_dev=3.5,
        subject_scores={"Physics": 85.0, "Chemistry": 85.0},
        weak_topics=[],
        max_attempts_in_cohort=10,
        current_composite=75.0,
        target_composite=65.0,
        is_locked=False
    )
    assert len(suggestions) > 0
    assert any("already better than or equal to" in s for s in suggestions)

def test_generate_suggestions_not_eligible():
    # User is not eligible (current_rank is None because avg_score < 30%)
    suggestions = generate_personalized_suggestions(
        current_rank=None,
        desired_rank=10,
        avg_score=25.0,
        attempts=2,
        scores=[20.0, 30.0],
        std_dev=5.0,
        subject_scores={"Physics": 25.0},
        weak_topics=[],
        max_attempts_in_cohort=10,
        current_composite=0.0,
        target_composite=55.0,
        is_locked=False
    )
    assert len(suggestions) > 0
    assert any("below the leaderboard eligibility threshold" in s for s in suggestions)

def test_generate_suggestions_has_gap():
    # User is rank 50, wants rank 10. Cohort max attempts = 10.
    suggestions = generate_personalized_suggestions(
        current_rank=50,
        desired_rank=10,
        avg_score=60.0,
        attempts=4,
        scores=[55.0, 65.0, 60.0, 60.0],
        std_dev=3.5,
        subject_scores={"Physics": 50.0, "Mathematics": 70.0},
        weak_topics=[("Calculus", 45.0)],
        max_attempts_in_cohort=10,
        current_composite=52.0,
        target_composite=64.0,
        is_locked=False
    )
    assert len(suggestions) > 0
    assert any("composite score gap" in s for s in suggestions)
    assert any("weakest subject" in s for s in suggestions)
    # Check weak topic suggestion
    assert any("Calculus" in s for s in suggestions)

def test_generate_suggestions_locked():
    # User is trial/free (locked)
    suggestions = generate_personalized_suggestions(
        current_rank=50,
        desired_rank=10,
        avg_score=60.0,
        attempts=4,
        scores=[55.0, 65.0, 60.0, 60.0],
        std_dev=3.5,
        subject_scores={"Physics": 50.0, "Mathematics": 70.0},
        weak_topics=[("Calculus", 45.0)],
        max_attempts_in_cohort=10,
        current_composite=52.0,
        target_composite=64.0,
        is_locked=True
    )
    assert len(suggestions) > 0
    # Every regular item should contain redact asterisks
    for s in suggestions[:-1]:
        assert "*" in s
    # The last item should be the upgrade prompt
    assert "Upgrade to Pro" in suggestions[-1]

def test_api_suggestions_unauthorized():
    client = TestClient(app)
    response = client.get("/api/student/rank-suggestions?desired_rank=10")
    assert response.status_code == 401
    assert "auth_required" in response.text
