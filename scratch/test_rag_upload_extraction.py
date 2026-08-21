import sys
import json
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8')

from smartkcet.rag.mcq_extractor import extract_or_generate_mcqs

# Sample uploaded textbook text (Physics Projectile Motion concept)
sample_uploaded_text = """
Chapter: Motion in a Plane - Projectile Motion
A projectile is an object thrown into space upon which the only acting force is gravity. 
The horizontal velocity remains constant throughout the motion because no horizontal force acts on the projectile (neglecting air resistance).
The vertical component of velocity changes continuously under the acceleration due to gravity g = 9.8 m/s^2.
The time of flight T of a projectile launched with initial velocity u at an angle theta to the horizontal is given by T = (2 u sin theta) / g.
The maximum height H reached by the projectile is H = (u^2 sin^2 theta) / (2g).
The horizontal range R is given by R = (u^2 sin 2theta) / g. Range is maximum when the angle of projection theta = 45 degrees.
Example Problem: A ball is thrown with an initial velocity of 20 m/s at an angle of 30 degrees to the horizontal. Taking g = 10 m/s^2, the maximum height attained by the projectile is H = (20^2 * sin^2(30)) / (2*10) = (400 * 0.25) / 20 = 5 meters.
"""

print("--- TESTING RAG EXTRACTION ON UPLOADED TEXTBOOK TEXT ---")
results = extract_or_generate_mcqs(sample_uploaded_text, topic="Physics", min_questions=5)

print(f"\n[OK] Extracted {len(results)} MCQs grounded on the uploaded content:")
for idx, q in enumerate(results, 1):
    print(f"\nQ{idx}: {q['q']}")
    for opt_idx, opt in enumerate(q['opts']):
        print(f"  {chr(65+opt_idx)}. {opt}")
    print(f"  Correct Answer: {q['opts'][q['ans']] if isinstance(q['ans'], int) and q['ans'] < len(q['opts']) else q['ans']}")
    if q.get("exp"):
        print(f"  Explanation: {q['exp']}")
