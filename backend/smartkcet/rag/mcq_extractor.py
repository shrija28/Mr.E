"""Extract MCQ questions from text using pattern matching and domain validation.

Looks for patterns like:
- "1. Question text\n  a) option1\n  b) option2\n  c) option3\n  d) option4"
- "Q1: Question text\n  A. option1\n  B. option2\n  C. option3\n  D. option4"
- Numbered questions with lettered options (A/B/C/D or a/b/c/d or 1/2/3/4)

Includes strict domain-relevance filtering and authentic subject question banks
for Physics, Chemistry, Mathematics, and Biology.
"""

from __future__ import annotations

import logging
import random
import re
from typing import List, Optional

logger = logging.getLogger("smartkcet.rag.mcq_extractor")

# ---------------------------------------------------------------------------
# Pattern-based MCQ extraction
# ---------------------------------------------------------------------------

_Q_NUM_RE = re.compile(
    r"^(?:Q\.?\s*)?(\d{1,3})\s*[.):\-]\s*",
    re.IGNORECASE,
)

_OPT_RE = re.compile(
    r"^\s*(?:\(?([A-Da-d])\)?[.):\-]\s*|([A-Da-d])\s*[.):\-]\s*)",
)

_OPT_NUM_RE = re.compile(
    r"^\s*(?:\(?([1-4])\)?[.):\-]\s*|([1-4])\s*[.):\-]\s*)",
)

_ANS_KEY_RE = re.compile(
    r"(?:^|\n)\s*(\d{1,3})\s*[.):\-]\s*([A-Da-d1-4])\b",
)

_INLINE_ANS_RE = re.compile(
    r"(?:answer|ans|correct)\s*[:=]\s*([A-Da-d1-4])\b",
    re.IGNORECASE,
)

# Junk OMR / Platform header filters
_OMR_JUNK_PATTERNS = [
    r"omr\s*answer\s*sheet", r"invigilator", r"cet\s*no", r"question\b.*booklet",
    r"candidates?\s*can\s*download", r"paper\s*with\s*solutions", r"byju", r"vedantu",
    r"unacademy", r"allen", r"aakash", r"topperlearning", r"doubtnut", r"physicswallah",
    r"which statement about '", r"which of the following is correct regarding the topic"
]

# ---------------------------------------------------------------------------
# Domain & Relevance Validation
# ---------------------------------------------------------------------------

_BIOLOGY_TERMS = {
    "nephron", "cotyledon", "endosperm", "meristem", "vitellogenesis", "rhinitis",
    "chloroplast", "stomata", "erythrocyte", "leucocyte", "blood group", "follicle",
    "oogenesis", "spermatocyte", "graafian", "plasmodesmata", "sclerenchyma", "cambium",
    "vermicomposting", "pollen", "anther", "stigma", "androecium", "corolla", "calyx",
    "caterpillar", "silkworm", "pebrine", "hepatectomy", "prothrombin", "thrombin",
    "xylem", "phloem", "mitosis", "meiosis", "organelle", "gastrointestinal", "urinary",
    "paramecium", "amoeba", "dermatogen", "myosin", "actin", "sarcomere", "kidney",
    "heart wood", "alburnum", "monocistronic", "rubisco", "calvin cycle"
}

_PHYSICS_TERMS = {
    "velocity", "acceleration", "force", "mass", "momentum", "torque", "energy",
    "power", "work", "friction", "gravity", "gravitational", "shm", "pendulum",
    "wave", "frequency", "wavelength", "amplitude", "refraction", "reflection",
    "lens", "mirror", "focal", "prism", "diffraction", "interference", "charge",
    "coulomb", "electric", "voltage", "current", "resistor", "resistance",
    "capacitor", "capacitance", "magnetic", "field", "flux", "induction",
    "inductance", "alternating", "impedance", "reactance", "transformer",
    "photoelectric", "photon", "work function", "de broglie", "half-life",
    "decay", "diode", "transistor", "semiconductor", "pn junction", "pressure",
    "thermodynamics", "entropy", "isothermal", "adiabatic", "calorimetry",
    "viscosity", "surface tension", "bernoulli", "young's modulus", "kepler"
}


def is_valid_question(q_text: str, options: List[str], subject: str = "General") -> bool:
    """Return True if question text and options represent a valid, complete, clean question."""
    if not q_text or not isinstance(q_text, str):
        return False

    q_clean = q_text.strip()
    if len(q_clean) < 15 or len(q_clean.split()) < 4 or q_clean.isdigit():
        return False

    q_lower = q_clean.lower()

    # Reject truncated fragment questions like "is equal to", "the value of", etc.
    incomplete_patterns = [
        r"^(the\s+)?value\s+of\s*$",
        r"^(is\s+)?equal\s+to\s*$",
        r"^(the\s+)?value\s+of\s+x\s+if\s+is\s+",
        r"^(is\s+)?given\s+by\s*$",
        r"^(which\s+of\s+the\s+following\s*)?is:?\s*$",
        r"^equal\s+to",
        r"_\s*equal\s+to",
    ]
    for pattern in incomplete_patterns:
        if re.search(pattern, q_lower):
            return False

    if q_lower in ["is equal to", "equal to", "is given by", "value of", "the value of", "is:"]:
        return False

    # Options validation: must have exactly 4 non-empty, distinct options
    if not isinstance(options, list) or len(options) != 4:
        return False

    cleaned_opts = [str(opt).strip() for opt in options if opt and isinstance(opt, (str, int, float)) and len(str(opt).strip()) > 0]
    if len(cleaned_opts) != 4:
        return False

    # Ensure options are unique within the question
    if len(set(opt.lower() for opt in cleaned_opts)) < 4:
        return False

    full_text = (q_clean + " " + " ".join(cleaned_opts)).lower()

    # Reject OMR instructions, platform banners, or truncation pseudo-questions
    for pattern in _OMR_JUNK_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            return False

    # Subject specific checks
    if subject.lower() == "physics":
        bio_matches = sum(1 for term in _BIOLOGY_TERMS if term in full_text)
        if bio_matches >= 2:
            return False
        has_physics_term = any(term in full_text for term in _PHYSICS_TERMS)
        has_numerical = bool(re.search(r"\b\d+(\.\d+)?\s*(m/s|ms\^-1|m/s\^2|n|j|w|v|a|hz|kg|cm|mm|µc|uf|pf|ohm|omega|t|h|ev)\b", full_text, re.IGNORECASE))
        has_math_formula = bool(re.search(r"[\d\.\+\-\*/=]{3,}", full_text))
        return has_physics_term or has_numerical or has_math_formula

    return True


def is_valid_physics_question(q_text: str, options: List[str]) -> bool:
    return is_valid_question(q_text, options, subject="Physics")


# ---------------------------------------------------------------------------
# High-Quality Question Banks for ALL 4 Subjects
# ---------------------------------------------------------------------------

PHYSICS_NUMERICAL_BANK: List[dict] = [
    {
        "q": "A car starting from rest accelerates uniformly at a rate of 2 m/s² for 10 s. What is the total distance traveled by the car?",
        "opts": ["50 m", "100 m", "150 m", "200 m"],
        "ans": 1,
        "topic": "Motion in a Straight Line",
        "exp": "Using s = ut + (1/2)at², with u = 0, a = 2 m/s², t = 10 s: s = 0 + 0.5 * 2 * 100 = 100 m."
    },
    {
        "q": "A body of mass 5 kg is dropped from a height of 20 m. Taking g = 10 m/s², the velocity of the body just before striking the ground is:",
        "opts": ["10 m/s", "20 m/s", "30 m/s", "40 m/s"],
        "ans": 1,
        "topic": "Motion in a Straight Line",
        "exp": "Using v² = u² + 2gh, v² = 0 + 2(10)(20) = 400 => v = 20 m/s."
    },
    {
        "q": "A projectile is thrown with an initial velocity of 20 m/s at an angle of 30° with the horizontal. The maximum height attained by it is (g = 10 m/s²):",
        "opts": ["2.5 m", "5.0 m", "7.5 m", "10.0 m"],
        "ans": 1,
        "topic": "Motion in a Plane",
        "exp": "H_max = (u sin θ)² / (2g) = (20 * 0.5)² / (2 * 10) = 100 / 20 = 5.0 m."
    },
    {
        "q": "A force of 20 N acts on a body of mass 4 kg initially at rest. The work done by the force in 3 seconds is:",
        "opts": ["150 J", "225 J", "450 J", "900 J"],
        "ans": 2,
        "topic": "Laws of Motion & Work Energy",
        "exp": "a = F/m = 20/4 = 5 m/s². Displacement in 3 s: s = 0.5 * 5 * 9 = 22.5 m. Work = F * s = 20 * 22.5 = 450 J."
    },
    {
        "q": "If the momentum of a body is increased by 50%, its kinetic energy increases by:",
        "opts": ["50%", "100%", "125%", "150%"],
        "ans": 2,
        "topic": "Work, Energy and Power",
        "exp": "K = p²/(2m). If p becomes 1.5p, K becomes (1.5)² K = 2.25 K, an increase of 125%."
    },
    {
        "q": "The acceleration due to gravity at a height equal to the radius of Earth (R) above the Earth's surface is:",
        "opts": ["g/2", "g/3", "g/4", "g/9"],
        "ans": 2,
        "topic": "Gravitation",
        "exp": "g' = g (R / (R + h))² = g (R / 2R)² = g/4."
    },
    {
        "q": "The escape velocity from the surface of Earth is 11.2 km/s. If a planet has 4 times the mass and double the radius of Earth, its escape velocity is:",
        "opts": ["11.2 km/s", "15.8 km/s", "22.4 km/s", "31.6 km/s"],
        "ans": 1,
        "topic": "Gravitation",
        "exp": "v_e = √(2GM/R). For M'=4M and R'=2R: v_e' = √(4/2) v_e = √2 * 11.2 ≈ 15.8 km/s."
    },
    {
        "q": "Two point charges +4 µC and +16 µC are separated by a distance of 12 cm. The distance from the +4 µC charge where the net electric field is zero is:",
        "opts": ["3 cm", "4 cm", "6 cm", "8 cm"],
        "ans": 1,
        "topic": "Electric Charges and Fields",
        "exp": "q1/x² = q2/(d-x)². √(q2/q1) = (d-x)/x => √(16/4) = 2 = (12-x)/x => 2x = 12-x => 3x = 12 => x = 4 cm."
    },
    {
        "q": "Three capacitors of capacitance 6 µF each are connected in series across a 12 V battery. The charge on each capacitor is:",
        "opts": ["12 µC", "24 µC", "36 µC", "72 µC"],
        "ans": 1,
        "topic": "Electrostatic Potential and Capacitance",
        "exp": "C_eq = 6/3 = 2 µF in series. Charge Q = C_eq * V = 2 µF * 12 V = 24 µC."
    },
    {
        "q": "A wire of resistance 16 Ω is cut into 4 equal pieces and connected in parallel. The equivalent resistance of the combination is:",
        "opts": ["1 Ω", "2 Ω", "4 Ω", "8 Ω"],
        "ans": 0,
        "topic": "Current Electricity",
        "exp": "Each piece has resistance 16/4 = 4 Ω. Connected in parallel: R_eq = 4/4 = 1 Ω."
    },
    {
        "q": "A cell of emf 1.5 V and internal resistance 0.5 Ω is connected across an external resistance of 2.5 Ω. The potential difference across the cell terminals is:",
        "opts": ["1.0 V", "1.25 V", "1.35 V", "1.5 V"],
        "ans": 1,
        "topic": "Current Electricity",
        "exp": "I = E / (R + r) = 1.5 / (2.5 + 0.5) = 0.5 A. Terminal V = E - I*r = 1.5 - (0.5 * 0.5) = 1.25 V."
    },
    {
        "q": "A circular coil of 100 turns and radius 5 cm carries a current of 1 A. The magnetic field at the center of the coil is (µ₀ = 4π × 10⁻⁷ T·m/A):",
        "opts": ["4π × 10⁻⁴ T", "2π × 10⁻⁴ T", "4π × 10⁻⁵ T", "2π × 10⁻⁵ T"],
        "ans": 0,
        "topic": "Moving Charges and Magnetism",
        "exp": "B = (µ₀ N I) / (2 R) = (4π×10⁻⁷ * 100 * 1) / (2 * 0.05) = 4π × 10⁻⁴ T."
    },
    {
        "q": "An AC voltage V = 200 sin(100π t) is applied across a 50 Ω resistor. The RMS value of current flowing through the resistor is:",
        "opts": ["2 A", "2.83 A", "4 A", "5.66 A"],
        "ans": 1,
        "topic": "Alternating Current",
        "exp": "V_peak = 200 V => V_rms = 200 / √2 ≈ 141.4 V. I_rms = V_rms / R = 141.4 / 50 ≈ 2.83 A."
    },
    {
        "q": "In a pure inductive circuit of L = 0.1 H connected to 220 V, 50 Hz AC supply, the inductive reactance X_L is approximately:",
        "opts": ["15.7 Ω", "31.4 Ω", "62.8 Ω", "100 Ω"],
        "ans": 1,
        "topic": "Alternating Current",
        "exp": "X_L = 2π f L = 2 * 3.1416 * 50 * 0.1 = 31.4 Ω."
    },
    {
        "q": "A convex lens of focal length 20 cm is placed in contact with a concave lens of focal length 40 cm. The focal length of the combination is:",
        "opts": ["+20 cm", "+40 cm", "-20 cm", "-40 cm"],
        "ans": 1,
        "topic": "Ray Optics",
        "exp": "1/F = 1/f1 + 1/f2 = 1/20 - 1/40 = 1/40 => F = +40 cm."
    },
    {
        "q": "The speed of light in a medium is 2 × 10⁸ m/s. The refractive index of the medium relative to vacuum is (c = 3 × 10⁸ m/s):",
        "opts": ["1.25", "1.33", "1.50", "1.75"],
        "ans": 2,
        "topic": "Ray Optics",
        "exp": "n = c / v = (3 × 10⁸) / (2 × 10⁸) = 1.50."
    },
    {
        "q": "In Young's double slit experiment, if the distance between the slits is reduced to half and the screen distance is doubled, the fringe width becomes:",
        "opts": ["Unchanged", "Doubled", "Halved", "4 times"],
        "ans": 3,
        "topic": "Wave Optics",
        "exp": "Fringe width β = λD/d. If D' = 2D and d' = d/2, β' = λ(2D)/(d/2) = 4 (λD/d) = 4β."
    },
    {
        "q": "The work function of a photosensitive metal is 2.5 eV. The threshold frequency for photoelectric emission is (h = 6.63 × 10⁻³⁴ J·s, 1 eV = 1.6 × 10⁻¹⁹ J):",
        "opts": ["3.0 × 10¹⁴ Hz", "6.0 × 10¹⁴ Hz", "7.5 × 10¹⁴ Hz", "9.0 × 10¹⁴ Hz"],
        "ans": 1,
        "topic": "Dual Nature of Radiation and Matter",
        "exp": "Work function Φ = 2.5 * 1.6×10⁻¹⁹ J = 4.0×10⁻¹⁹ J. ν₀ = Φ / h = (4.0×10⁻¹⁹) / (6.63×10⁻³⁴) ≈ 6.0 × 10¹⁴ Hz."
    },
    {
        "q": "The de Broglie wavelength of an electron accelerated through a potential difference of 100 V is approximately:",
        "opts": ["0.123 nm", "0.246 nm", "1.23 nm", "12.3 nm"],
        "ans": 0,
        "topic": "Dual Nature of Radiation and Matter",
        "exp": "λ = 1.227 / √V nm = 1.227 / √100 = 1.227 / 10 = 0.1227 nm ≈ 0.123 nm."
    },
    {
        "q": "The radius of the first Bohr orbit of a hydrogen atom is 0.53 Å. The radius of the second orbit (n = 2) is:",
        "opts": ["1.06 Å", "1.59 Å", "2.12 Å", "4.24 Å"],
        "ans": 2,
        "topic": "Atoms",
        "exp": "r_n = r₁ * n² = 0.53 Å * (2)² = 0.53 * 4 = 2.12 Å."
    },
    {
        "q": "The half-life of a radioactive isotope is 5 days. The fraction of the initial mass that remains undecayed after 20 days is:",
        "opts": ["1/4", "1/8", "1/16", "1/32"],
        "ans": 2,
        "topic": "Nuclei",
        "exp": "Number of half-lives n = 20 / 5 = 4. Remaining fraction = (1/2)⁴ = 1/16."
    },
    {
        "q": "In a p-n junction diode, the barrier potential for Silicon at room temperature is approximately:",
        "opts": ["0.1 V", "0.3 V", "0.7 V", "1.1 V"],
        "ans": 2,
        "topic": "Semiconductor Electronics",
        "exp": "The barrier potential for Silicon p-n junction is ~0.7 V (for Germanium it is ~0.3 V)."
    },
    {
        "q": "An ideal transformer has 500 primary turns and 50 secondary turns. If the input primary voltage is 220 V, the output secondary voltage is:",
        "opts": ["11 V", "22 V", "44 V", "110 V"],
        "ans": 1,
        "topic": "Alternating Current",
        "exp": "V_s / V_p = N_s / N_p => V_s = 220 * (50 / 500) = 22 V."
    },
    {
        "q": "A spring of force constant 400 N/m is stretched by 5 cm from its equilibrium position. The potential energy stored in the spring is:",
        "opts": ["0.5 J", "1.0 J", "2.0 J", "5.0 J"],
        "ans": 0,
        "topic": "Work, Energy and Power",
        "exp": "U = (1/2) k x² = 0.5 * 400 * (0.05)² = 200 * 0.0025 = 0.5 J."
    },
    {
        "q": "A particle executes Simple Harmonic Motion (SHM) with an amplitude of 10 cm and period of 2 s. The maximum velocity of the particle is:",
        "opts": ["5π cm/s", "10π cm/s", "20π cm/s", "40π cm/s"],
        "ans": 1,
        "topic": "Oscillations",
        "exp": "v_max = ω A = (2π / T) * A = (2π / 2) * 10 = 10π cm/s."
    }
]

CHEMISTRY_BANK: List[dict] = [
    {
        "q": "What is the mass percentage of carbon in carbon dioxide (CO₂)?",
        "opts": ["12.00%", "27.27%", "72.73%", "33.33%"],
        "ans": 1,
        "topic": "Some Basic Concepts of Chemistry",
        "exp": "Molar mass of CO₂ = 12 + 2(16) = 44 g/mol. Mass % of C = (12 / 44) * 100 = 27.27%."
    },
    {
        "q": "The maximum number of electrons that can be accommodated in a subshell with l = 2 (d-subshell) is:",
        "opts": ["2", "6", "10", "14"],
        "ans": 2,
        "topic": "Structure of Atom",
        "exp": "Number of electrons in a subshell = 2(2l + 1). For l = 2: 2(2*2 + 1) = 10 electrons."
    },
    {
        "q": "Which of the following species has a square planar geometry according to VSEPR theory?",
        "opts": ["CH₄", "SF₄", "XeF₄", "NH₄⁺"],
        "ans": 2,
        "topic": "Chemical Bonding",
        "exp": "XeF₄ has 4 bond pairs and 2 lone pairs on Xe (sp³d² hybridization), giving a square planar shape."
    },
    {
        "q": "For a reaction ΔH = +40 kJ/mol and ΔS = +100 J/(K·mol). The temperature above which reaction becomes spontaneous is:",
        "opts": ["273 K", "300 K", "400 K", "500 K"],
        "ans": 2,
        "topic": "Thermodynamics",
        "exp": "T = ΔH / ΔS = (40000 J/mol) / (100 J/K·mol) = 400 K."
    },
    {
        "q": "The standard EMF of cell Zn | Zn²⁺ || Cu²⁺ | Cu with E°(Zn²⁺/Zn) = -0.76 V and E°(Cu²⁺/Cu) = +0.34 V is:",
        "opts": ["+0.42 V", "+1.10 V", "-1.10 V", "+0.76 V"],
        "ans": 1,
        "topic": "Electrochemistry",
        "exp": "E°_cell = 0.34 - (-0.76) = +1.10 V."
    }
]

MATHEMATICS_BANK: List[dict] = [
    {
        "q": "The domain of the real-valued function f(x) = sin⁻¹(2x - 1) is:",
        "opts": ["[-1, 1]", "[0, 1]", "[-1/2, 1/2]", "(0, 1)"],
        "ans": 1,
        "topic": "Inverse Trigonometric Functions",
        "exp": "-1 ≤ 2x - 1 ≤ 1 => 0 ≤ 2x ≤ 2 => 0 ≤ x ≤ 1."
    },
    {
        "q": "If matrix A = [[2, 3], [1, 4]], then the determinant of A⁻¹ (|A⁻¹|) is:",
        "opts": ["1/5", "1/8", "5", "8"],
        "ans": 0,
        "topic": "Matrices and Determinants",
        "exp": "|A| = 8 - 3 = 5. |A⁻¹| = 1/5."
    },
    {
        "q": "If A is a square matrix of order 3 with |A| = 4, then |adj(A)| is equal to:",
        "opts": ["4", "12", "16", "64"],
        "ans": 2,
        "topic": "Determinants",
        "exp": "|adj(A)| = |A|^(n-1) = 4² = 16."
    },
    {
        "q": "The derivative of tan⁻¹[sin x / (1 + cos x)] with respect to x is:",
        "opts": ["1/2", "1", "2", "-1/2"],
        "ans": 0,
        "topic": "Continuity and Differentiability",
        "exp": "sin x / (1 + cos x) = tan(x/2) => y = x/2 => dy/dx = 1/2."
    },
    {
        "q": "If vector a = 2i + j + 3k and vector b = 3i + 5j - k, then dot product a · b is equal to:",
        "opts": ["5", "8", "11", "14"],
        "ans": 1,
        "topic": "Vector Algebra",
        "exp": "a · b = (2*3) + (1*5) + (3*-1) = 6 + 5 - 3 = 8."
    }
]

BIOLOGY_BANK: List[dict] = [
    {
        "q": "In R.H. Whittaker's Five Kingdom Classification, Kingdom Monera exclusively includes:",
        "opts": ["Unicellular eukaryotes", "Prokaryotic organisms like Bacteria and Cyanobacteria", "Multicellular fungi", "Acellular viruses"],
        "ans": 1,
        "topic": "Biological Classification",
        "exp": "Kingdom Monera comprises all prokaryotic unicellular organisms lacking a membrane-bound nucleus."
    },
    {
        "q": "Double fertilization involving syngamy and triple fusion is a unique feature of:",
        "opts": ["Algae", "Bryophytes", "Gymnosperms", "Angiosperms"],
        "ans": 3,
        "topic": "Plant Kingdom",
        "exp": "Double fertilization occurs exclusively in flowering plants (Angiosperms)."
    },
    {
        "q": "The organelle known as the powerhouse of the cell where ATP synthesis occurs is:",
        "opts": ["Golgi apparatus", "Ribosome", "Mitochondrion", "Lysosome"],
        "ans": 2,
        "topic": "Cell Biology",
        "exp": "Mitochondria generate ATP through cellular respiration on their inner cristae membrane."
    },
    {
        "q": "During meiotic cell division, crossing over occurs during which stage of Prophase I?",
        "opts": ["Leptotene", "Zygotene", "Pachytene", "Diplotene"],
        "ans": 2,
        "topic": "Cell Cycle",
        "exp": "Crossing over occurs during the Pachytene stage."
    },
    {
        "q": "In C₄ plants, the primary carbon dioxide (CO₂) acceptor in mesophyll cells is:",
        "opts": ["Ribulose-1,5-bisphosphate (RuBP)", "Phosphoenolpyruvate (PEP)", "Oxaloacetic acid (OAA)", "Phosphoglyceric acid (PGA)"],
        "ans": 1,
        "topic": "Photosynthesis",
        "exp": "In C₄ plants, CO₂ is fixed by PEP carboxylase using Phosphoenolpyruvate (PEP)."
    }
]


def _option_index(letter: str) -> int:
    """Convert A/B/C/D or 1/2/3/4 to 0-based index."""
    letter = letter.upper()
    if letter in "ABCD":
        return ord(letter) - ord("A")
    if letter in "1234":
        return int(letter) - 1
    return 0


def _extract_answer_keys(text: str) -> dict[int, int]:
    """Try to find an answer key section at the end of the text."""
    answer_section_markers = [
        r"answer\s*key",
        r"answers?\s*:",
        r"key\s*:",
        r"solution",
    ]
    marker_pattern = re.compile(
        "|".join(answer_section_markers), re.IGNORECASE
    )

    keys: dict[int, int] = {}

    match = marker_pattern.search(text)
    if match:
        answer_text = text[match.start():]
        for m in _ANS_KEY_RE.finditer(answer_text):
            q_num = int(m.group(1))
            ans_letter = m.group(2)
            keys[q_num] = _option_index(ans_letter)

    return keys


def extract_mcqs_from_text(text: str, topic: str = "General") -> List[dict]:
    """Extract structured MCQ questions from raw text."""
    if not text or not text.strip():
        return []

    questions: List[dict] = []
    lines = text.split("\n")
    answer_keys = _extract_answer_keys(text)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        q_match = _Q_NUM_RE.match(line)
        if not q_match:
            i += 1
            continue

        q_num = int(q_match.group(1))
        q_text = line[q_match.end():].strip()

        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                i += 1
                continue
            if _OPT_RE.match(next_line) or _OPT_NUM_RE.match(next_line):
                break
            if _Q_NUM_RE.match(next_line):
                break
            q_text += " " + next_line
            i += 1

        if not q_text.strip():
            continue

        options: List[str] = []
        inline_answer: Optional[int] = None

        while i < len(lines) and len(options) < 4:
            opt_line = lines[i].strip()
            if not opt_line:
                i += 1
                continue

            opt_match = _OPT_RE.match(opt_line)
            if opt_match:
                opt_text = opt_line[opt_match.end():].strip()
                options.append(opt_text)
                i += 1
                continue

            opt_num_match = _OPT_NUM_RE.match(opt_line)
            if opt_num_match:
                opt_text = opt_line[opt_num_match.end():].strip()
                options.append(opt_text)
                i += 1
                continue

            ans_match = _INLINE_ANS_RE.search(opt_line)
            if ans_match and len(options) == 4:
                inline_answer = _option_index(ans_match.group(1))
                i += 1
                break

            break

        if len(options) != 4:
            continue

        # Validate question cleanliness
        if not is_valid_question(q_text, options, subject=topic):
            logger.info("Filtered out non-subject / junk / OMR extracted question: %s", q_text[:50])
            continue

        if inline_answer is None:
            lookahead = min(i + 3, len(lines))
            for j in range(i, lookahead):
                ans_match = _INLINE_ANS_RE.search(lines[j])
                if ans_match:
                    inline_answer = _option_index(ans_match.group(1))
                    break

        correct_ans = 0
        if inline_answer is not None:
            correct_ans = inline_answer
        elif q_num in answer_keys:
            correct_ans = answer_keys[q_num]

        questions.append({
            "q": q_text.strip(),
            "opts": options,
            "ans": correct_ans,
            "topic": topic,
            "exp": "",
        })

    logger.info(
        "Pattern extraction found %d MCQs from text (%d chars)",
        len(questions),
        len(text),
    )
    return questions


def generate_fallback_mcqs(text: str, topic: str = "General", max_questions: int = 20) -> List[dict]:
    """Generate high-quality fallback questions from curated subject question banks.

    Ensures NO pseudo-questions ('Which statement about ...') or random OMR lines are EVER generated!
    """
    topic_lower = topic.lower()

    subject_bank_map = {
        "physics": PHYSICS_NUMERICAL_BANK,
        "chemistry": CHEMISTRY_BANK,
        "mathematics": MATHEMATICS_BANK,
        "maths": MATHEMATICS_BANK,
        "biology": BIOLOGY_BANK,
    }

    bank = subject_bank_map.get(topic_lower, PHYSICS_NUMERICAL_BANK)
    selected = random.sample(bank, min(max_questions, len(bank)))
    results = []
    for q in selected:
        results.append({
            "q": q["q"],
            "opts": list(q["opts"]),
            "ans": q["ans"],
            "topic": q["topic"],
            "exp": q.get("exp", ""),
        })
    logger.info("Provided %d authentic questions from %s question bank", len(results), topic)
    return results


def extract_or_generate_mcqs(
    text: str,
    topic: str = "General",
    min_questions: int = 20,
) -> List[dict]:
    """Extract MCQs from uploaded text via pattern matching or Groq LLM RAG extraction."""
    extracted = extract_mcqs_from_text(text, topic=topic)
    extracted = [q for q in extracted if is_valid_question(q["q"], q["opts"], subject=topic)]

    if len(extracted) >= min_questions:
        logger.info(
            "Extracted %d valid MCQs from text patterns for %s",
            len(extracted),
            topic,
        )
        return extracted

    needed = min_questions - len(extracted)
    
    # Try RAG LLM extraction from uploaded text content
    rag_questions = []
    if len(text.strip()) > 50:
        try:
            from .groq_client import generate_kcet_mcqs_from_textbook
            from .parsing import chunk_text
            chunks = chunk_text(text) if len(text) > 1000 else [text]
            
            logger.info("Attempting RAG LLM extraction from %d chunks for %s...", len(chunks), topic)
            llm_results = generate_kcet_mcqs_from_textbook(
                context_chunks=chunks,
                subject=topic,
                set_label="U",
                used_questions=set(q["q"] for q in extracted),
                questions_needed=needed,
            )
            for q in llm_results:
                if is_valid_question(q.get("q", ""), q.get("opts", []), subject=topic):
                    rag_questions.append(q)
            logger.info("RAG LLM extracted %d valid MCQs from uploaded content for %s", len(rag_questions), topic)
        except Exception as exc:
            logger.warning("RAG LLM extraction failed (%s), falling back to authentic question bank", exc)

    combined = extracted + rag_questions
    if len(combined) < min_questions:
        still_needed = min_questions - len(combined)
        fallback = generate_fallback_mcqs(text, topic=topic, max_questions=still_needed)
        combined.extend(fallback)

    logger.info("Total MCQs for %s after RAG extraction & fallback: %d", topic, len(combined))
    return combined[:min_questions]



__all__ = [
    "extract_mcqs_from_text",
    "generate_fallback_mcqs",
    "extract_or_generate_mcqs",
    "is_valid_question",
    "is_valid_physics_question",
    "PHYSICS_NUMERICAL_BANK",
    "CHEMISTRY_BANK",
    "MATHEMATICS_BANK",
    "BIOLOGY_BANK",
]
