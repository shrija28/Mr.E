"""Extract clean text page-by-page from NCERT textbook PDFs in backend/data/textbooks
and build clean FAISS vector stores & chunk files for ALL 4 Subjects:
Physics, Chemistry, Mathematics, and Biology.
"""

import json
import os
import re
from pathlib import Path
import fitz  # PyMuPDF
import faiss
from sentence_transformers import SentenceTransformer

textbooks_dir = Path("backend/data/textbooks")
faiss_dir = Path("backend/data/faiss")
faiss_dir.mkdir(parents=True, exist_ok=True)

print("Loading SentenceTransformer model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_subject_from_filename(filename: str) -> str:
    fn = filename.lower()
    # Map topic ranges or filename keywords
    if any(k in fn for k in ["physic", "motion", "gravitation", "thermodynamics", "electrostatic", "current_electricity", "optics", "wave", "atom", "nuclei", "semiconductor"]):
        # Check topic number if available
        m = re.search(r"topic_(\d+)_", fn)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 28:
                return "Physics"
            elif 29 <= num <= 58:
                return "Chemistry"
            elif 59 <= num <= 86:
                return "Mathematics"
            elif 87 <= num <= 124:
                return "Biology"
        return "Physics"
    elif any(k in fn for k in ["chem", "atom", "bonding", "equilibrium", "redox", "hydrocarbon", "solution", "electrochem", "kinetics", "block", "organic", "alcohol", "aldehyde", "amine", "polymer"]):
        return "Chemistry"
    elif any(k in fn for k in ["math", "trig", "vector", "matrix", "determinant", "integral", "derivative", "probability", "geometry", "linear", "conic", "relation"]):
        return "Mathematics"
    elif any(k in fn for k in ["bio", "plant", "animal", "cell", "reproduction", "genetics", "evolution", "health", "microbe", "ecosystem", "anatomy", "digestion", "respiration", "circulation", "excretory", "neural", "chemical_coordination"]):
        return "Biology"
    
    # Fallback by number range
    m = re.search(r"topic_(\d+)_", fn)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 28:
            return "Physics"
        elif 29 <= num <= 58:
            return "Chemistry"
        elif 59 <= num <= 86:
            return "Mathematics"
        elif 87 <= num <= 124:
            return "Biology"
            
    return "General"

subject_chunks = {
    "Physics": [],
    "Chemistry": [],
    "Mathematics": [],
    "Biology": []
}

pdf_files = list(textbooks_dir.glob("*.pdf"))
print(f"Found {len(pdf_files)} PDF textbook files in {textbooks_dir}.")

for pdf_path in pdf_files:
    subject = get_subject_from_filename(pdf_path.name)
    if subject not in subject_chunks:
        continue

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            t = page.get_text("text")
            # Filter out header/footer lines and OMR instructions
            clean_lines = [
                line.strip() for line in t.split("\n")
                if len(line.strip()) > 15
                and not re.search(r"(cet no|invigilator|omr|answer sheet|download|byju|vedantu)", line, re.IGNORECASE)
            ]
            full_text += " ".join(clean_lines) + " "

        # Chunk text into ~400 char windows
        words = full_text.split()
        chunk_size = 70
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            if len(chunk) > 100:
                subject_chunks[subject].append(f"[{pdf_path.stem}] {chunk}")

    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}")

# Build FAISS index & write chunks for each subject
for subject, chunks in subject_chunks.items():
    if not chunks:
        print(f"No chunks extracted for {subject}.")
        continue

    chunks_file = faiss_dir / f"{subject}.chunks.json"
    index_file = faiss_dir / f"{subject}.index"

    print(f"Writing {len(chunks)} clean text chunks for {subject} to {chunks_file}...")
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Building FAISS vector index for {subject} ({len(chunks)} chunks)...")
    # Subsample max 3000 chunks for vector index if too large
    indexed_chunks = chunks[:3000]
    vecs = embedder.encode(indexed_chunks, show_progress_bar=False).astype("float32")
    index = faiss.IndexFlatL2(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(index_file))
    print(f"✓ Saved {subject}.index ({len(indexed_chunks)} vectors).")

print("All subject textbooks cleanly indexed into FAISS stores!")
