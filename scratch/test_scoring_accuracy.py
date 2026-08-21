import sys
sys.path.insert(0, 'backend')

from smartkcet.submissions.scoring import score_submission

test_questions = [
    {
        "q": "What is 2 + 2?",
        "opts": ["3", "4", "5", "6"],
        "ans": "1",  # index 1
        "topic": "Math",
        "marks": 1
    },
    {
        "q": "What is the capital of France?",
        "opts": ["London", "Berlin", "Paris", "Rome"],
        "ans": "B",  # letter B (index 1... wait, Paris is index 2. If ans='Paris')
        "ans": "Paris",  # option text
        "topic": "GK",
        "marks": 1
    },
    {
        "q": "Maximum height of projectile launched at 20m/s at 30 deg?",
        "opts": ["2.5 m", "5 m", "7.5 m", "10 m"],
        "ans": "5 m",  # option text for index 1
        "topic": "Physics",
        "marks": 1
    },
    {
        "q": "SI unit of force?",
        "opts": ["Joule", "Watt", "Newton", "Pascal"],
        "ans": "C",  # letter C for index 2
        "topic": "Physics",
        "marks": 1
    },
    {
        "q": "Genotypic ratio of monohybrid F2?",
        "opts": ["3:1", "1:2:1", "9:3:3:1", "1:1"],
        "ans": 1,  # integer 1
        "topic": "Biology",
        "marks": 1
    }
]

# Student answers all 5 correctly:
# Q0: index 1 ("4")
# Q1: index 2 ("Paris")
# Q2: index 1 ("5 m")
# Q3: index 2 ("Newton")
# Q4: index 1 ("1:2:1")
student_answers = {
    "0": 1,
    "1": 2,
    "2": 1,
    "3": 2,
    "4": 1
}

result = score_submission(test_questions, student_answers)

print("\n--- SCORING ACCURACY TEST RESULT ---")
print(f"Earned: {result['earned']} / {result['total']}")
print(f"Percentage: {result['percentage']}%")
print(f"Pass Flag: {result['pass']}")
print(f"Question Results:")
for idx, qr in enumerate(result['questionResults']):
    print(f"  Q{idx+1}: Status={qr['status']}, Given={qr['given']}, Correct={qr['correctAns']}, Earned={qr['earned']}")

assert result['percentage'] == 100, f"Expected 100%, got {result['percentage']}%"
assert result['earned'] == 5, f"Expected 5, got {result['earned']}"
print("\n[SUCCESS] 100% ACCURATE SCORING VERIFIED FOR ALL ANSWER FORMATS!")
