"""AI Answer Analysis and Diagnostic Evaluation Engine.

Provides deep AI-powered evaluation of student exam submissions:
- Diagnostic performance assessment (retention, accuracy, pacing).
- Topic-wise mastery classification (Mastered, Intermediate, Review Needed).
- Question-by-question solution breakdown with conceptual explanations.
- Actionable study recommendations and chapter review priorities.

Utilizes Groq LLM when available with a resilient rule-based analytical engine.
"""

from __future__ import annotations

import logging
import os
import json
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("smartkcet.rag.ai_analyzer")


def _is_correct(given: Any, ans: Any, opts: Any = None) -> bool:
    """Helper to check correctness matching smartkcet scoring logic."""
    if given is None or str(given).strip() == "":
        return False
    given_str = str(given).strip().lower()
    ans_str = str(ans).strip().lower() if ans is not None else ""

    if given_str == ans_str:
        return True

    letter_map = {"a": "0", "b": "1", "c": "2", "d": "3", "0": "0", "1": "1", "2": "2", "3": "3"}
    if letter_map.get(given_str) == letter_map.get(ans_str):
        return True

    if opts and isinstance(opts, (list, tuple)):
        try:
            g_idx = int(letter_map.get(given_str, given_str))
            if 0 <= g_idx < len(opts) and str(opts[g_idx]).strip().lower() == ans_str:
                return True
        except (ValueError, TypeError):
            pass

        try:
            a_idx = int(letter_map.get(ans_str, ans_str))
            if 0 <= a_idx < len(opts) and str(opts[a_idx]).strip().lower() == given_str:
                return True
        except (ValueError, TypeError):
            pass

        for idx, opt in enumerate(opts):
            if str(opt).strip().lower() == ans_str and str(idx) == letter_map.get(given_str, given_str):
                return True

    return False


def _get_option_index(value: Any, opts: list[str]) -> Optional[int]:
    """Resolve an option value (string, letter, or index) to an integer index (0-3)."""
    if value is None or str(value).strip() == "":
        return None
    val_str = str(value).strip().lower()
    letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "0": 0, "1": 1, "2": 2, "3": 3}
    if val_str in letter_map:
        return letter_map[val_str]
    for idx, opt in enumerate(opts):
        if str(opt).strip().lower() == val_str:
            return idx
    return None


def _synthesize_concept_explanation(q_text: str, topic: str, correct_opt: str) -> str:
    """Generate a clean conceptual explanation if the question lacks one."""
    topic_clean = topic if topic and topic != "General" else "KCET Core Concepts"
    return (
        f"Key Principle ({topic_clean}): The correct answer is '{correct_opt}'. "
        f"This directly follows from fundamental principles in {topic_clean}. "
        f"Make sure to review the core formulas and standard definitions for this topic."
    )


_SUBTYPE_LABELS = {
    "direct_formula": "⚡ Direct Formula Substitution",
    "multi_step": "🧩 Multi-Step Problem Solving",
    "theory_definition": "📖 Pure Theory & Definition",
    "physical_numerical": "🔢 Physical Chemistry Numerical",
    "fact_reaction": "🧪 Reaction & Memory Fact",
    "concept_application": "💡 Concept Application",
}


def generate_offline_ai_analysis(
    questions: List[Dict[str, Any]],
    answers: Dict[str, Any],
    score_data: Dict[str, Any],
    time_taken_sec: int,
    subject: str = "General",
) -> Dict[str, Any]:
    """Produce comprehensive structured AI analysis using pedagogical heuristics and KCET blueprint diagnostics."""
    from .mcq_extractor import infer_question_subtype

    total_questions = len(questions)
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    question_reviews = []
    topic_breakdown: Dict[str, Dict[str, int]] = {}
    subtype_stats: Dict[str, Dict[str, Any]] = {}

    for i, q in enumerate(questions):
        q_text = q.get("q", "")
        raw_opts = q.get("opts", [])
        opts = list(raw_opts) if isinstance(raw_opts, (list, tuple)) else []
        correct_ans_raw = q.get("ans", 0)
        topic = q.get("topic", "General") or "General"
        existing_exp = q.get("exp", "").strip()

        # Identify or infer question subtype
        subtype = q.get("subtype")
        if not subtype:
            subtype = infer_question_subtype(q_text, opts, subject)
        subtype_label = _SUBTYPE_LABELS.get(subtype, subtype.replace("_", " ").title())

        subtype_stats.setdefault(subtype, {
            "total": 0,
            "correct": 0,
            "label": subtype_label,
            "key": subtype
        })
        subtype_stats[subtype]["total"] += 1

        given_val = answers.get(str(i))
        correct = _is_correct(given_val, correct_ans_raw, opts)

        selected_idx = _get_option_index(given_val, opts)
        correct_idx = _get_option_index(correct_ans_raw, opts)
        if correct_idx is None:
            correct_idx = 0

        correct_opt_text = opts[correct_idx] if 0 <= correct_idx < len(opts) else str(correct_ans_raw)
        selected_opt_text = opts[selected_idx] if selected_idx is not None and 0 <= selected_idx < len(opts) else None

        topic_breakdown.setdefault(topic, {"earned": 0, "total": 0})
        topic_breakdown[topic]["total"] += 1

        if given_val is None or str(given_val).strip() == "":
            status = "unanswered"
            unanswered_count += 1
            ai_note = f"Question ({subtype_label}) was skipped. Review this area to build confidence under exam conditions."
        elif correct:
            status = "correct"
            correct_count += 1
            subtype_stats[subtype]["correct"] += 1
            topic_breakdown[topic]["earned"] += 1
            ai_note = f"Excellent execution! {subtype_label} solved with precision."
        else:
            status = "wrong"
            incorrect_count += 1
            ai_note = f"Misconception alert in {subtype_label}: You selected ({selected_opt_text or given_val}), but the verified concept points to '{correct_opt_text}'."

        explanation = existing_exp if existing_exp else _synthesize_concept_explanation(q_text, topic, correct_opt_text)

        question_reviews.append({
            "index": i + 1,
            "q": q_text,
            "options": opts,
            "selected_idx": selected_idx,
            "selected_text": selected_opt_text,
            "correct_idx": correct_idx,
            "correct_text": correct_opt_text,
            "is_correct": correct,
            "status": status,
            "topic": topic,
            "subtype": subtype,
            "subtype_label": subtype_label,
            "explanation": explanation,
            "ai_feedback": ai_note,
        })

    percentage = round((correct_count / max(1, total_questions)) * 100)

    # Subtype breakdown compilation
    subtype_breakdown_dict = {}
    for st_key, st_val in subtype_stats.items():
        st_pct = round((st_val["correct"] / max(1, st_val["total"])) * 100)
        subtype_breakdown_dict[st_key] = {
            "key": st_key,
            "label": st_val["label"],
            "total": st_val["total"],
            "correct": st_val["correct"],
            "accuracy_pct": st_pct,
        }

    # Blueprint high-level category calculations
    subj_lower = subject.lower()
    blueprint_performance: Dict[str, Any] = {}
    if "physic" in subj_lower:
        direct_st = subtype_stats.get("direct_formula", {"total": 0, "correct": 0})
        multi_st = subtype_stats.get("multi_step", {"total": 0, "correct": 0})
        theory_st = subtype_stats.get("theory_definition", {"total": 0, "correct": 0})

        calc_total = direct_st["total"] + multi_st["total"]
        calc_correct = direct_st["correct"] + multi_st["correct"]
        calc_pct = round((calc_correct / max(1, calc_total)) * 100) if calc_total > 0 else 0

        theory_total = theory_st["total"]
        theory_correct = theory_st["correct"]
        theory_pct = round((theory_correct / max(1, theory_total)) * 100) if theory_total > 0 else 0

        blueprint_performance = {
            "type": "physics",
            "calculation_total": calc_total,
            "calculation_correct": calc_correct,
            "calculation_accuracy_pct": calc_pct,
            "theory_total": theory_total,
            "theory_correct": theory_correct,
            "theory_accuracy_pct": theory_pct,
            "diagnosis": (
                f"Calculations: {calc_correct}/{calc_total} ({calc_pct}%) | "
                f"Pure Theory: {theory_correct}/{theory_total} ({theory_pct}%). "
                + ("Strong theoretical retention; prioritize speed and multi-step formula derivations."
                   if theory_pct >= calc_pct
                   else "Solid calculation foundation; strengthen memorization of theoretical laws and definitions.")
            )
        }
    elif "chem" in subj_lower:
        num_st = subtype_stats.get("physical_numerical", {"total": 0, "correct": 0})
        fact_st = subtype_stats.get("fact_reaction", {"total": 0, "correct": 0})

        num_total = num_st["total"]
        num_correct = num_st["correct"]
        num_pct = round((num_correct / max(1, num_total)) * 100) if num_total > 0 else 0

        fact_total = fact_st["total"]
        fact_correct = fact_st["correct"]
        fact_pct = round((fact_correct / max(1, fact_total)) * 100) if fact_total > 0 else 0

        blueprint_performance = {
            "type": "chemistry",
            "numerical_total": num_total,
            "numerical_correct": num_correct,
            "numerical_accuracy_pct": num_pct,
            "fact_reaction_total": fact_total,
            "fact_reaction_correct": fact_correct,
            "fact_reaction_accuracy_pct": fact_pct,
            "diagnosis": (
                f"Physical Numericals: {num_correct}/{num_total} ({num_pct}%) | "
                f"Reactions & Facts: {fact_correct}/{fact_total} ({fact_pct}%). "
                + ("Excellent numerical accuracy; dedicate revision to organic named reactions and inorganic trends."
                   if num_pct >= fact_pct
                   else "Good recall of chemical reactions; practice standard formula substitution in Solutions & Kinetics.")
            )
        }
    elif "math" in subj_lower:
        direct_st = subtype_stats.get("direct_formula", {"total": 0, "correct": 0})
        multi_st = subtype_stats.get("multi_step", {"total": 0, "correct": 0})
        concept_st = subtype_stats.get("concept_application", {"total": 0, "correct": 0})

        d_total = direct_st["total"]
        d_correct = direct_st["correct"]
        d_pct = round((d_correct / max(1, d_total)) * 100) if d_total > 0 else 0

        m_total = multi_st["total"] + concept_st["total"]
        m_correct = multi_st["correct"] + concept_st["correct"]
        m_pct = round((m_correct / max(1, m_total)) * 100) if m_total > 0 else 0

        blueprint_performance = {
            "type": "mathematics",
            "formula_total": d_total,
            "formula_correct": d_correct,
            "formula_accuracy_pct": d_pct,
            "multi_step_total": m_total,
            "multi_step_correct": m_correct,
            "multi_step_accuracy_pct": m_pct,
            "diagnosis": (
                f"Formula & Direct: {d_correct}/{d_total} ({d_pct}%) | "
                f"Multi-Step Calculus & Vectors: {m_correct}/{m_total} ({m_pct}%). "
                + ("Strong algebraic and formula accuracy; practice time management on multi-step integrals and 3D geometry."
                   if d_pct >= m_pct
                   else "Solid complex problem-solving; ensure basic trigonometric formulas and determinant shortcuts are fast.")
            )
        }
    elif "bio" in subj_lower:
        fact_st = subtype_stats.get("fact_reaction", {"total": 0, "correct": 0})
        theory_st = subtype_stats.get("theory_definition", {"total": 0, "correct": 0})
        concept_st = subtype_stats.get("concept_application", {"total": 0, "correct": 0})

        f_total = fact_st["total"]
        f_correct = fact_st["correct"]
        f_pct = round((f_correct / max(1, f_total)) * 100) if f_total > 0 else 0

        t_total = theory_st["total"] + concept_st["total"]
        t_correct = theory_st["correct"] + concept_st["correct"]
        t_pct = round((t_correct / max(1, t_total)) * 100) if t_total > 0 else 0

        blueprint_performance = {
            "type": "biology",
            "factual_total": f_total,
            "factual_correct": f_correct,
            "factual_accuracy_pct": f_pct,
            "conceptual_total": t_total,
            "conceptual_correct": t_correct,
            "conceptual_accuracy_pct": t_pct,
            "diagnosis": (
                f"Factual & Memory: {f_correct}/{f_total} ({f_pct}%) | "
                f"Conceptual & Physiology: {t_correct}/{t_total} ({t_pct}%). "
                + ("High factual recall; focus review on multi-step genetics crosses and hormonal feedback loops."
                   if f_pct >= t_pct
                   else "Strong physiological comprehension; revise specific anatomical terms, examples, and NCERT scientists.")
            )
        }

    # Determine performance band
    if percentage >= 85:
        band = "Outstanding Mastery"
        summary_text = (
            f"Exceptional performance in {subject}! You demonstrated strong command across core theoretical concepts "
            f"and numerical problem-solving. Maintain this consistency with targeted time-bound mock sessions."
        )
    elif percentage >= 65:
        band = "Proficient & Competent"
        summary_text = (
            f"Solid understanding of {subject} fundamentals. While your core concepts are sound, a few errors in "
            f"intermediate topics cost crucial marks. Focused revision on weak topics will easily push you above 85%."
        )
    elif percentage >= 40:
        band = "Developing Foundation"
        summary_text = (
            f"Moderate performance in {subject}. You have a basic grasp of the concepts, but accuracy drops in "
            f"multi-step applications. Strengthen your chapter formulas and practice standard previous year questions."
        )
    else:
        band = "Needs Comprehensive Revision"
        summary_text = (
            f"Your score indicates foundational conceptual gaps in {subject}. Prioritize thorough textbook reading "
            f"and high-yield summary notes before attempting full-length timed tests."
        )

    # Pacing analysis
    avg_time_per_q = round(time_taken_sec / max(1, total_questions), 1)
    if avg_time_per_q < 40:
        pacing_note = f"Rapid answering pace (~{avg_time_per_q}s/question). Be careful not to rush through questions with negative marking traps."
    elif avg_time_per_q <= 90:
        pacing_note = f"Balanced pacing (~{avg_time_per_q}s/question). Excellent time discipline suited for the actual KCET examination."
    else:
        pacing_note = f"Slower pacing (~{avg_time_per_q}s/question). Practice rapid calculation techniques and formula shortcuts to finish comfortably within the 60-minute limit."

    # Topic insights
    topic_insights = []
    action_plan = []
    for topic, stats in topic_breakdown.items():
        t_pct = round((stats["earned"] / max(1, stats["total"])) * 100)
        if t_pct >= 75:
            t_status = "Mastered"
            t_feed = "High accuracy. Keep revising periodic formulas to retain edge."
        elif t_pct >= 50:
            t_status = "Intermediate"
            t_feed = "Fair grasp. Review numerical examples and edge cases."
            action_plan.append({
                "priority": "Medium",
                "topic": topic,
                "action": f"Review key NCERT examples and summary points in {topic}."
            })
        else:
            t_status = "Review Needed"
            t_feed = "Conceptual gap detected. Must re-read textbook chapter."
            action_plan.append({
                "priority": "High",
                "topic": topic,
                "action": f"Deep-dive into textbook theory and solve 15-20 practice MCQs for {topic}."
            })

        topic_insights.append({
            "topic": topic,
            "earned": stats["earned"],
            "total": stats["total"],
            "percentage": t_pct,
            "status": t_status,
            "feedback": t_feed,
        })

    # Sort topic insights: weak first
    topic_insights.sort(key=lambda x: x["percentage"])

    if not action_plan:
        action_plan.append({
            "priority": "Maintenance",
            "topic": subject,
            "action": "Take full-syllabus mixed practice tests to reinforce endurance and accuracy."
        })

    # Build topic_breakdown dictionary format for easy frontend & API consumption
    topic_breakdown_dict = {}
    for ti in topic_insights:
        topic_breakdown_dict[ti["topic"]] = {
            "total": ti["total"],
            "correct": ti["earned"],
            "accuracy_pct": ti["percentage"],
            "mastery_level": ti["status"],
        }

    # Build detailed_reviews with normalized field names
    detailed_reviews = []
    for qr in question_reviews:
        detailed_reviews.append({
            "question_number": qr["index"],
            "question_text": qr["q"],
            "student_answer": qr["selected_text"] or ("Option " + str(qr["selected_idx"] + 1) if qr["selected_idx"] is not None else "Not Answered"),
            "correct_answer": qr["correct_text"],
            "student_option_index": qr["selected_idx"],
            "correct_option_index": qr["correct_idx"],
            "is_correct": qr["is_correct"],
            "is_unanswered": qr["status"] == "unanswered",
            "topic": qr["topic"],
            "subtype": qr["subtype"],
            "subtype_label": qr["subtype_label"],
            "explanation": qr["explanation"],
            "ai_insight": qr["ai_feedback"],
            "options": qr.get("options", []),
        })

    # Simple string list for action_plan
    action_plan_strings = [item["action"] for item in action_plan]

    return {
        "summary": {
            "score": correct_count,
            "total": total_questions,
            "percentage": percentage,
            "performance_band": band,
            "assessment": summary_text,
            "overall_verdict": summary_text,
            "accuracy_pct": percentage,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unanswered_count": unanswered_count,
            "time_taken_sec": time_taken_sec,
            "avg_time_per_question": avg_time_per_q,
            "pacing_evaluation": pacing_note,
            "pacing_assessment": pacing_note,
            "subtype_breakdown": subtype_breakdown_dict,
            "blueprint_performance": blueprint_performance,
            "blueprint_diagnosis": blueprint_performance.get("diagnosis", ""),
        },
        "topic_insights": topic_insights,
        "topic_breakdown": topic_breakdown_dict,
        "subtype_breakdown": subtype_breakdown_dict,
        "blueprint_performance": blueprint_performance,
        "question_reviews": question_reviews,
        "detailed_reviews": detailed_reviews,
        "action_plan": action_plan_strings,
        "action_plan_items": action_plan,
        "ai_engine": "SmartKCET Pedagogical AI",
    }


def analyze_student_submission(
    questions: List[Dict[str, Any]],
    answers: Dict[str, Any],
    score_data: Dict[str, Any],
    time_taken_sec: int,
    subject: str = "General",
) -> Dict[str, Any]:
    """Analyze student answers and return comprehensive AI diagnostic insights.
    
    Tries Groq LLM if configured; seamlessly falls back to the deterministic AI engine.
    """
    base_analysis = generate_offline_ai_analysis(
        questions=questions,
        answers=answers,
        score_data=score_data,
        time_taken_sec=time_taken_sec,
        subject=subject,
    )

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key.startswith("your-") or api_key == "sk-xxx":
        return base_analysis

    try:
        from .groq_client import get_groq_client, create_chat_completion_with_fallback
        client = get_groq_client()

        incorrect_topics = [
            t["topic"] for t in base_analysis["topic_insights"] if t["percentage"] < 60
        ]
        strong_topics = [
            t["topic"] for t in base_analysis["topic_insights"] if t["percentage"] >= 75
        ]

        prompt = f"""You are a master KCET tutor and pedagogical AI examiner.
Analyze the following student performance in {subject}:
- Total Questions: {len(questions)}
- Score: {base_analysis['summary']['correct_count']} / {len(questions)} ({base_analysis['summary']['accuracy_pct']}%)
- Time Taken: {time_taken_sec} seconds (~{base_analysis['summary']['avg_time_per_question']}s/question)
- Strong Topics: {', '.join(strong_topics) if strong_topics else 'None'}
- Topics with Mistakes: {', '.join(incorrect_topics) if incorrect_topics else 'None'}

Provide:
1. A concise 2-3 sentence diagnostic paragraph assessing their conceptual strengths and exact areas where they made mistakes.
2. 3 bullet points of high-impact strategic advice for this student to boost their KCET rank.

Format your output as valid JSON with keys:
{{
  "assessment": "...",
  "tips": ["tip1", "tip2", "tip3"]
}}
"""
        response = create_chat_completion_with_fallback(
            client=client,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )

        content = response.choices[0].message.content.strip()
        cleaned = re.sub(r"^```(?:json|)\n?", "", content, flags=re.MULTILINE)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        data = json.loads(cleaned)
        if isinstance(data, dict):
            if data.get("assessment"):
                base_analysis["summary"]["assessment"] = data["assessment"].strip()
            if data.get("tips") and isinstance(data["tips"], list):
                base_analysis["action_plan"] = [
                    {"priority": "High" if i == 0 else "Medium", "topic": subject, "action": tip}
                    for i, tip in enumerate(data["tips"][:4])
                ]
            base_analysis["ai_engine"] = "Groq Llama 3.3 + SmartKCET RAG"
    except Exception as exc:
        logger.info("Groq LLM assessment enrichment skipped (%s), using native pedagogical AI", exc)

    return base_analysis
