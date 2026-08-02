import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from smartkcet.db.base import Base
from smartkcet.student.recommendations import (
    map_score_to_rank_and_tier,
    calculate_match_type,
    redact_string,
    COLLEGES
)

def test_map_score_to_rank_and_tier():
    # Tier 1 score mapping (90-100)
    rank1, rng1, tier1 = map_score_to_rank_and_tier(95.0)
    assert tier1 == "Tier 1"
    assert rank1 > 0
    assert "-" in rng1

    # Tier 2 score mapping (75-90)
    rank2, rng2, tier2 = map_score_to_rank_and_tier(80.0)
    assert tier2 == "Tier 2"
    assert rank2 > rank1
    
    # Tier 3 score mapping (45-60)
    rank3, rng3, tier3 = map_score_to_rank_and_tier(50.0)
    assert tier3 == "Tier 3"
    assert rank3 > rank2
    
    # Tier 4 score mapping (<45)
    rank4, rng4, tier4 = map_score_to_rank_and_tier(35.0)
    assert tier4 == "Tier 4"
    assert rank4 > rank3


def test_calculate_match_type():
    # Safe match (projected rank is significantly better than cutoff, rank < 0.8 * cutoff)
    # rank = 500, cutoff = 1200 (0.8 * 1200 = 960)
    assert calculate_match_type(500, 1200) == "safe"

    # Target match (projected rank is close to cutoff, 0.8 * cutoff <= rank <= 1.2 * cutoff)
    # rank = 1000, cutoff = 1200
    assert calculate_match_type(1000, 1200) == "target"

    # Reach match (projected rank is worse than cutoff, rank > 1.2 * cutoff)
    # rank = 1500, cutoff = 1200 (1.2 * 1200 = 1440)
    assert calculate_match_type(1500, 1200) == "reach"


def test_redact_string():
    name = "RV College of Engineering"
    redacted = redact_string(name)
    assert redacted != name
    assert redacted.startswith("R")
    assert redacted.endswith("g")
    assert "*" in redacted
    assert len(redacted.split()) == len(name.split())


def test_api_recommendations_unauthorized():
    from fastapi.testclient import TestClient
    from smartkcet.main import app
    
    client = TestClient(app)
    response = client.get("/api/student/college-recommendations")
    assert response.status_code == 401
    assert "auth_required" in response.text

