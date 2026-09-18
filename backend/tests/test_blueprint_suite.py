"""Automated regression test suite for KCET 2026 Blueprint Engine, Quotas, Subtype Ratios and Topic Normalization."""

import pytest
from smartkcet.rag.blueprint import (
    KCET_BLUEPRINT_2026,
    SUBJECT_SUBTYPE_TARGETS,
    calculate_chapter_quotas,
    calculate_subtype_quotas,
    get_blueprint_chapter_info,
)
from smartkcet.rag.mcq_extractor import infer_question_subtype

def test_blueprint_chapter_counts_and_sums():
    for subject in ["Physics", "Chemistry", "Mathematics", "Biology"]:
        chapters = KCET_BLUEPRINT_2026.get(subject, [])
        assert len(chapters) > 0, f"No blueprint chapters defined for {subject}"
        
        quotas = calculate_chapter_quotas(subject, total_questions=60)
        assert sum(quotas.values()) == 60, f"Full quota sum for {subject} is {sum(quotas.values())}, expected 60"

def test_physics_calculation_ratio():
    quotas = calculate_subtype_quotas("Physics", total_questions=60)
    calc_total = quotas.get("direct_formula", 0) + quotas.get("multi_step", 0)
    calc_pct = (calc_total / 60) * 100
    assert 50.0 <= calc_pct <= 60.0, f"Physics calculations {calc_pct}% outside 50-60%"

def test_chemistry_numerical_ratio():
    quotas = calculate_subtype_quotas("Chemistry", total_questions=60)
    num_qs = quotas.get("physical_numerical", 0)
    assert 5 <= num_qs <= 8, f"Chemistry numericals {num_qs} outside 5-8 Qs range"

def test_proportional_normalization_of_uploaded_subset():
    uploaded_phys = [
        "Kinematics (Motion in Straight Line & Plane)",
        "Laws of Motion & Friction",
        "Thermodynamics & Kinetic Theory",
        "Electrostatics (Charges, Fields, Potential)",
        "Current Electricity"
    ]
    quotas = calculate_chapter_quotas("Physics", uploaded_topics=uploaded_phys, total_questions=60)
    assert sum(quotas.values()) == 60
    assert set(quotas.keys()) == set(uploaded_phys)

def test_subtype_classification():
    q_phys_num = "A body falls freely from rest under gravity g = 9.8 m/s^2. Calculate its speed after 3 seconds."
    assert infer_question_subtype(q_phys_num, ["10 m/s", "29.4 m/s", "50 m/s", "60 m/s"], "Physics") in ("direct_formula", "multi_step")

    q_phys_theory = "Define Lenz's law of conservation of energy."
    assert infer_question_subtype(q_phys_theory, ["A", "B", "C", "D"], "Physics") == "theory_definition"

    q_chem_num = "Calculate the molarity of 4g of NaOH in 250 mL of water."
    assert infer_question_subtype(q_chem_num, ["0.1 M", "0.4 M", "1.0 M", "2.0 M"], "Chemistry") == "physical_numerical"

    q_chem_fact = "When phenol reacts with zinc dust, it gives benzene."
    assert infer_question_subtype(q_chem_fact, ["Benzene", "Toluene", "Aniline", "Benzoic acid"], "Chemistry") == "fact_reaction"
