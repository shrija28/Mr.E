import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from smartkcet.main import create_app

def run_verification():
    print("=== Starting RAG & AI Analysis Verification ===")
    app = create_app()
    client = app.test_client()

    # 1. Admin Login
    print("\n--- 1. Admin Authentication ---")
    admin_login_res = client.post("/api/auth/admin/login", json={
        "email": "admin@mre.com",
        "password": "admin"
    })
    print(f"Admin login status: {admin_login_res.status_code}")
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.get_data(as_text=True)}"

    # 2. Create Exam with source="rag"
    print("\n--- 2. Creating Exam via RAG (Textbook & Syllabus Augmented) ---")
    exam_res = client.post("/api/admin/exams", json={
        "exam_name": "KCET Physics RAG AI Test",
        "subject": "Physics",
        "source": "rag",
        "is_published": True
    })
    print(f"Create RAG exam status: {exam_res.status_code}")
    assert exam_res.status_code == 200, f"Create RAG exam failed: {exam_res.get_data(as_text=True)}"
    exam_data = exam_res.get_json()
    print(f"Exam ID: {exam_data.get('exam_id')}")
    print(f"Exam Source: {exam_data.get('source')}")
    print(f"Sets created: {len(exam_data.get('set_ids', []))}")
    assert exam_data.get("source") == "rag", "Exam source should be 'rag'"
    assert len(exam_data.get("set_ids", [])) == 4, "Should create 4 sets (A, B, C, D)"

    first_set_id = exam_data["set_ids"][0]["exam_set_id"]
    print(f"First Set ID: {first_set_id}")

    # 3. Student Registration / Login
    print("\n--- 3. Student Authentication ---")
    # Try logging in with student account
    student_login = client.post("/api/auth/login", json={
        "email": "student_rag_test@mre.com",
        "password": "Password123!"
    })
    if student_login.status_code != 200:
        # Register if not existing
        reg_res = client.post("/api/auth/register", json={
            "email": "student_rag_test@mre.com",
            "password": "Password123!",
            "display_name": "KCET AI Test Student",
            "puc_year": "PUC-2",
            "target_year": 2026
        })
        print(f"Student register status: {reg_res.status_code}")
        student_login = client.post("/api/auth/login", json={
            "email": "student_rag_test@mre.com",
            "password": "Password123!"
        })
    print(f"Student login status: {student_login.status_code}")
    assert student_login.status_code == 200, "Student login must succeed"

    # 4. Fetch Questions for the Exam Set
    print("\n--- 4. Fetch Exam Set Questions ---")
    q_res = client.get(f"/api/student/exams/{first_set_id}")
    print(f"Fetch questions status: {q_res.status_code}")
    assert q_res.status_code == 200, f"Failed to fetch questions: {q_res.get_data(as_text=True)}"
    q_data = q_res.get_json()
    questions = q_data.get("questions", [])
    print(f"Fetched {len(questions)} questions for set {first_set_id}")
    assert len(questions) == 60, f"Expected 60 questions per set, got {len(questions)}"

    # 5. Submit Answers and Verify AI Answer Analysis
    print("\n--- 5. Submit Exam & Receive AI Answer Analysis ---")
    # Simulate student answering first 45 questions
    student_answers = {str(i): "0" for i in range(45)}  # Answer 0 for Q0 to Q44
    submit_res = client.post("/api/student/submit", json={
        "exam_set_id": first_set_id,
        "answers": student_answers,
        "time_taken_sec": 2400
    })
    print(f"Submit status: {submit_res.status_code}")
    assert submit_res.status_code == 200, f"Submission failed: {submit_res.get_data(as_text=True)}"
    submit_data = submit_res.get_json()

    print("\n--- 6. Verifying AI Analysis Structure ---")
    assert "ai_analysis" in submit_data, "Response must include 'ai_analysis' object!"
    ai_analysis = submit_data["ai_analysis"]

    # Verify Summary
    summary = ai_analysis.get("summary", {})
    print(f"AI Performance Band: {summary.get('performance_band')}")
    print(f"AI Pacing Assessment: {summary.get('pacing_assessment')}")
    print(f"AI Overall Verdict: {summary.get('overall_verdict')}")
    assert summary.get("performance_band") is not None, "Performance band must be present"
    assert summary.get("overall_verdict") is not None, "Overall verdict must be present"
    assert summary.get("total") == 60, f"Expected 60 total marks/questions, got {summary.get('total')}"

    # Verify Topic Breakdown
    topic_breakdown = ai_analysis.get("topic_breakdown", {})
    print(f"AI Topic Breakdown categories: {list(topic_breakdown.keys())}")
    assert len(topic_breakdown) > 0, "Topic breakdown must contain diagnosed topics"
    first_topic = next(iter(topic_breakdown.values()))
    print(f"Sample topic diagnostic: {first_topic}")
    assert "mastery_level" in first_topic, "Topic must contain mastery_level"

    # Verify Action Plan
    action_plan = ai_analysis.get("action_plan", [])
    print(f"AI Action Plan recommendations ({len(action_plan)} steps):")
    for step in action_plan[:3]:
        print(f"  - {step}")
    assert len(action_plan) > 0, "Action plan must provide study recommendations"

    # Verify Detailed Reviews (all 60 questions evaluated)
    detailed_reviews = ai_analysis.get("detailed_reviews", [])
    print(f"Detailed Question AI Reviews: {len(detailed_reviews)} questions reviewed")
    assert len(detailed_reviews) == 60, f"Expected 60 reviewed questions, got {len(detailed_reviews)}"
    q1 = detailed_reviews[0]
    print(f"Sample Question 1 AI Review:")
    print(f"  Q: {q1.get('question_text')[:60]}...")
    print(f"  Subtype: {q1.get('subtype')} ({q1.get('subtype_label')})")
    print(f"  Student Ans: {q1.get('student_answer')} | Correct Ans: {q1.get('correct_answer')}")
    print(f"  Is Correct: {q1.get('is_correct')}")
    print(f"  Concept Explanation: {q1.get('explanation')[:80]}...")
    print(f"  AI Diagnostic Insight: {q1.get('ai_insight')}")
    assert "explanation" in q1 and q1["explanation"], "Detailed review must include conceptual explanation"
    assert "ai_insight" in q1 and q1["ai_insight"], "Detailed review must include diagnostic insight"
    assert "subtype" in q1 and q1["subtype"], "Detailed review must include question subtype"
    assert "subtype_label" in q1 and q1["subtype_label"], "Detailed review must include subtype label"

    # Verify Blueprint Breakdown in Submission Response
    print("\n--- 7. Verifying Blueprint Calculation Breakdown in AI Response ---")
    subtype_breakdown = ai_analysis.get("subtype_breakdown", {})
    print(f"Subtype breakdown keys: {list(subtype_breakdown.keys())}")
    assert len(subtype_breakdown) > 0, "Subtype breakdown must contain categorized subtypes"
    blueprint_perf = ai_analysis.get("blueprint_performance", {})
    print(f"Blueprint performance: {blueprint_perf}")
    assert "calculation_accuracy_pct" in blueprint_perf or "numerical_accuracy_pct" in blueprint_perf, "Blueprint performance must contain calculation metrics"

    # 6. Direct Blueprint Quota Tests for Physics & Chemistry at 60 questions scale
    print("\n--- 8. Testing Blueprint Quotas at 60 Questions Scale in MCQ Generator ---")
    from smartkcet.rag.mcq_extractor import generate_fallback_mcqs

    # Physics Blueprint Check (60 questions)
    phys_qs = generate_fallback_mcqs(text="", topic="Physics", max_questions=60)
    assert len(phys_qs) == 60, f"Expected 60 physics questions, got {len(phys_qs)}"
    direct_cnt = sum(1 for q in phys_qs if q.get("subtype") == "direct_formula")
    multi_cnt = sum(1 for q in phys_qs if q.get("subtype") == "multi_step")
    theory_cnt = sum(1 for q in phys_qs if q.get("subtype") == "theory_definition")
    total_calc = direct_cnt + multi_cnt
    calc_pct = (total_calc / 60) * 100
    print(f"Physics MCQ Generation (60 questions):")
    print(f"  - Direct Formula: {direct_cnt} ({direct_cnt/60*100:.1f}%) [Blueprint target: ~30% to 40% (21/60 = 35%)]")
    print(f"  - Multi-Step: {multi_cnt} ({multi_cnt/60*100:.1f}%) [Blueprint target: ~15% to 20% (12/60 = 20%)]")
    print(f"  - Pure Theory: {theory_cnt} ({theory_cnt/60*100:.1f}%) [Blueprint target: ~40% to 50% (27/60 = 45%)]")
    print(f"  - Total Calculations: {total_calc} ({calc_pct:.1f}%) [Blueprint requirement: 50% to 60%]")

    assert 50 <= calc_pct <= 60, f"Physics calculations must be between 50% and 60%, got {calc_pct}%"
    assert 30 <= (direct_cnt / 60) * 100 <= 40, f"Direct formula must be ~30% to 40%, got {direct_cnt/60*100}%"
    assert 15 <= (multi_cnt / 60) * 100 <= 25, f"Multi-step must be ~15% to 20%, got {multi_cnt/60*100}%"
    assert 40 <= (theory_cnt / 60) * 100 <= 50, f"Pure theory must be ~40% to 50%, got {theory_cnt/60*100}%"

    # Chemistry Blueprint Check (60 questions)
    chem_qs = generate_fallback_mcqs(text="", topic="Chemistry", max_questions=60)
    assert len(chem_qs) == 60, f"Expected 60 chemistry questions, got {len(chem_qs)}"
    num_cnt = sum(1 for q in chem_qs if q.get("subtype") == "physical_numerical")
    fact_cnt = sum(1 for q in chem_qs if q.get("subtype") == "fact_reaction")
    num_pct = (num_cnt / 60) * 100
    fact_pct = (fact_cnt / 60) * 100
    print(f"\nChemistry MCQ Generation (60 questions):")
    print(f"  - Physical Numericals: {num_cnt} ({num_pct:.1f}%) [Blueprint target: 5 to 8 out of 60 (~8% to 12%)]")
    print(f"  - Direct Fact & Reactions: {fact_cnt} ({fact_pct:.1f}%) [Blueprint target: ~88% to 92% (54/60 = 90%)]")
    print(f"  - Total Calculations: {num_cnt} ({num_pct:.1f}%) [Blueprint requirement: 10% to 15%]")

    assert 8 <= num_pct <= 15, f"Chemistry numericals must be between ~8% and 15%, got {num_pct}%"
    assert 5 <= num_cnt <= 8, f"Chemistry numericals must be 5 to 8 questions out of 60, got {num_cnt}"
    assert 85 <= fact_pct <= 92, f"Chemistry facts/reactions must be between ~85% and 92%, got {fact_pct}%"

    print("\n✅ ALL 60-QUESTION BLUEPRINT & RAG VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()

