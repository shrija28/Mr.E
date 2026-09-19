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
from typing import List, Optional, Iterable
from .topic_matcher import is_topic_matching

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


def shuffle_options_for_set_label(opts: List[str], ans: Any, set_label: str) -> tuple[List[str], str]:
    """Applies a deterministic set-specific permutation to options for Set A, B, C, D.
    Ensures Q1..Q60 stems are identical across all sets while option letters A/B/C/D are scrambled per set.
    """
    if not isinstance(opts, list) or len(opts) != 4:
        return opts, str(ans) if ans is not None else "0"

    clean_opts = [
        re.sub(r"^\s*(?:\([A-Da-d1-4]\)|[A-Da-d1-4]\s*[.):\-]|option\s+[A-Da-d1-4]\s*[:\-]?)\s*", "", str(opt), flags=re.IGNORECASE).strip()
        for opt in opts
    ]

    ans_str = str(ans).strip() if ans is not None else "0"
    letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "0": 0, "1": 1, "2": 2, "3": 3}

    current_idx = None
    if ans_str.lower() in letter_map:
        current_idx = letter_map[ans_str.lower()]
    elif ans_str.isdigit() and 0 <= int(ans_str) < 4:
        current_idx = int(ans_str)
    else:
        for idx, opt in enumerate(clean_opts):
            if str(opt).lower() == ans_str.lower():
                current_idx = idx
                break

    if current_idx is None or current_idx < 0 or current_idx >= 4:
        current_idx = 0

    # Deterministic permutations for each set label
    label_upper = str(set_label).strip().upper()
    if label_upper == 'B':
        perm = [1, 2, 3, 0]
    elif label_upper == 'C':
        perm = [3, 0, 1, 2]
    elif label_upper == 'D':
        perm = [2, 3, 0, 1]
    else:
        perm = [0, 1, 2, 3]

    shuffled_opts = [clean_opts[i] for i in perm]
    new_ans_idx = perm.index(current_idx)

    return shuffled_opts, str(new_ans_idx)


def shuffle_question_options(opts: List[str], ans: Any) -> tuple[List[str], str]:
    """Alias for backwards compatibility using random option shuffling."""
    return shuffle_options_for_set_label(opts, ans, "A")


def normalize_question_fingerprint(q_text: str) -> str:
    """Requirement 1: Strict question deduplication fingerprint.
    Normalizes question stem by removing question numbers, punctuation, spaces, and converting to lowercase.
    """
    if not q_text or not isinstance(q_text, str):
        return ""
    text = q_text.lower().strip()
    text = re.sub(r"^(?:q\.?\s*\d+|\d+[\.\)\-:]?\s*)", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def extract_concept_fingerprint(q_text: str) -> str:
    """Requirement: Concept-level formula deduplication (DO NOT REPEAT REPETITIVE NUMERICAL VARIATIONS).
    Maps any question stem to its canonical formula or concept archetype so that max 1 question
    per concept archetype is selected for an exam.
    """
    if not q_text or not isinstance(q_text, str):
        return ""
    q = q_text.lower().strip()

    # ── Physics Concepts ──
    if "projectile" in q or "launched" in q:
        if "maximum height" in q or "h_max" in q or "highest point" in q:
            return "concept:phy_projectile_max_height"
        if "range" in q or "horizontal distance" in q:
            return "concept:phy_projectile_range"
        if "time of flight" in q:
            return "concept:phy_projectile_time_of_flight"
        if "kinetic energy" in q:
            return "concept:phy_projectile_ke_apex"
        return "concept:phy_projectile_kinematics"

    if "capacitor" in q or "capacitance" in q:
        if "energy" in q or "electrostatic energy" in q or "stored" in q:
            return "concept:phy_capacitor_energy"
        if "series" in q:
            return "concept:phy_capacitor_series"
        if "parallel" in q:
            return "concept:phy_capacitor_parallel"
        if "dielectric" in q:
            return "concept:phy_capacitor_dielectric"

    if "resistor" in q or "resistance" in q or "resistors" in q:
        if "parallel" in q:
            return "concept:phy_resistors_parallel"
        if "series" in q:
            return "concept:phy_resistors_series"
        if "stretched" in q or "length" in q:
            return "concept:phy_wire_stretching_resistance"
        if "wheatstone" in q or "bridge" in q:
            return "concept:phy_wheatstone_bridge"

    if "lens" in q or "mirror" in q or "focal length" in q:
        if "power" in q or "diopter" in q or "dioptres" in q:
            return "concept:phy_lens_power"
        if "combination" in q or "contact" in q:
            return "concept:phy_lens_combination"
        if "magnification" in q:
            return "concept:phy_lens_magnification"

    if "refractive index" in q or "speed of light" in q:
        return "concept:phy_refraction_speed"

    if "de broglie" in q or "photoelectric" in q or "work function" in q:
        if "work function" in q or "threshold" in q:
            return "concept:phy_photoelectric_work_function"
        if "de broglie" in q:
            return "concept:phy_de_broglie_wavelength"

    if "transformer" in q:
        return "concept:phy_transformer_turns_ratio"

    if "bohr" in q or "orbit" in q:
        if "radius" in q:
            return "concept:phy_bohr_orbit_radius"
        if "energy level" in q or "ionization" in q:
            return "concept:phy_bohr_energy_level"

    if "half-life" in q or "radioactive" in q or "decay" in q:
        return "concept:phy_radioactive_decay"

    if "carnot" in q or "efficiency" in q:
        return "concept:phy_carnot_engine"

    if "spring" in q or "force constant" in q:
        return "concept:phy_spring_potential_energy"

    if "shm" in q or "simple harmonic" in q:
        if "maximum velocity" in q or "v_max" in q:
            return "concept:phy_shm_max_velocity"
        if "time period" in q or "frequency" in q:
            return "concept:phy_shm_time_period"

    if "escape velocity" in q:
        return "concept:phy_escape_velocity"

    if "acceleration due to gravity" in q or "value of g" in q:
        return "concept:phy_gravity_variation"

    if "young's double slit" in q or "fringe width" in q:
        return "concept:phy_ydse_fringe_width"

    # ── Chemistry Concepts ──
    if "mass percentage" in q or "percentage by mass" in q:
        return "concept:chem_mass_percentage"

    if "oxidation state" in q or "oxidation number" in q:
        return "concept:chem_oxidation_state"

    if "first-order" in q or "rate constant" in q or "half-life" in q:
        return "concept:chem_kinetics_first_order"

    if "standard reduction potential" in q or "standard cell potential" in q or "e°_cell" in q:
        return "concept:chem_electro_cell_emf"

    if "hybridization" in q or "geometry" in q or "vsepr" in q:
        return "concept:chem_bonding_hybridization"

    if "aldol" in q or "cannizzaro" in q or "reimer-tiemann" in q or "kolbe" in q or "clemmensen" in q:
        return "concept:chem_organic_named_reaction"

    if "sn1" in q or "sn2" in q:
        return "concept:chem_haloalkane_substitution"

    if "ligand" in q or "coordination number" in q or "crystal field" in q:
        return "concept:chem_coordination_compounds"

    # ── Mathematics Concepts ──
    if "inverse function" in q or "f⁻¹" in q or "f^-1" in q:
        return "concept:math_inverse_function"

    if "principal value" in q or "sin⁻¹" in q or "cos⁻¹" in q or "tan⁻¹" in q or "sin^-1" in q or "cos^-1" in q:
        return "concept:math_inverse_trig_value"

    if "matrix" in q or "matrices" in q:
        if "symmetric" in q or "skew-symmetric" in q:
            return "concept:math_matrix_symmetry"
        if "order" in q or "elements" in q:
            return "concept:math_matrix_order"
        if "inverse" in q or "adjoint" in q:
            return "concept:math_matrix_adjoint_inverse"

    if "determinant" in q or "|adj(a)|" in q or "|ka|" in q or "|2a|" in q or "|3a|" in q:
        return "concept:math_determinant_properties"

    if "continuous at" in q or "continuity" in q:
        return "concept:math_continuity"

    if "derivative of" in q or "dy/dx" in q or "d/dx" in q:
        if "x^" in q or "polynomial" in q:
            return "concept:math_derivative_power_rule"
        if "sin" in q or "cos" in q or "log" in q:
            return "concept:math_derivative_chain_rule"
        return "concept:math_derivative_calculation"

    if "integral of" in q or "∫" in q or "dx" in q:
        return "concept:math_integral_calculation"

    if "vector" in q or "dot product" in q or "cross product" in q:
        if "dot product" in q or "scalar dot" in q:
            return "concept:math_vector_dot_product"
        if "cross product" in q:
            return "concept:math_vector_cross_product"
        if "perpendicular" in q:
            return "concept:math_vector_perpendicular"
        if "magnitude" in q:
            return "concept:math_vector_magnitude"
        if "projection" in q:
            return "concept:math_vector_projection"
        return "concept:math_vector_operations"

    if "probability" in q or "bayes" in q:
        return "concept:math_probability"

    # Fallback: strip punctuation and replace ALL numbers/digits with # to unify numerical variations
    clean_norm = re.sub(r"\d+(\.\d+)?", "#", q)
    clean_norm = re.sub(r"[^\w\s#]", "", clean_norm)
    return "concept:num_pattern:" + " ".join(clean_norm.split())


def interleave_by_subtype(questions: List[dict]) -> List[dict]:
    """Requirement 2: Strict question type variety (DO NOT REPEAT THE SAME TYPES OF QUESTION).
    Interleaves questions so that adjacent questions alternate among question subtypes:
    direct_formula, multi_step, theory_definition, physical_numerical, fact_reaction.
    """
    if not questions:
        return []

    from collections import defaultdict, deque
    grouped = defaultdict(deque)
    for q in questions:
        st = q.get("subtype") or "theory_definition"
        grouped[st].append(q)

    subtypes = list(grouped.keys())
    interleaved = []
    while any(grouped.values()):
        for st in list(subtypes):
            if grouped[st]:
                interleaved.append(grouped[st].popleft())

    return interleaved


# Official KCET 2026 Chapter Weightage Specifications (out of 60 questions per subject)
KCET_PHYSICS_WEIGHTS = [
    # 1st PUC (~30% / 18 Qs)
    ("Physical World, Units & Measurements", ["unit", "dimension", "error", "measurement", "physical world"], 1),
    ("Kinematics (Straight Line & Plane)", ["straight line", "plane", "kinematics", "projectile", "velocity", "acceleration", "displacement"], 3),
    ("Laws of Motion & Friction", ["laws of motion", "friction", "newton", "momentum", "impulse", "tension"], 2),
    ("Work, Energy, Power & Collisions", ["work", "energy", "power", "collision", "spring", "potential energy"], 2),
    ("Gravitation", ["gravitation", "gravitational", "kepler", "escape velocity", "orbital", "g at height"], 3),
    ("Mechanics of Solids & Fluids", ["solid", "fluid", "young's modulus", "viscosity", "surface tension", "bernoulli", "pascal", "stokes"], 2),
    ("Thermodynamics & Kinetic Theory", ["thermodynamics", "kinetic theory", "carnot", "isothermal", "adiabatic", "specific heat", "mean free path"], 3),
    ("Oscillations & Waves", ["oscillation", "simple harmonic", "shm", "wave", "doppler", "pendulum", "frequency", "standing wave"], 2),
    # 2nd PUC (~70% / 42 Qs)
    ("Electrostatics (Charges, Fields, Potential)", ["charge", "electric field", "coulomb", "gauss", "potential", "capacitor", "capacitance", "dielectric"], 7),
    ("Current Electricity", ["current electricity", "ohm", "resistance", "resistivity", "potentiometer", "wheatstone", "kirchhoff", "drift velocity"], 5),
    ("Magnetic Effects of Current & Magnetism", ["magnetic", "biot", "ampere", "cyclotron", "torque on loop", "galvanometer", "ferromagnetism"], 5),
    ("Electromagnetic Induction & AC", ["induction", "faraday", "lenz", "alternating current", "ac", "transformer", "inductance", "impedance", "resonance"], 5),
    ("Ray Optics & Wave Optics", ["ray optics", "wave optics", "lens", "mirror", "refraction", "prism", "young's double", "interference", "diffraction", "polarization"], 7),
    ("Modern Physics (Dual Nature, Atoms, Nuclei)", ["dual nature", "photoelectric", "de broglie", "atom", "bohr", "nucleus", "radioactivity", "half-life", "binding energy"], 6),
    ("Semiconductors & Electronics", ["semiconductor", "p-n junction", "diode", "transistor", "logic gate", "zener", "rectifier", "led"], 4),
    ("Electromagnetic Waves & Communication", ["electromagnetic wave", "em wave", "displacement current", "communication", "antenna", "modulation"], 3),
]

KCET_CHEMISTRY_WEIGHTS = [
    # 1st PUC (~33% / 20 Qs)
    ("Some Basic Concepts of Chemistry", ["basic concept", "mole", "molarity", "molality", "stoichiometry", "empirical formula"], 2),
    ("Structure of Atom", ["structure of atom", "bohr", "quantum number", "heisenberg", "de broglie", "photoelectric", "orbital"], 2),
    ("Classification of Elements & Periodicity", ["periodicity", "periodic table", "ionization enthalpy", "electronegativity", "atomic radius"], 2),
    ("Chemical Bonding & Molecular Structure", ["bonding", "hybridization", "vsepr", "molecular orbital", "dipole moment", "hydrogen bond"], 2),
    ("States of Matter: Gases and Liquids", ["states of matter", "boyle", "charles", "ideal gas", "van der waals", "surface tension", "viscosity"], 1),
    ("Thermodynamics (Chemistry)", ["thermodynamics", "enthalpy", "entropy", "gibbs", "hess's law", "heat of combustion"], 2),
    ("Equilibrium", ["equilibrium", "le chatelier", "kc", "kp", "ph", "buffer", "solubility product", "ksp"], 2),
    ("Redox Reactions", ["redox", "oxidation number", "balancing", "reducing agent", "oxidizing agent"], 1),
    ("Hydrogen", ["hydrogen", "heavy water", "hydrogen peroxide", "h2o2", "hydride"], 1),
    ("s-Block Elements", ["s-block", "alkali", "alkaline earth", "sodium hydroxide", "calcium carbonate", "plaster of paris"], 1),
    ("Some p-Block Elements (1st PUC)", ["p-block", "boron", "diborane", "carbon", "allotrope", "silicone", "silicates"], 1),
    ("Organic Chemistry - Basic Principles", ["basic principles", "iupac", "isomerism", "carbocation", "inductive", "resonance", "hyperconjugation"], 1),
    ("Hydrocarbons", ["hydrocarbons", "alkane", "alkene", "alkyne", "markovnikov", "ozonolysis", "benzene", "friedel-crafts"], 1),
    ("Environmental Chemistry", ["environmental chemistry", "smog", "acid rain", "greenhouse", "bod", "cod"], 1),
    # 2nd PUC (~67% / 40 Qs)
    ("Solid State", ["solid state", "unit cell", "schottky", "frenkel", "packing efficiency", "bragg", "coordination number"], 3),
    ("Solutions", ["solutions", "raoult", "henry", "colligative", "osmotic", "van 't hoff", "elevation of boiling", "freezing point"], 3),
    ("Electrochemistry", ["electrochemistry", "nernst", "kolrausch", "faraday", "molar conductivity", "fuel cell", "corrosion"], 3),
    ("Chemical Kinetics", ["chemical kinetics", "order of reaction", "rate constant", "arrhenius", "half-life", "activation energy"], 3),
    ("Surface Chemistry", ["surface chemistry", "adsorption", "physisorption", "chemisorption", "colloid", "tyndall", "hardy-schulze", "emulsion"], 2),
    ("General Principles of Isolation", ["isolation", "metallurgy", "froth flotation", "calcination", "roasting", "refining", "elllingham"], 1),
    ("p-Block Elements (2nd PUC)", ["p-block", "nitrogen", "ammonia", "nitric acid", "phosphorus", "sulfuric acid", "ozone", "halogen", "interhalogen"], 4),
    ("d & f Block Elements", ["d and f block", "lanthanide", "actinide", "transition metal", "oxidation state", "kmno4", "k2cr2o7"], 3),
    ("Coordination Compounds", ["coordination compound", "iupac name", "isomerism", "werner", "valence bond", "crystal field", "spectrochemical"], 3),
    ("Haloalkanes & Haloarenes", ["haloalkane", "haloarene", "sn1", "sn2", "wurtz", "fittig", "chloroform", "freon"], 3),
    ("Alcohols, Phenols & Ethers", ["alcohol", "phenol", "ether", "lucas", "kolbe", "reimer-tiemann", "williamson", "dehydration"], 3),
    ("Aldehydes, Ketones & Carboxylic Acids", ["aldehyde", "ketone", "carboxylic acid", "aldol", "cannizzaro", "tollens", "fehling", "clemmensen", "hvz"], 4),
    ("Amines", ["amines", "diazotization", "sandmeyer", "hinsberg", "hoffmann bromamide", "carbylamine"], 2),
    ("Biomolecules", ["biomolecules", "carbohydrate", "glucose", "protein", "amino acid", "dna", "rna", "vitamin", "enzyme"], 1),
    ("Polymers", ["polymers", "nylon", "bakelite", "teflon", "neoprene", "buna-n", "dacron", "vulcanization"], 1),
    ("Chemistry in Everyday Life", ["everyday life", "antiseptic", "analgesic", "antipyretic", "aspartame", "dettol", "detergent", "soap"], 1),
]

KCET_MATHEMATICS_WEIGHTS = [
    # 1st PUC (~30% / 18 Qs)
    ("Sets, Relations & Functions (1st PUC)", ["set", "subset", "venn", "domain", "range", "relation", "sets"], 3),
    ("Trigonometric Functions", ["trigonometric", "sin", "cos", "tan", "radian", "general solution", "trigonometry"], 3),
    ("Complex Numbers & Quadratic Equations", ["complex number", "iota", "modulus", "argument", "quadratic equation", "discriminant", "complex numbers"], 2),
    ("Permutations, Combinations & Inequalities", ["permutation", "combination", "factorial", "linear inequalities", "permutations and combinations"], 3),
    ("Binomial Theorem & Sequences/Series", ["binomial", "ap", "gp", "arithmetic progression", "geometric progression", "series", "sequences and series", "binomial theorem"], 2),
    ("Straight Lines & Conic Sections", ["straight line", "slope", "intercept", "parabola", "ellipse", "hyperbola", "circle", "conic sections", "conic"], 3),
    ("Limits & Derivatives (1st PUC)", ["limit", "derivative", "l'hopital", "first principle", "limits and derivatives"], 2),
    # 2nd PUC (~70% / 42 Qs)
    ("Relations & Functions & Inverse Trig", ["inverse trig", "one-one", "onto", "bijective", "principal value", "relations and functions", "inverse trigonometric functions"], 4),
    ("Matrices & Determinants", ["matrix", "matrices", "determinant", "determinants", "adjoint", "inverse of matrix", "cramer"], 5),
    ("Continuity, Differentiability & AOD", ["continuity", "differentiable", "chain rule", "tangent", "normal", "maxima", "minima", "increasing", "continuity and differentiability", "application of derivatives"], 8),
    ("Integrals & Application of Integrals", ["integral", "integrals", "integration", "substitution", "by parts", "definite integral", "area under curve", "application of integrals"], 8),
    ("Differential Equations", ["differential equation", "differential equations", "order", "degree", "variable separable", "integrating factor", "homogeneous"], 4),
    ("Vectors & 3D Geometry", ["vector", "vector algebra", "dot product", "cross product", "scalar triple", "direction cosines", "plane", "shortest distance", "three dimensional geometry", "3d"], 8),
    ("Linear Programming & Probability", ["linear programming", "feasible region", "probability", "bayes", "conditional probability", "binomial distribution"], 5),
]


def apply_kcet_chapter_distribution(questions: List[dict], subject: str, target_count: int = 60) -> List[dict]:
    """Applies official KCET 2026 Chapter-Wise Weightage Engine across 1st PUC and 2nd PUC chapters.
    Enforces exact chapter quota allocations and concept deduplication.
    """
    if not questions:
        return []

    sub_lower = subject.lower()
    weights_spec = []
    if "physic" in sub_lower:
        weights_spec = KCET_PHYSICS_WEIGHTS
    elif "chem" in sub_lower:
        weights_spec = KCET_CHEMISTRY_WEIGHTS
    elif "math" in sub_lower:
        weights_spec = KCET_MATHEMATICS_WEIGHTS

    if not weights_spec:
        # Fallback for Biology or general subjects (40% 1st PUC / 60% 2nd PUC)
        puc1_kw = ("living world", "plant physiology", "human physiology", "cell", "biomolecule")
        puc1_qs = [q for q in questions if any(kw in (q.get("topic") or "").lower() for kw in puc1_kw)]
        puc2_qs = [q for q in questions if q not in puc1_qs]
        puc1_target = int(target_count * 0.40)
        puc2_target = target_count - puc1_target
        res = puc1_qs[:puc1_target] + puc2_qs[:puc2_target]
        if len(res) < target_count:
            rem = [q for q in questions if q not in res]
            res.extend(rem[:target_count - len(res)])
        return interleave_by_subtype(res[:target_count])

    # Concept deduplication: track normalized question fingerprints AND concept fingerprints
    selected = []
    seen_fingerprints = set()
    seen_concepts = set()
    used_questions = set()

    for category_name, keywords, target_qty in weights_spec:
        # Scale quota proportionately if target_count != 60
        scaled_qty = max(1, round(target_qty * (target_count / 60.0)))
        added_for_cat = 0
        for q in questions:
            if added_for_cat >= scaled_qty:
                break
            q_id = id(q)
            if q_id in used_questions:
                continue
            q_text = q.get("q", "")
            fp = normalize_question_fingerprint(q_text)
            concept_fp = extract_concept_fingerprint(q_text)
            top = (q.get("topic") or "").lower()
            q_full = (q_text + " " + top).lower()

            if fp and fp not in seen_fingerprints and concept_fp not in seen_concepts and any(kw in q_full for kw in keywords):
                selected.append(q)
                seen_fingerprints.add(fp)
                seen_concepts.add(concept_fp)
                used_questions.add(q_id)
                added_for_cat += 1

    # Top up remaining if pool size < target_count
    if len(selected) < target_count:
        for q in questions:
            if len(selected) >= target_count:
                break
            q_id = id(q)
            q_text = q.get("q", "")
            fp = normalize_question_fingerprint(q_text)
            concept_fp = extract_concept_fingerprint(q_text)
            if q_id not in used_questions and fp and fp not in seen_fingerprints and concept_fp not in seen_concepts:
                selected.append(q)
                seen_fingerprints.add(fp)
                seen_concepts.add(concept_fp)
                used_questions.add(q_id)

    if len(selected) < target_count:
        needed = target_count - len(selected)
        topup = _generate_subject_variations(subject, needed, {q.get("q", "") for q in selected if q.get("q")})
        for q in topup:
            if len(selected) >= target_count:
                break
            q_text = q.get("q", "")
            fp = normalize_question_fingerprint(q_text)
            concept_fp = extract_concept_fingerprint(q_text)
            if fp and fp not in seen_fingerprints and concept_fp not in seen_concepts:
                selected.append(q)
                seen_fingerprints.add(fp)
                seen_concepts.add(concept_fp)

    return interleave_by_subtype(selected[:target_count])


>>>>>>> ec47da2 (updated few features)
def is_valid_question(q_text: str, options: List[str], subject: str = "General")-> bool:
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

    if subject.lower() == "biology":
        physics_matches = sum(1 for term in _PHYSICS_TERMS if term in full_text)
        if physics_matches >= 2:
            return False
        has_calc = bool(re.search(r"\b\d+(\.\d+)?\s*(m/s|ms\^-1|m/s\^2|ohm|omega|µc|uf|pf|rad/s)\b", full_text, re.IGNORECASE))
        if has_calc:
            return False

    return True


def is_valid_physics_question(q_text: str, options: List[str])-> bool:
    return is_valid_question(q_text, options, subject="Physics")


# ---------------------------------------------------------------------------
# High-Quality Question Banks Partitioned by KCET Blueprint Subtypes
# ---------------------------------------------------------------------------

# ── Physics Bank 1: Direct Formula Substitution (~30% to 40% of Physics) ──
PHYSICS_DIRECT_FORMULA_BANK: List[dict] = [
    {
        "q": "A car starting from rest accelerates uniformly at a rate of 2 m/s² for 10 s. What is the total distance traveled by the car?",
        "opts": ["50 m", "100 m", "150 m", "200 m"],
        "ans": 1,
        "topic": "Motion in a Straight Line",
        "subtype": "direct_formula",
        "exp": "Using s = ut + (1/2)at², with u = 0, a = 2 m/s², t = 10 s: s = 0 + 0.5 * 2 * 100 = 100 m."
    },
    {
        "q": "A body of mass 5 kg is dropped from a height of 20 m. Taking g = 10 m/s², the velocity of the body just before striking the ground is:",
        "opts": ["10 m/s", "20 m/s", "30 m/s", "40 m/s"],
        "ans": 1,
        "topic": "Motion in a Straight Line",
        "subtype": "direct_formula",
        "exp": "Using v² = u² + 2gh, v² = 0 + 2(10)(20) = 400 => v = 20 m/s."
    },
    {
        "q": "A projectile is thrown with an initial velocity of 20 m/s at an angle of 30° with the horizontal. The maximum height attained by it is (g = 10 m/s²):",
        "opts": ["2.5 m", "5.0 m", "7.5 m", "10.0 m"],
        "ans": 1,
        "topic": "Motion in a Plane",
        "subtype": "direct_formula",
        "exp": "H_max = (u sin θ)² / (2g) = (20 * 0.5)² / (2 * 10) = 100 / 20 = 5.0 m."
    },
    {
        "q": "Three capacitors of capacitance 6 µF each are connected in series across a 12 V battery. The charge on each capacitor is:",
        "opts": ["12 µC", "24 µC", "36 µC", "72 µC"],
        "ans": 1,
        "topic": "Electrostatic Potential and Capacitance",
        "subtype": "direct_formula",
        "exp": "C_eq = 6/3 = 2 µF in series. Charge Q = C_eq * V = 2 µF * 12 V = 24 µC."
    },
    {
        "q": "A wire of resistance 16 Ω is cut into 4 equal pieces and connected in parallel. The equivalent resistance of the combination is:",
        "opts": ["1 Ω", "2 Ω", "4 Ω", "8 Ω"],
        "ans": 0,
        "topic": "Current Electricity",
        "subtype": "direct_formula",
        "exp": "Each piece has resistance 16/4 = 4 Ω. Connected in parallel: R_eq = 4/4 = 1 Ω."
    },
    {
        "q": "A circular coil of 100 turns and radius 5 cm carries a current of 1 A. The magnetic field at the center of the coil is (µ₀ = 4π × 10⁻⁷ T·m/A):",
        "opts": ["4π × 10⁻⁴ T", "2π × 10⁻⁴ T", "4π × 10⁻⁵ T", "2π × 10⁻⁵ T"],
        "ans": 0,
        "topic": "Moving Charges and Magnetism",
        "subtype": "direct_formula",
        "exp": "B = (µ₀ N I) / (2 R) = (4π×10⁻⁷ * 100 * 1) / (2 * 0.05) = 4π × 10⁻⁴ T."
    },
    {
        "q": "An AC voltage V = 200 sin(100π t) is applied across a 50 Ω resistor. The RMS value of current flowing through the resistor is:",
        "opts": ["2 A", "2.83 A", "4 A", "5.66 A"],
        "ans": 1,
        "topic": "Alternating Current",
        "subtype": "direct_formula",
        "exp": "V_peak = 200 V => V_rms = 200 / √2 ≈ 141.4 V. I_rms = V_rms / R = 141.4 / 50 ≈ 2.83 A."
    },
    {
        "q": "In a pure inductive circuit of L = 0.1 H connected to 220 V, 50 Hz AC supply, the inductive reactance X_L is approximately:",
        "opts": ["15.7 Ω", "31.4 Ω", "62.8 Ω", "100 Ω"],
        "ans": 1,
        "topic": "Alternating Current",
        "subtype": "direct_formula",
        "exp": "X_L = 2π f L = 2 * 3.1416 * 50 * 0.1 = 31.4 Ω."
    },
    {
        "q": "A convex lens of focal length 20 cm is placed in contact with a concave lens of focal length 40 cm. The focal length of the combination is:",
        "opts": ["+20 cm", "+40 cm", "-20 cm", "-40 cm"],
        "ans": 1,
        "topic": "Ray Optics",
        "subtype": "direct_formula",
        "exp": "1/F = 1/f1 + 1/f2 = 1/20 - 1/40 = 1/40 => F = +40 cm."
    },
    {
        "q": "The speed of light in a medium is 2 × 10⁸ m/s. The refractive index of the medium relative to vacuum is (c = 3 × 10⁸ m/s):",
        "opts": ["1.25", "1.33", "1.50", "1.75"],
        "ans": 2,
        "topic": "Ray Optics",
        "subtype": "direct_formula",
        "exp": "n = c / v = (3 × 10⁸) / (2 × 10⁸) = 1.50."
    },
    {
        "q": "The work function of a photosensitive metal is 2.5 eV. The threshold frequency for photoelectric emission is (h = 6.63 × 10⁻³⁴ J·s, 1 eV = 1.6 × 10⁻¹⁹ J):",
        "opts": ["3.0 × 10¹⁴ Hz", "6.0 × 10¹⁴ Hz", "7.5 × 10¹⁴ Hz", "9.0 × 10¹⁴ Hz"],
        "ans": 1,
        "topic": "Dual Nature of Radiation and Matter",
        "subtype": "direct_formula",
        "exp": "Work function Φ = 2.5 * 1.6×10⁻¹⁹ J = 4.0×10⁻¹⁹ J. ν₀ = Φ / h = (4.0×10⁻¹⁹) / (6.63×10⁻³⁴) ≈ 6.0 × 10¹⁴ Hz."
    },
    {
        "q": "The de Broglie wavelength of an electron accelerated through a potential difference of 100 V is approximately:",
        "opts": ["0.123 nm", "0.246 nm", "1.23 nm", "12.3 nm"],
        "ans": 0,
        "topic": "Dual Nature of Radiation and Matter",
        "subtype": "direct_formula",
        "exp": "λ = 1.227 / √V nm = 1.227 / √100 = 1.227 / 10 = 0.1227 nm ≈ 0.123 nm."
    },
    {
        "q": "The radius of the first Bohr orbit of a hydrogen atom is 0.53 Å. The radius of the second orbit (n = 2) is:",
        "opts": ["1.06 Å", "1.59 Å", "2.12 Å", "4.24 Å"],
        "ans": 2,
        "topic": "Atoms",
        "subtype": "direct_formula",
        "exp": "r_n = r₁ * n² = 0.53 Å * (2)² = 0.53 * 4 = 2.12 Å."
    },
    {
        "q": "An ideal transformer has 500 primary turns and 50 secondary turns. If the input primary voltage is 220 V, the output secondary voltage is:",
        "opts": ["11 V", "22 V", "44 V", "110 V"],
        "ans": 1,
        "topic": "Alternating Current",
        "subtype": "direct_formula",
        "exp": "V_s / V_p = N_s / N_p => V_s = 220 * (50 / 500) = 22 V."
    },
    {
        "q": "A spring of force constant 400 N/m is stretched by 5 cm from its equilibrium position. The potential energy stored in the spring is:",
        "opts": ["0.5 J", "1.0 J", "2.0 J", "5.0 J"],
        "ans": 0,
        "topic": "Work, Energy and Power",
        "subtype": "direct_formula",
        "exp": "U = (1/2) k x² = 0.5 * 400 * (0.05)² = 200 * 0.0025 = 0.5 J."
    },
    {
        "q": "A particle executes Simple Harmonic Motion (SHM) with an amplitude of 10 cm and period of 2 s. The maximum velocity of the particle is:",
        "opts": ["5π cm/s", "10π cm/s", "20π cm/s", "40π cm/s"],
        "ans": 1,
        "topic": "Oscillations",
        "subtype": "direct_formula",
        "exp": "v_max = ω A = (2π / T) * A = (2π / 2) * 10 = 10π cm/s."
    },
    {
        "q": "A convex lens has a focal length of +25 cm. The optical power of the lens in diopters is:",
        "opts": ["+2.5 D", "+4.0 D", "+5.0 D", "+10.0 D"],
        "ans": 1,
        "topic": "Ray Optics",
        "subtype": "direct_formula",
        "exp": "P = 100 / f(cm) = 100 / 25 = +4.0 D."
    }
]

# ── Physics Bank 2: Multi-Step Conceptual Problem Solving (~15% to 20% of Physics) ──
PHYSICS_MULTI_STEP_BANK: List[dict] = [
    {
        "q": "A force of 20 N acts on a body of mass 4 kg initially at rest. The work done by the force in 3 seconds is:",
        "opts": ["150 J", "225 J", "450 J", "900 J"],
        "ans": 2,
        "topic": "Laws of Motion & Work Energy",
        "subtype": "multi_step",
        "exp": "Step 1: a = F/m = 20/4 = 5 m/s². Step 2: Displacement s = 0.5 * a * t² = 0.5 * 5 * 9 = 22.5 m. Step 3: Work = F * s = 20 * 22.5 = 450 J."
    },
    {
        "q": "If the momentum of a body is increased by 50%, its kinetic energy increases by:",
        "opts": ["50%", "100%", "125%", "150%"],
        "ans": 2,
        "topic": "Work, Energy and Power",
        "subtype": "multi_step",
        "exp": "K = p²/(2m). If p becomes 1.5p, K becomes (1.5)² K = 2.25 K, which represents an increase of (2.25 - 1) * 100 = 125%."
    },
    {
        "q": "The acceleration due to gravity at a height equal to the radius of Earth (R) above the Earth's surface is:",
        "opts": ["g/2", "g/3", "g/4", "g/9"],
        "ans": 2,
        "topic": "Gravitation",
        "subtype": "multi_step",
        "exp": "Using g' = g (R / (R + h))²: for h = R, g' = g (R / 2R)² = g (1/2)² = g/4."
    },
    {
        "q": "The escape velocity from the surface of Earth is 11.2 km/s. If a planet has 4 times the mass and double the radius of Earth, its escape velocity is:",
        "opts": ["11.2 km/s", "15.8 km/s", "22.4 km/s", "31.6 km/s"],
        "ans": 1,
        "topic": "Gravitation",
        "subtype": "multi_step",
        "exp": "v_e = √(2GM/R). For M'=4M and R'=2R: v_e' = √(4/2) v_e = √2 * 11.2 ≈ 1.414 * 11.2 ≈ 15.8 km/s."
    },
    {
        "q": "Two point charges +4 µC and +16 µC are separated by a distance of 12 cm. The distance from the +4 µC charge where the net electric field is zero is:",
        "opts": ["3 cm", "4 cm", "6 cm", "8 cm"],
        "ans": 1,
        "topic": "Electric Charges and Fields",
        "subtype": "multi_step",
        "exp": "q1/x² = q2/(d-x)². √(q2/q1) = (d-x)/x => √(16/4) = 2 = (12-x)/x => 2x = 12-x => 3x = 12 => x = 4 cm."
    },
    {
        "q": "A cell of emf 1.5 V and internal resistance 0.5 Ω is connected across an external resistance of 2.5 Ω. The potential difference across the cell terminals is:",
        "opts": ["1.0 V", "1.25 V", "1.35 V", "1.5 V"],
        "ans": 1,
        "topic": "Current Electricity",
        "subtype": "multi_step",
        "exp": "Current I = E / (R + r) = 1.5 / (2.5 + 0.5) = 0.5 A. Terminal V = E - I*r = 1.5 - (0.5 * 0.5) = 1.25 V."
    },
    {
        "q": "In Young's double slit experiment, if the distance between the slits is reduced to half and the screen distance is doubled, the fringe width becomes:",
        "opts": ["Unchanged", "Doubled", "Halved", "4 times"],
        "ans": 3,
        "topic": "Wave Optics",
        "subtype": "multi_step",
        "exp": "Fringe width β = λD/d. If D' = 2D and d' = d/2, β' = λ(2D)/(d/2) = 4 (λD/d) = 4β."
    },
    {
        "q": "The half-life of a radioactive isotope is 5 days. The fraction of the initial mass that remains undecayed after 20 days is:",
        "opts": ["1/4", "1/8", "1/16", "1/32"],
        "ans": 2,
        "topic": "Nuclei",
        "subtype": "multi_step",
        "exp": "Number of elapsed half-lives n = 20 / 5 = 4. Remaining fraction = (1/2)⁴ = 1/16."
    },
    {
        "q": "A Carnot engine operates between temperatures of 500 K and 300 K. If the sink temperature is decreased by 50 K while the source temperature remains unchanged, the percentage increase in efficiency is:",
        "opts": ["10%", "25%", "50%", "15%"],
        "ans": 1,
        "topic": "Thermodynamics",
        "subtype": "multi_step",
        "exp": "Initial η₁ = 1 - 300/500 = 0.40 (40%). New η₂ = 1 - 250/500 = 0.50 (50%). Increase = (0.50 - 0.40)/0.40 * 100 = 25%."
    },
    {
        "q": "A cylindrical copper wire of resistance 5 Ω is stretched uniformly until its length is tripled. Its new resistance assuming constant density is:",
        "opts": ["15 Ω", "25 Ω", "45 Ω", "60 Ω"],
        "ans": 2,
        "topic": "Current Electricity",
        "subtype": "multi_step",
        "exp": "Volume V = A * L = constant. If L' = 3L, then A' = A/3. New resistance R' = ρ L' / A' = ρ (3L) / (A/3) = 9 R = 9 * 5 = 45 Ω."
    }
]

# ── Physics Bank 3: Pure Theory & Definition-Based (~40% to 50% of Physics) ──
PHYSICS_THEORY_BANK: List[dict] = [
    {
        "q": "Lenz's law of electromagnetic induction is a direct consequence of the law of conservation of:",
        "opts": ["Charge", "Momentum", "Energy", "Angular momentum"],
        "ans": 2,
        "topic": "Electromagnetic Induction",
        "subtype": "theory_definition",
        "exp": "Lenz's law states that induced emf opposes the change that produces it, ensuring mechanical work is converted to electrical energy (Conservation of Energy)."
    },
    {
        "q": "The phenomenon of light wave polarization conclusively proves that light waves are:",
        "opts": ["Longitudinal waves", "Transverse waves", "Stationary waves", "Mechanical waves"],
        "ans": 1,
        "topic": "Wave Optics",
        "subtype": "theory_definition",
        "exp": "Only transverse waves exhibit the property of polarization as vibrations occur perpendicular to the direction of wave propagation."
    },
    {
        "q": "In a p-n junction diode, the barrier potential for Silicon at room temperature is approximately:",
        "opts": ["0.1 V", "0.3 V", "0.7 V", "1.1 V"],
        "ans": 2,
        "topic": "Semiconductor Electronics",
        "subtype": "theory_definition",
        "exp": "The barrier potential for Silicon p-n junction is ~0.7 V (for Germanium it is ~0.3 V)."
    },
    {
        "q": "According to Gauss's law in electrostatics, the net electric flux through any closed Gaussian surface enclosing zero net charge is:",
        "opts": ["Infinite", "Zero", "Dependent on shape", "Negative"],
        "ans": 1,
        "topic": "Electric Charges and Fields",
        "subtype": "theory_definition",
        "exp": "By Gauss's theorem, total electric flux Φ_E = q_enclosed / ε₀. If q_enclosed = 0, Φ_E = 0 regardless of surface geometry."
    },
    {
        "q": "In the photoelectric effect, the maximum kinetic energy of the emitted photoelectrons depends exclusively on:",
        "opts": ["Intensity of incident light", "Frequency of incident light", "Area of the metal surface", "Time of exposure"],
        "ans": 1,
        "topic": "Dual Nature of Radiation and Matter",
        "subtype": "theory_definition",
        "exp": "Einstein's photoelectric equation K_max = hν - Φ shows that kinetic energy depends linearly on frequency ν, independent of intensity."
    },
    {
        "q": "Bohr's quantization postulate states that an electron orbits in stable non-radiating states where its orbital angular momentum is:",
        "opts": ["An integral multiple of h / (2π)", "An odd multiple of h / π", "Independent of Planck constant", "An integral multiple of 2π / h"],
        "ans": 0,
        "topic": "Atoms",
        "subtype": "theory_definition",
        "exp": "Bohr's condition: L = m v r = n h / (2π), where n is the principal quantum number (1, 2, 3...)."
    },
    {
        "q": "The work done by a static magnetic field on a charged particle moving through it is always:",
        "opts": ["Positive", "Negative", "Zero", "Equal to q v B"],
        "ans": 2,
        "topic": "Moving Charges and Magnetism",
        "subtype": "theory_definition",
        "exp": "The magnetic Lorentz force F = q(v × B) is always perpendicular to velocity v. Hence, power P = F · v = 0, and work done is zero."
    },
    {
        "q": "To convert a moving coil galvanometer into a voltmeter, what must be connected with the galvanometer?",
        "opts": ["A high resistance in series", "A low resistance in parallel", "A high resistance in parallel", "A low resistance in series"],
        "ans": 0,
        "topic": "Moving Charges and Magnetism",
        "subtype": "theory_definition",
        "exp": "A high multiplier resistance R is connected in series with the galvanometer coil to ensure minimal current is drawn from the circuit."
    },
    {
        "q": "To minimize energy dissipation caused by eddy currents, the soft iron core of a transformer is:",
        "opts": ["Solid and unlaminated", "Laminated with insulating varnish", "Made of copper", "Hollow"],
        "ans": 1,
        "topic": "Alternating Current",
        "subtype": "theory_definition",
        "exp": "Laminating the core into thin sheets separated by varnish restricts the path of eddy currents, significantly lowering I²R power loss."
    },
    {
        "q": "Which of the following electromagnetic radiations possesses the highest frequency and shortest wavelength?",
        "opts": ["Radio waves", "Microwaves", "X-rays", "Gamma rays"],
        "ans": 3,
        "topic": "Electromagnetic Waves",
        "subtype": "theory_definition",
        "exp": "Gamma rays have the shortest wavelength (< 10⁻¹² m) and highest photon energy/frequency in the electromagnetic spectrum."
    },
    {
        "q": "Total internal reflection (TIR) can occur only when a light ray travels:",
        "opts": ["From rarer to denser medium at any angle", "From denser to rarer medium at angle greater than critical angle", "Along the normal", "In vacuum only"],
        "ans": 1,
        "topic": "Ray Optics",
        "subtype": "theory_definition",
        "exp": "TIR requires light to propagate from an optically denser to rarer medium with angle of incidence i > critical angle θ_c."
    },
    {
        "q": "In an intrinsic semiconductor at absolute zero (0 K), the conduction band is completely empty and it behaves as:",
        "opts": ["A superconductor", "A perfect insulator", "A good conductor", "A ferromagnetic material"],
        "ans": 1,
        "topic": "Semiconductor Electronics",
        "subtype": "theory_definition",
        "exp": "At 0 K, all valence electrons are bound in covalent bonds; zero thermal carriers exist in the conduction band, acting as an insulator."
    },
    {
        "q": "The nuclear binding energy per nucleon curve attains its broad maximum (highest stability) near the mass number of:",
        "opts": ["Helium (A = 4)", "Carbon (A = 12)", "Iron (A = 56)", "Uranium (A = 238)"],
        "ans": 2,
        "topic": "Nuclei",
        "subtype": "theory_definition",
        "exp": "Binding energy per nucleon reaches ~8.75 MeV/nucleon near Fe-56 (mass number A ≈ 56), making it the most stable nucleus."
    },
    {
        "q": "When unpolarized light is incident on a transparent boundary at Brewster's angle, the reflected and refracted rays are:",
        "opts": ["Parallel to each other", "Perpendicular to each other", "Antiparallel", "At 45° to each other"],
        "ans": 1,
        "topic": "Wave Optics",
        "subtype": "theory_definition",
        "exp": "At Brewster's angle i_B, the reflected and refracted rays are mutually perpendicular: i_B + r = 90°."
    },
    {
        "q": "An ideal voltmeter and an ideal ammeter must have electrical resistances respectively equal to:",
        "opts": ["Zero and Infinite", "Infinite and Zero", "Zero and Zero", "Infinite and Infinite"],
        "ans": 1,
        "topic": "Current Electricity",
        "subtype": "theory_definition",
        "exp": "An ideal voltmeter draws zero current (infinite resistance); an ideal ammeter introduces zero voltage drop (zero resistance)."
    }
]

# Aliases for backwards compatibility
PHYSICS_NUMERICAL_BANK: List[dict] = PHYSICS_DIRECT_FORMULA_BANK + PHYSICS_MULTI_STEP_BANK

# ── Chemistry Bank 1: Physical Chemistry Numericals (~8% to 12% of Chemistry) ──
CHEMISTRY_NUMERICAL_BANK: List[dict] = [
    {
        "q": "What is the mass percentage of carbon in carbon dioxide (CO₂)? (Atomic masses: C = 12, O = 16)",
        "opts": ["12.00%", "27.27%", "72.73%", "33.33%"],
        "ans": 1,
        "topic": "Some Basic Concepts of Chemistry",
        "subtype": "physical_numerical",
        "exp": "Molar mass of CO₂ = 12 + 2(16) = 44 g/mol. Mass % of C = (12 / 44) * 100 = 27.27%."
    },
    {
        "q": "For a chemical reaction, ΔH = +40 kJ/mol and ΔS = +100 J/(K·mol). The temperature above which the reaction becomes spontaneous is:",
        "opts": ["273 K", "300 K", "400 K", "500 K"],
        "ans": 2,
        "topic": "Thermodynamics",
        "subtype": "physical_numerical",
        "exp": "For spontaneity, ΔG = ΔH - TΔS < 0 => T > ΔH / ΔS = (40000 J/mol) / (100 J/K·mol) = 400 K."
    },
    {
        "q": "The standard EMF of the galvanic cell Zn | Zn²⁺ || Cu²⁺ | Cu with E°(Zn²⁺/Zn) = -0.76 V and E°(Cu²⁺/Cu) = +0.34 V is:",
        "opts": ["+0.42 V", "+1.10 V", "-1.10 V", "+0.76 V"],
        "ans": 1,
        "topic": "Electrochemistry",
        "subtype": "physical_numerical",
        "exp": "E°_cell = E°_cathode - E°_anode = 0.34 - (-0.76) = +1.10 V."
    },
    {
        "q": "If the rate constant of a first-order chemical reaction is 6.93 × 10⁻³ s⁻¹, the half-life period (t₁/₂) of the reaction is:",
        "opts": ["10 s", "50 s", "100 s", "200 s"],
        "ans": 2,
        "topic": "Chemical Kinetics",
        "subtype": "physical_numerical",
        "exp": "For a first order reaction, t₁/₂ = 0.693 / k = 0.693 / (6.93 × 10⁻³) = 100 seconds."
    },
    {
        "q": "The depression in freezing point for a 0.1 molal aqueous solution of a non-volatile non-electrolyte solute is (K_f for water = 1.86 K·kg/mol):",
        "opts": ["0.0186 K", "0.186 K", "1.86 K", "3.72 K"],
        "ans": 1,
        "topic": "Solutions",
        "subtype": "physical_numerical",
        "exp": "ΔT_f = K_f * m = 1.86 K·kg/mol * 0.1 mol/kg = 0.186 K."
    },
    {
        "q": "The osmotic pressure of a solution containing 6.0 g of urea (molar mass = 60 g/mol) in 1.0 L of water at 300 K is (R = 0.0821 L·atm/(mol·K)):",
        "opts": ["1.23 atm", "2.46 atm", "4.92 atm", "0.246 atm"],
        "ans": 1,
        "topic": "Solutions",
        "subtype": "physical_numerical",
        "exp": "Moles of urea = 6/60 = 0.1 mol. Molarity C = 0.1 M. π = C R T = 0.1 * 0.0821 * 300 = 2.46 atm."
    },
    {
        "q": "The quantity of electricity in Coulombs required for the complete reduction of 1 mole of Al³⁺ to metallic Al is (1 Faraday = 96500 C):",
        "opts": ["96,500 C", "193,000 C", "289,500 C", "386,000 C"],
        "ans": 2,
        "topic": "Electrochemistry",
        "subtype": "physical_numerical",
        "exp": "Al³⁺ + 3e⁻ -> Al. 1 mole of Al³⁺ requires 3 Faradays = 3 * 96,500 = 289,500 C."
    },
    {
        "q": "For a zero-order reaction A -> Products with rate constant k = 0.2 mol/(L·s), the time required for the concentration of A to decrease from 2.0 M to 1.0 M is:",
        "opts": ["2.5 s", "5.0 s", "10.0 s", "0.5 s"],
        "ans": 1,
        "topic": "Chemical Kinetics",
        "subtype": "physical_numerical",
        "exp": "For zero-order: [A]₀ - [A] = k * t => 2.0 - 1.0 = 0.2 * t => t = 1.0 / 0.2 = 5.0 s."
    }
]

# ── Chemistry Bank 2: Direct Fact, Memory & Reaction-Based (~88% to 92% of Chemistry) ──
CHEMISTRY_FACT_REACTION_BANK: List[dict] = [
    {
        "q": "The maximum number of electrons that can be accommodated in a subshell with azimuthal quantum number l = 2 (d-subshell) is:",
        "opts": ["2", "6", "10", "14"],
        "ans": 2,
        "topic": "Structure of Atom",
        "subtype": "fact_reaction",
        "exp": "Number of electrons in a subshell = 2(2l + 1). For l = 2: 2(2*2 + 1) = 10 electrons."
    },
    {
        "q": "Which of the following molecules has a square planar geometry according to VSEPR theory?",
        "opts": ["CH₄", "SF₄", "XeF₄", "NH₄⁺"],
        "ans": 2,
        "topic": "Chemical Bonding",
        "subtype": "fact_reaction",
        "exp": "XeF₄ has 4 bond pairs and 2 lone pairs on the central Xe atom (sp³d² hybridization), giving a square planar geometry."
    },
    {
        "q": "When phenol is treated with chloroform (CHCl₃) in the presence of aqueous NaOH followed by acid hydrolysis, the major product formed is:",
        "opts": ["Salicylic acid", "Salicylaldehyde", "Benzoic acid", "Picric acid"],
        "ans": 1,
        "topic": "Alcohols, Phenols and Ethers",
        "subtype": "fact_reaction",
        "exp": "This is the Reimer-Tiemann reaction where electrophilic dichlorocarbene (:CCl₂) attacks phenol to synthesize salicylaldehyde."
    },
    {
        "q": "The reaction of sodium phenoxide with carbon dioxide (CO₂) under pressure at 400 K followed by acidification produces salicylic acid. This reaction is known as:",
        "opts": ["Kolbe's reaction", "Reimer-Tiemann reaction", "Friedel-Crafts acylation", "Wurtz reaction"],
        "ans": 0,
        "topic": "Alcohols, Phenols and Ethers",
        "subtype": "fact_reaction",
        "exp": "Kolbe's synthesis involves electrophilic carboxylation of phenoxide ion by CO₂ followed by protonation to yield ortho-hydroxybenzoic acid (salicylic acid)."
    },
    {
        "q": "Lucas reagent, used to distinguish between primary, secondary, and tertiary alcohols, consists of a mixture of:",
        "opts": ["Anhydrous ZnCl₂ and conc. HCl", "Dilute HCl and Zn dust", "Conc. H₂SO₄ and KMnO₄", "AlCl₃ and conc. HNO₃"],
        "ans": 0,
        "topic": "Alcohols, Phenols and Ethers",
        "subtype": "fact_reaction",
        "exp": "Lucas reagent is an equimolar solution of anhydrous ZnCl₂ in concentrated HCl. 3° alcohols form immediate turbidity, 2° within 5 minutes, 1° do not react at room temperature."
    },
    {
        "q": "Which of the following aldehydes does NOT undergo Aldol condensation due to the lack of α-hydrogen atoms?",
        "opts": ["Acetaldehyde", "Propanal", "Benzaldehyde", "Butanal"],
        "ans": 2,
        "topic": "Aldehydes, Ketones and Carboxylic Acids",
        "subtype": "fact_reaction",
        "exp": "Benzaldehyde (C₆H₅CHO) and Formaldehyde (HCHO) lack α-hydrogen atoms and undergo the Cannizzaro disproportionation reaction instead of Aldol condensation."
    },
    {
        "q": "The reduction of aldehydes and ketones to corresponding alkanes using zinc amalgam (Zn/Hg) and concentrated hydrochloric acid is called:",
        "opts": ["Wolff-Kishner reduction", "Clemmensen reduction", "Rosenmund reduction", "Stephen reduction"],
        "ans": 1,
        "topic": "Aldehydes, Ketones and Carboxylic Acids",
        "subtype": "fact_reaction",
        "exp": "Clemmensen reduction employs Zn(Hg) and conc. HCl to convert carbonyl >C=O groups directly into methylene -CH₂- groups."
    },
    {
        "q": "Lanthanoid contraction observed in the inner transition series is primarily caused by:",
        "opts": ["Imperfection of 4f electron shielding", "Increase in nuclear charge alone", "Complete filling of 5d subshell", "High shielding effect of 4f electrons"],
        "ans": 0,
        "topic": "d and f Block Elements",
        "subtype": "fact_reaction",
        "exp": "Due to the diffused radial shapes of 4f orbitals, 4f electrons shield outer electrons very poorly against increasing nuclear charge, causing uniform contraction of atomic radii."
    },
    {
        "q": "When excess silver nitrate (AgNO₃) solution is added to 1 mole of coordination compound [Co(NH₃)₆]Cl₃, how many moles of AgCl are precipitated?",
        "opts": ["1 mole", "2 moles", "3 moles", "0 moles"],
        "ans": 2,
        "topic": "Coordination Compounds",
        "subtype": "fact_reaction",
        "exp": "All three chloride ions are outside the coordination sphere as ionizable counter-ions, precipitating 3 moles of AgCl per mole of complex."
    },
    {
        "q": "Which of the following 3d-transition metal ions is diamagnetic due to having zero unpaired d-electrons?",
        "opts": ["Ti³⁺", "Fe²⁺", "Sc³⁺", "Cu²⁺"],
        "ans": 2,
        "topic": "d and f Block Elements",
        "subtype": "fact_reaction",
        "exp": "Scandium has atomic number 21 ([Ar] 3d¹ 4s²). Sc³⁺ has electronic configuration [Ar] 3d⁰ with 0 unpaired electrons, making it diamagnetic."
    },
    {
        "q": "The basicity (number of replaceable ionizable protons) of orthophosphoric acid (H₃PO₄) is:",
        "opts": ["1", "2", "3", "4"],
        "ans": 2,
        "topic": "p-Block Elements",
        "subtype": "fact_reaction",
        "exp": "H₃PO₄ has three P-OH bonds and one P=O bond, making it a tribasic acid with basicity = 3."
    },
    {
        "q": "During the industrial manufacture of ammonia by Haber's process, the promoter added to enhance the activity of iron catalyst is:",
        "opts": ["Molybdenum (Mo)", "Platinum (Pt)", "Nickel (Ni)", "Copper (Cu)"],
        "ans": 0,
        "topic": "p-Block Elements",
        "subtype": "fact_reaction",
        "exp": "In Haber's process, finely divided iron acts as the catalyst while molybdenum (or K₂O/Al₂O₃) acts as a promoter to increase catalytic efficiency."
    },
    {
        "q": "Williamson synthesis involves an SN2 nucleophilic substitution reaction between an alkyl halide and:",
        "opts": ["Sodium alkoxide", "Carboxylic acid", "Grignard reagent", "Ester"],
        "ans": 0,
        "topic": "Alcohols, Phenols and Ethers",
        "subtype": "fact_reaction",
        "exp": "R-X + R'-O⁻ Na⁺ -> R-O-R' + NaX. Williamson synthesis prepares symmetrical and unsymmetrical ethers via nucleophilic attack of alkoxide ion on primary alkyl halide."
    },
    {
        "q": "Which of the following nitrogenous bases is found in RNA but is completely absent in DNA?",
        "opts": ["Thymine", "Uracil", "Guanine", "Cytosine"],
        "ans": 1,
        "topic": "Biomolecules",
        "subtype": "fact_reaction",
        "exp": "RNA contains Uracil (U) which pairs with Adenine (A), whereas DNA contains Thymine (T) instead of Uracil."
    },
    {
        "q": "Denaturation of proteins caused by physical changes (heat) or chemical changes (pH) destroys secondary and tertiary structures while leaving which structure intact?",
        "opts": ["Primary structure", "Quaternary structure", "Alpha-helix", "Beta-pleated sheet"],
        "ans": 0,
        "topic": "Biomolecules",
        "subtype": "fact_reaction",
        "exp": "Denaturation breaks weak hydrogen and disulfide bonds stabilizing 2° and 3° conformations, but the covalent peptide bonds of the primary sequence remain intact."
    },
    {
        "q": "The temporary bleaching action of sulfur dioxide (SO₂) on colored organic matter occurs by the process of:",
        "opts": ["Oxidation", "Reduction", "Hydrolysis", "Dehydration"],
        "ans": 1,
        "topic": "p-Block Elements",
        "subtype": "fact_reaction",
        "exp": "SO₂ bleaches coloring matter by reduction (SO₂ + 2H₂O -> H₂SO₄ + 2[H]). Atmospheric oxygen gradually re-oxidizes the bleached material, making it temporary."
    },
    {
        "q": "According to VSEPR theory, the molecular shape of chlorine trifluoride (ClF₃) is:",
        "opts": ["Trigonal planar", "T-shaped", "Tetrahedral", "Trigonal bipyramidal"],
        "ans": 1,
        "topic": "Chemical Bonding",
        "subtype": "fact_reaction",
        "exp": "ClF₃ has 3 bond pairs and 2 lone pairs on central Cl atom in equatorial positions of a trigonal bipyramid, resulting in a slightly bent T-shape."
    },
    {
        "q": "Which of the following ligands acts as an ambidentate ligand capable of coordinating through two different donor atoms?",
        "opts": ["H₂O", "NH₃", "SCN⁻", "EDTA⁴⁻"],
        "ans": 2,
        "topic": "Coordination Compounds",
        "subtype": "fact_reaction",
        "exp": "Thiocyanate ion (SCN⁻) can coordinate through sulfur (M-SCN, thiocyanato) or nitrogen (M-NCS, isothiocyanato), classifying it as an ambidentate ligand."
    }
]

# Alias for backwards compatibility
CHEMISTRY_BANK: List[dict] = CHEMISTRY_NUMERICAL_BANK + CHEMISTRY_FACT_REACTION_BANK


from .mathematics_bank import MATHEMATICS_BANK
from .biology_bank import BIOLOGY_BANK


def _option_index(letter: str)-> int:
    """Convert A/B/C/D or 1/2/3/4 to 0-based index."""
    letter = letter.upper()
    if letter in "ABCD":
        return ord(letter) - ord("A")
    if letter in "1234":
        return int(letter) - 1
    return 0


def _extract_answer_keys(text: str)-> dict[int, int]:
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


def extract_mcqs_from_text(text: str, topic: str = "General")-> List[dict]:
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


def infer_question_subtype(q_text: str, opts: List[str], subject: str = "General") -> str:
    """Infer the KCET question subtype based on subject and question content."""
    text_full = (q_text + " " + " ".join(opts)).lower()
    subj_lower = subject.lower()

    if "physic" in subj_lower:
        # Check if question has calculation / formula patterns
        has_num = bool(re.search(r"\b\d+(\.\d+)?\s*(m/s|m/s²|n|j|w|v|a|hz|kg|cm|mm|µc|uf|pf|ohm|omega|t|h|ev|diopter|d)\b", text_full, re.IGNORECASE))
        has_math_op = bool(re.search(r"[\d\.\+\-\*/=√²³]{2,}", text_full))

        multi_step_keywords = [
            "then", "increased by", "decreased by", "ratio", "if the",
            "striking", "combination", "work done by", "neutral point",
            "fringe width", "carnot", "stretched", "resonance", "maximum height"
        ]
        if (has_num or has_math_op) and any(kw in text_full for kw in multi_step_keywords):
            return "multi_step"
        elif has_num or has_math_op or "calculate" in text_full or "value of" in text_full or "equal to" in text_full:
            return "direct_formula"
        return "theory_definition"

    elif "chem" in subj_lower:
        has_num = bool(re.search(r"\b\d+(\.\d+)?\s*(g/mol|kj/mol|j/k|molar|mol/l|atm|s⁻¹|s\^-1|k|v|coulomb|ml|mol|m)\b", text_full, re.IGNORECASE))
        num_keywords = [
            "molarity", "molality", "normality", "mole fraction", "molar mass",
            "percentage by mass", "mass percentage", "half-life", "freezing point",
            "osmotic pressure", "rate constant", "emf of cell", "coulombs",
            "zero-order", "first-order", "depression in", "elevation in",
            "calculate the", "determine the mass", "volume of", "solubility product",
            "equilibrium constant", "activation energy", "faraday's constant", "ph of"
        ]
        if has_num and any(kw in text_full for kw in num_keywords) or any(kw in text_full for kw in ["molarity", "molality", "osmotic pressure", "half-life", "rate constant"]):
            return "physical_numerical"
        
        theory_keywords = [
            "definition", "law", "principle", "rule", "theory", "vsepr",
            "hybridization", "hybridisation", "isoelectronic", "aufbau",
            "hund's", "pauli", "le chatelier", "coordination number", "isomerism"
        ]
        if any(kw in text_full for kw in theory_keywords):
            return "theory_definition"

        return "fact_reaction"

    elif "math" in subj_lower:
        multi_step_math = [
            "area bounded", "differential equation", "maxima", "minima", "tangent and normal",
            "shortest distance", "plane passing through", "angle between planes", "bayes",
            "locus", "conic", "eccentricity", "coordinates of", "equation of the circle"
        ]
        if any(kw in text_full for kw in multi_step_math):
            return "multi_step"

        concept_math = [
            "reflexive", "symmetric", "transitive", "equivalence", "bijection", "one-one", "onto",
            "tautology", "contradiction", "truth table", "domain of", "range of", "identity element"
        ]
        if any(kw in text_full for kw in concept_math):
            return "concept_application"

        return "direct_formula"

    elif "bio" in subj_lower:
        concept_bio = [
            "pedigree", "dihybrid", "monohybrid", "ratio", "cross", "genotype",
            "phenotype", "recombinant dna", "transcription", "translation",
            "replication fork", "lac operon", "pcr", "mechanism of", "pathway"
        ]
        if any(kw in text_full for kw in concept_bio):
            return "concept_application"

        theory_bio = [
            "defined as", "principle of", "cell theory", "hardy-weinberg",
            "ecological succession", "mitosis", "meiosis", "trophic level"
        ]
        if any(kw in text_full for kw in theory_bio):
            return "theory_definition"

        return "fact_reaction"

    return "theory_definition"


def _generate_subject_variations(
    topic: str,
    needed: int,
    used_texts: set[str],
    subtype_filter: Optional[str] = None,
    allowed_topics: Optional[Iterable[str]] = None,
) -> List[dict]:
    """Generates authentic, high-quality KCET syllabus MCQs for any shortfall,
    strictly partitioned by blueprint subtype and concept-level formula deduplication.
    """
    topic_lower = topic.lower()
    generated: List[dict] = []
    allowed_list = list(allowed_topics) if allowed_topics else None
    used_fingerprints = {normalize_question_fingerprint(t) for t in used_texts if t}
    used_concepts = {extract_concept_fingerprint(t) for t in used_texts if t}

    def _add_q(q_dict: dict) -> bool:
        q_text = q_dict.get("q", "").strip()
        if not q_text or q_text in used_texts:
            return False
        if allowed_list and not is_topic_matching(q_dict.get("topic", ""), allowed_list):
            return False
        fp = normalize_question_fingerprint(q_text)
        concept_fp = extract_concept_fingerprint(q_text)
        if not fp or fp in used_fingerprints or concept_fp in used_concepts:
            return False
        if is_valid_question(q_text, q_dict.get("opts", []), subject=topic):
            generated.append(q_dict)
            used_texts.add(q_text)
            used_fingerprints.add(fp)
            used_concepts.add(concept_fp)
            return len(generated) >= needed
        return False

    # ── 1. Physics Variations ────────────────────────────────────────────────
    if "physic" in topic_lower:
        # [Direct Formula Generators]
        if not subtype_filter or subtype_filter == "direct_formula":
            # 1. Projectile maximum height
            for u in [10, 15, 20, 25, 30, 35, 40, 45, 50, 60]:
                for th in [30, 45, 60]:
                    sin_val = 0.5 if th == 30 else (0.7071 if th == 45 else 0.866)
                    h_val = round(((u * sin_val) ** 2) / 20.0, 1)
                    q = {
                        "q": f"A projectile is launched with an initial velocity of {u} m/s at an angle of {th}° with the horizontal. The maximum height reached by the projectile is (take g = 10 m/s²):",
                        "opts": [f"{h_val} m", f"{round(h_val * 1.5, 1)} m", f"{round(h_val * 0.5, 1)} m", f"{round((u**2) / 20.0, 1)} m"],
                        "ans": 0,
                        "topic": "Motion in a Plane",
                        "subtype": "direct_formula",
                        "exp": f"Using H_max = (u sin θ)² / (2g): for u = {u} m/s and θ = {th}°, H_max = ({u} * {sin_val})² / 20 = {h_val} m."
                    }
                    if _add_q(q): return generated

            # 2. Capacitor stored electrostatic energy
            for C in [2, 4, 5, 8, 10, 15, 20, 25, 50, 100]:
                for V in [10, 20, 50, 100, 150, 200, 220, 400]:
                    u_val = round(0.5 * C * (V**2) * 1e-3, 2)
                    q = {
                        "q": f"A capacitor of capacitance {C} µF is charged to a potential difference of {V} V. The electrostatic energy stored in the electric field of the capacitor is:",
                        "opts": [f"{u_val} mJ", f"{round(C * V * 1e-3, 2)} mJ", f"{round(0.5 * C * V * 1e-3, 2)} mJ", f"{round(u_val * 2, 2)} mJ"],
                        "ans": 0,
                        "topic": "Electrostatic Potential and Capacitance",
                        "subtype": "direct_formula",
                        "exp": f"Energy U = (1/2) C V² = 0.5 * {C}×10⁻⁶ * ({V})² = {u_val} mJ."
                    }
                    if _add_q(q): return generated

            # 3. Resistors in parallel
            r_pairs = [
                (6, 12), (10, 40), (20, 30), (15, 30), (8, 24), (12, 24), (14, 28), (18, 36),
                (5, 20), (10, 15), (20, 80), (30, 60), (4, 12), (9, 18), (16, 48), (25, 75),
                (12, 60), (40, 60), (50, 50), (100, 100), (3, 6), (7, 14), (20, 20), (30, 30)
            ]
            for r1, r2 in r_pairs:
                r_eq = round((r1 * r2) / (r1 + r2), 2)
                q = {
                    "q": f"Two resistors of resistances {r1} Ω and {r2} Ω are connected in parallel across an ideal voltage source. The equivalent resistance of the combination is:",
                    "opts": [f"{r_eq} Ω", f"{r1 + r2} Ω", f"{round(abs(r1 - r2), 1)} Ω", f"{round((r1 + r2) / 2, 1)} Ω"],
                    "ans": 0,
                    "topic": "Current Electricity",
                    "subtype": "direct_formula",
                    "exp": f"For resistors in parallel, 1/R_eq = 1/R1 + 1/R2 => R_eq = ({r1} * {r2}) / ({r1 + r2}) = {r_eq} Ω."
                }
                if _add_q(q): return generated

            # 4. Refraction speed of light
            media = [
                (1.33, "water"), (1.5, "crown glass"), (1.6, "flint glass"), (2.42, "diamond"),
                (1.46, "fused quartz"), (1.65, "dense flint glass"), (1.54, "rock salt"),
                (1.77, "sapphire"), (1.31, "ice"), (1.36, "ethyl alcohol")
            ]
            for n, med in media:
                v_val = round(3.0 / n, 2)
                q = {
                    "q": f"The refractive index of {med} is {n}. Taking the speed of light in vacuum c = 3.0 × 10⁸ m/s, the speed of light in this medium is:",
                    "opts": [f"{v_val} × 10⁸ m/s", f"{round(3.0 * n, 2)} × 10⁸ m/s", f"{round(1.5 / n, 2)} × 10⁸ m/s", "3.0 × 10⁸ m/s"],
                    "ans": 0,
                    "topic": "Ray Optics",
                    "subtype": "direct_formula",
                    "exp": f"v = c / n = (3.0 × 10⁸) / {n} = {v_val} × 10⁸ m/s."
                }
                if _add_q(q): return generated

            # 5. Lens power
            lens_data = [
                (10, "convex"), (20, "convex"), (25, "convex"), (40, "convex"), (50, "convex"), (100, "convex"),
                (-10, "concave"), (-20, "concave"), (-25, "concave"), (-40, "concave"), (-50, "concave"), (-100, "concave"),
                (5, "convex"), (-5, "concave"), (12.5, "convex"), (-12.5, "concave")
            ]
            for f, l_type in lens_data:
                p_val = round(100.0 / abs(f), 1)
                sign = "+" if f > 0 else "-"
                opp_sign = "-" if f > 0 else "+"
                q = {
                    "q": f"A {l_type} lens has a focal length of {abs(f)} cm. The optical power of the lens in diopters (D) is:",
                    "opts": [f"{sign}{p_val} D", f"{opp_sign}{p_val} D", f"{sign}{round(p_val * 0.1, 2)} D", f"{round(abs(f) / 100.0, 2)} D"],
                    "ans": 0,
                    "topic": "Ray Optics",
                    "subtype": "direct_formula",
                    "exp": f"Power P = 100 / f(cm) = 100 / ({f}) = {sign}{p_val} D."
                }
                if _add_q(q): return generated

            # 6. Step-down transformer turns ratio
            xformer_data = [
                (1000, 100, 220), (500, 50, 240), (800, 200, 220), (1200, 300, 240), (600, 150, 220),
                (2000, 100, 220), (1000, 250, 200), (500, 100, 250), (400, 40, 220), (1500, 150, 240),
                (800, 100, 240), (1000, 200, 250), (1000, 50, 220), (2200, 110, 220), (500, 25, 200)
            ]
            for Np, Ns, Vp in xformer_data:
                Vs = round(Vp * Ns / Np, 1)
                q = {
                    "q": f"An ideal step-down transformer has {Np} turns in its primary coil and {Ns} turns in its secondary coil. When connected to a {Vp} V AC mains, the secondary output voltage is:",
                    "opts": [f"{Vs} V", f"{round(Vp * Np / Ns, 1)} V", f"{Vp} V", f"{round(Vs * 2, 1)} V"],
                    "ans": 0,
                    "topic": "Alternating Current",
                    "subtype": "direct_formula",
                    "exp": f"Vs / Vp = Ns / Np => Vs = {Vp} * ({Ns} / {Np}) = {Vs} V."
                }
                if _add_q(q): return generated

            # 7. Inductive reactance
            ind_data = [
                (0.1, 50), (0.2, 50), (0.05, 100), (0.5, 50), (0.25, 60), (0.15, 50), (0.4, 50),
                (0.3, 50), (0.02, 100), (0.01, 200), (0.08, 50), (0.6, 50), (1.0, 50), (0.04, 50)
            ]
            for L, freq in ind_data:
                xl = round(2 * 3.1416 * freq * L, 1)
                q = {
                    "q": f"An AC circuit contains an inductor of inductance {L} H operating at a supply frequency of {freq} Hz. The inductive reactance (X_L) of the coil is approximately:",
                    "opts": [f"{xl} Ω", f"{round(xl * 0.5, 1)} Ω", f"{round(xl * 2, 1)} Ω", f"{round(100 / xl, 2)} Ω"],
                    "ans": 0,
                    "topic": "Alternating Current",
                    "subtype": "direct_formula",
                    "exp": f"X_L = 2π f L = 2 * 3.1416 * {freq} * {L} ≈ {xl} Ω."
                }
                if _add_q(q): return generated

            # 8. De Broglie wavelength of accelerated electron
            voltages = [25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 400, 625, 900]
            for V_volts in voltages:
                lam = round(1.227 / (V_volts ** 0.5), 3)
                q = {
                    "q": f"An electron is accelerated from rest through a potential difference of {V_volts} V in an electric field. The de Broglie wavelength associated with the electron is:",
                    "opts": [f"{lam} nm", f"{round(lam * 10, 3)} nm", f"{round(lam * 0.1, 3)} nm", f"{round(lam * 2, 3)} nm"],
                    "ans": 0,
                    "topic": "Dual Nature of Radiation and Matter",
                    "subtype": "direct_formula",
                    "exp": f"λ = 1.227 / √V nm = 1.227 / √{V_volts} = {lam} nm."
                }
                if _add_q(q): return generated

            # 9. Center magnetic field of circular loop
            loop_data = [
                (2, 5), (5, 10), (10, 20), (4, 8), (3, 6), (8, 16), (1, 4), (6, 12),
                (12, 24), (5, 25), (2, 10), (4, 20), (8, 40), (10, 50)
            ]
            for I_curr, R_rad in loop_data:
                b_val = round((4 * 3.1416 * 1e-7 * I_curr / (2 * R_rad * 0.01)) * 1e6, 2)
                q = {
                    "q": f"A circular coil of radius {R_rad} cm carries a steady electric current of {I_curr} A. The magnitude of magnetic field at the centre of the coil is (take μ₀ = 4π × 10⁻⁷ T·m/A):",
                    "opts": [f"{b_val} µT", f"{round(b_val * 2, 2)} µT", f"{round(b_val * 0.5, 2)} µT", "12.5 µT"],
                    "ans": 0,
                    "topic": "Moving Charges and Magnetism",
                    "subtype": "direct_formula",
                    "exp": f"B = μ₀ I / (2R) = (4π × 10⁻⁷ * {I_curr}) / (2 * {R_rad * 0.01}) = {b_val} µT."
                }
                if _add_q(q): return generated

            # 10. Electric charge and current: Q = I * t
            curr_data = [(2, 30), (5, 60), (3, 40), (4, 25), (10, 20), (1.5, 60), (0.5, 120), (6, 15), (2.5, 40), (8, 10)]
            for I_amp, t_sec in curr_data:
                q_coul = round(I_amp * t_sec, 1)
                q = {
                    "q": f"A steady electric current of {I_amp} A flows through the filament of a lamp for {t_sec} seconds. The total electric charge that flows through any cross-section of the conductor is:",
                    "opts": [f"{q_coul} C", f"{round(q_coul * 2, 1)} C", f"{round(q_coul * 0.5, 1)} C", f"{round(I_amp / t_sec, 2)} C"],
                    "ans": 0,
                    "topic": "Current Electricity",
                    "subtype": "direct_formula",
                    "exp": f"Q = I * t = {I_amp} A * {t_sec} s = {q_coul} C."
                }
                if _add_q(q): return generated

        # [Multi-Step Problem Solving Generators]
        if not subtype_filter or subtype_filter == "multi_step":
            # 1. Wire stretching resistance: R' = n² * R
            for R in [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]:
                for n in [2, 3, 4, 5]:
                    r_new = R * (n ** 2)
                    q = {
                        "q": f"A uniform cylindrical copper wire of resistance {R} Ω is drawn out so that its length increases uniformly by a factor of {n}. Assuming its density remains constant, its new resistance will be:",
                        "opts": [f"{r_new} Ω", f"{R * n} Ω", f"{round(R / n, 1)} Ω", f"{round(R / (n * n), 2)} Ω"],
                        "ans": 0,
                        "topic": "Current Electricity",
                        "subtype": "multi_step",
                        "exp": f"When a wire of initial resistance R is stretched by factor n, area decreases by n. Hence R' = n² R = {n**2} * {R} = {r_new} Ω."
                    }
                    if _add_q(q): return generated

            # 2. Percentage increase in momentum and kinetic energy
            for p_pct in [10, 20, 25, 30, 40, 50, 60, 75, 80, 100]:
                for m in [1, 2, 4, 5]:
                    k_pct = round(((1 + p_pct / 100.0)**2 - 1) * 100.0, 1)
                    q = {
                        "q": f"If the linear momentum of a particle of mass {m} kg is increased by {p_pct}%, the percentage increase in its kinetic energy is:",
                        "opts": [f"{k_pct}%", f"{p_pct}%", f"{p_pct * 2}%", f"{round(((1 + p_pct/100.0)**2)*100.0, 1)}%"],
                        "ans": 0,
                        "topic": "Work, Energy and Power",
                        "subtype": "multi_step",
                        "exp": f"Since K = p²/(2m), an increase of p by {p_pct}% gives K' = (1 + {p_pct/100.0})² K, leading to an increase of {k_pct}%."
                    }
                    if _add_q(q): return generated

            # 3. Radioactive decay remaining fraction
            decay_data = [
                (5, 15), (4, 12), (10, 30), (3, 9), (8, 24), (2, 8), (6, 24), (7, 21),
                (12, 36), (15, 45), (20, 60), (25, 75), (30, 90), (5, 20), (10, 40)
            ]
            for th, days in decay_data:
                n_half = days // th
                denom = 2 ** n_half
                q = {
                    "q": f"A radioactive nucleus has a half-life of {th} days. Starting with an initial activity A₀, what fraction of the original nuclei remains undecayed after {days} days?",
                    "opts": [f"1/{denom}", f"1/{denom * 2}", f"1/{n_half}", f"{n_half}/{n_half + 1}"],
                    "ans": 0,
                    "topic": "Nuclei",
                    "subtype": "multi_step",
                    "exp": f"Number of half-lives elapsed n = {days} / {th} = {n_half}. Remaining fraction = (1/2)^{n_half} = 1/{denom}."
                }
                if _add_q(q): return generated

            # 4. Kinetic energy at apex of projectile
            for K_0 in [40, 50, 60, 80, 100, 120, 150, 160, 200, 240]:
                for theta in [30, 45, 60]:
                    cos_val = 0.866 if theta == 30 else (0.7071 if theta == 45 else 0.5)
                    k_top = round(K_0 * (cos_val ** 2), 1)
                    q = {
                        "q": f"A body of mass m is projected with initial kinetic energy K₀ = {K_0} J at an elevation angle of {theta}° to the horizontal. The kinetic energy of the projectile at its highest point is:",
                        "opts": [f"{k_top} J", f"{K_0} J", f"{round(K_0 / 2, 1)} J", "0 J"],
                        "ans": 0,
                        "topic": "Motion in a Plane",
                        "subtype": "multi_step",
                        "exp": f"At highest point, v_y = 0 and v = u cos θ. K = (1/2) m (u cos θ)² = K₀ cos² θ = {K_0} * ({cos_val:.3f})² = {k_top} J."
                    }
                    if _add_q(q): return generated

            # 5. Combination of two thin lenses
            lens_combos = [
                (20, 30), (15, 30), (10, 40), (25, 50), (30, 60), (10, 20), (20, 50),
                (15, 60), (25, 35), (40, 60), (50, 75), (10, 50), (20, 40), (12, 24)
            ]
            for f1, f2 in lens_combos:
                p_net = round(100.0 / f1 + 100.0 / f2, 1)
                diff = max(1.0, float(abs(f1 - f2)))
                q = {
                    "q": f"Two thin convex lenses of focal lengths {f1} cm and {f2} cm are placed in coaxial contact. The power of the combined lens system is:",
                    "opts": [f"{p_net} D", f"{round(100.0 / diff, 1)} D", f"{round((f1 + f2) / 100.0, 2)} D", f"{round(100.0 / (f1 * f2), 2)} D"],
                    "ans": 0,
                    "topic": "Ray Optics",
                    "subtype": "multi_step",
                    "exp": f"P_net = P1 + P2 = 100/{f1} + 100/{f2} = {p_net} D."
                }
                if _add_q(q): return generated

            # 6. Series LCR resonant angular frequency
            lcr_combos = [
                (10, 10), (20, 5), (50, 2), (5, 20), (40, 10), (25, 4), (100, 1),
                (80, 5), (50, 8), (200, 2), (10, 40), (8, 50)
            ]
            for L_mH, C_uF in lcr_combos:
                w0 = round(1.0 / ((L_mH * 1e-3 * C_uF * 1e-6) ** 0.5), 1)
                q = {
                    "q": f"In a series LCR resonant circuit, an inductor of {L_mH} mH and capacitor of {C_uF} µF are connected. The angular resonant frequency ω₀ is approximately:",
                    "opts": [f"{w0} rad/s", f"{round(w0 * 2, 1)} rad/s", f"{round(w0 * 0.5, 1)} rad/s", "5000 rad/s"],
                    "ans": 0,
                    "topic": "Alternating Current",
                    "subtype": "multi_step",
                    "exp": f"ω₀ = 1 / √(LC) = 1 / √({L_mH}×10⁻³ × {C_uF}×10⁻⁶) = {w0} rad/s."
                }
                if _add_q(q): return generated

            # 7. Carnot engine efficiency
            carnot_data = [
                (500, 300), (600, 300), (400, 300), (800, 400), (500, 250),
                (600, 400), (900, 300), (700, 350), (600, 450), (1000, 500)
            ]
            for T1, T2 in carnot_data:
                eta_pct = round((1 - T2 / T1) * 100, 1)
                q = {
                    "q": f"A reversible Carnot heat engine operates between heat reservoirs at temperatures {T1} K (source) and {T2} K (sink). The thermal efficiency of the engine is:",
                    "opts": [f"{eta_pct}%", f"{round(T2 / T1 * 100, 1)}%", f"{round(eta_pct * 0.8, 1)}%", f"{round(100 - eta_pct * 0.5, 1)}%"],
                    "ans": 0,
                    "topic": "Thermodynamics",
                    "subtype": "multi_step",
                    "exp": f"Efficiency η = 1 - T_sink / T_source = 1 - ({T2} / {T1}) = {eta_pct}%."
                }
                if _add_q(q): return generated

        # [Pure Theory & Definition Catalog]
        if not subtype_filter or subtype_filter == "theory_definition":
            theory_catalog = [
                # Dimensional Formulas
                ("Planck's constant (h)", ["[M L² T⁻¹]", "[M L T⁻¹]", "[M L² T⁻²]", "[M L⁰ T⁻¹]"], "Units and Measurements", "Planck's constant E = hν => [h] = [E]/[ν] = [M L² T⁻²]/[T⁻¹] = [M L² T⁻¹]."),
                ("Self-inductance (L)", ["[M L² T⁻² A⁻²]", "[M L T⁻² A⁻¹]", "[M L² T⁻¹ A⁻²]", "[M L⁰ T⁻² A⁻¹]"], "Electromagnetic Induction", "Using U = (1/2) L I² => [L] = [Energy]/[I²] = [M L² T⁻² A⁻²]."),
                ("Electric permittivity of free space (ε₀)", ["[M⁻¹ L⁻³ T⁴ A²]", "[M L³ T⁻⁴ A⁻²]", "[M⁻¹ L² T⁻² A²]", "[M L² T⁻³ A⁻¹]"], "Electric Charges and Fields", "From Coulomb's law F = q1 q2 / (4πε₀ r²), [ε₀] = [M⁻¹ L⁻³ T⁴ A²]."),
                ("Magnetic permeability of free space (μ₀)", ["[M L T⁻² A⁻²]", "[M L² T⁻¹ A⁻¹]", "[M⁻¹ L T⁻² A²]", "[M L² T⁻² A⁻¹]"], "Moving Charges and Magnetism", "From F/L = μ₀ I1 I2 / (2πd), [μ₀] = [M L T⁻² A⁻²]."),
                ("Magnetic flux (Φ_B)", ["[M L² T⁻² A⁻¹]", "[M L T⁻² A⁻¹]", "[M L² T⁻¹ A⁻²]", "[M L⁰ T⁻² A⁻¹]"], "Electromagnetic Induction", "Φ_B = B · A => [Φ_B] = [M T⁻² A⁻¹] [L²] = [M L² T⁻² A⁻¹]."),
                ("Universal gravitational constant (G)", ["[M⁻¹ L³ T⁻²]", "[M L² T⁻²]", "[M⁻¹ L² T⁻¹]", "[M L³ T⁻²]"], "Gravitation", "F = G m1 m2 / r² => [G] = [M⁻¹ L³ T⁻²]."),
                ("Stefan-Boltzmann constant (σ)", ["[M L⁰ T⁻³ K⁻⁴]", "[M L² T⁻³ K⁻⁴]", "[M L T⁻² K⁻⁴]", "[M L⁰ T⁻² K⁻¹]"], "Thermal Properties of Matter", "E = σ T⁴ => [σ] = [Power]/([Area][K⁴]) = [M L⁰ T⁻³ K⁻⁴]."),
                ("Boltzmann constant (k_B)", ["[M L² T⁻² K⁻¹]", "[M L T⁻² K⁻¹]", "[M L² T⁻¹ K⁻¹]", "[M L⁰ T⁻² K⁻¹]"], "Kinetic Theory", "Energy E = (3/2) k_B T => [k_B] = [M L² T⁻² K⁻¹]."),
                ("Coefficient of viscosity (η)", ["[M L⁻¹ T⁻¹]", "[M L² T⁻¹]", "[M L⁻² T⁻²]", "[M L⁻¹ T⁻²]"], "Mechanical Properties of Fluids", "From F = η A (dv/dx) => [η] = [M L⁻¹ T⁻¹]."),
                ("Surface tension", ["[M L⁰ T⁻²]", "[M L T⁻²]", "[M L⁻¹ T⁻²]", "[M L² T⁻²]"], "Mechanical Properties of Fluids", "Surface tension = Force / Length => [M T⁻²] = [M L⁰ T⁻²]."),
                ("Young's modulus of elasticity", ["[M L⁻¹ T⁻²]", "[M L² T⁻²]", "[M L⁻² T⁻¹]", "[M L T⁻²]"], "Mechanical Properties of Solids", "Modulus = Stress / Strain => [Stress] = [M L⁻¹ T⁻²]."),
                ("Electric dipole moment", ["[L T A]", "[M L T A]", "[L² T A]", "[T A⁻¹]"], "Electric Charges and Fields", "p = q × 2a => [Charge] × [Length] = [A T L]."),
                ("Magnetic dipole moment", ["[L² A]", "[M L² A]", "[L T A]", "[L⁻² A]"], "Magnetism and Matter", "M = I × A => [Current] × [Area] = [L² A]."),
                ("Capacitance (C)", ["[M⁻¹ L⁻² T⁴ A²]", "[M L² T⁻³ A⁻¹]", "[M⁻¹ L⁻³ T⁴ A²]", "[M L² T⁻² A²]"], "Electrostatic Potential and Capacitance", "C = Q / V => [Q²] / [Energy] = [M⁻¹ L⁻² T⁴ A²]."),
                ("Electrical resistivity (ρ)", ["[M L³ T⁻³ A⁻²]", "[M L² T⁻³ A⁻²]", "[M L³ T⁻² A⁻¹]", "[M⁻¹ L⁻³ T³ A²]"], "Current Electricity", "R = ρ L / A => [ρ] = [R] [L] = [M L³ T⁻³ A⁻²]."),
                # Conservation Laws & Foundational Principles
                ("Lenz's law of electromagnetic induction", ["Energy", "Electric charge", "Linear momentum", "Magnetic poles"], "Electromagnetic Induction", "Lenz's law is a direct macroscopic manifestation of the law of conservation of energy."),
                ("Kirchhoff's junction rule (first law)", ["Electric charge", "Energy", "Potential difference", "Magnetic flux"], "Current Electricity", "Kirchhoff's first law (Σ I = 0) represents the conservation of electric charge."),
                ("Kirchhoff's loop rule (second law)", ["Energy", "Electric charge", "Current", "Power"], "Current Electricity", "Kirchhoff's second law (Σ ΔV = 0) represents the conservation of energy in a closed loop."),
                ("Bernoulli's theorem for steady streamline flow", ["Total mechanical energy of flowing fluid", "Mass flow rate alone", "Angular momentum", "Linear momentum"], "Mechanical Properties of Fluids", "Bernoulli's equation states conservation of total mechanical energy per unit volume along a streamline."),
                ("Equation of continuity for incompressible fluid flow", ["Mass conservation", "Energy conservation", "Momentum conservation", "Volume conservation"], "Mechanical Properties of Fluids", "A₁ v₁ = A₂ v₂ expresses the conservation of mass in a fluid tube."),
                ("Kepler's second law of planetary motion (law of areas)", ["Angular momentum conservation", "Linear momentum conservation", "Total energy conservation", "Mass conservation"], "Gravitation", "Central gravitational forces exert zero torque (τ = 0), so angular momentum L is conserved."),
                # Magnetic Classification & Materials
                ("diamagnetic substances (e.g. Bismuth, Copper, Water)", ["Negative magnetic susceptibility (χ < 0) and slight repulsion by magnetic fields", "Strong attraction into magnetic fields", "Permanent magnetization above Curie point", "Positive susceptibility proportional to temperature"], "Magnetism and Matter", "Diamagnetic materials have paired electrons and χ < 0, being slightly repelled by magnetic fields."),
                ("paramagnetic substances (e.g. Aluminium, Oxygen)", ["Small positive magnetic susceptibility inversely proportional to absolute temperature (Curie law)", "Perfect diamagnetism with χ = -1", "Repulsion by magnetic poles", "Permanent magnetic saturation at all temperatures"], "Magnetism and Matter", "Paramagnets follow Curie's law χ ∝ 1/T with small positive susceptibility."),
                ("ferromagnetic substances (e.g. Iron, Cobalt, Nickel)", ["Spontaneous domain magnetization that transitions to paramagnetic above the Curie temperature", "Zero net magnetic moment at absolute zero", "Negative magnetic susceptibility", "Complete absence of magnetic hysteresis"], "Magnetism and Matter", "Ferromagnets exhibit strong domain alignment and become paramagnetic above Curie temperature T_c."),
                ("superconductors exhibiting the Meissner effect", ["Complete expulsion of magnetic flux lines with susceptibility χ = -1 (perfect diamagnetism)", "Infinite magnetic permeability", "Transition to ferromagnetism", "Zero electrical resistance with high positive susceptibility"], "Magnetism and Matter", "The Meissner effect in superconductors exhibits perfect diamagnetism with B = 0 inside and χ = -1."),
                # Semiconductor & Electronics Physics
                ("When Silicon is doped with Boron (trivalent acceptor impurity)", ["A p-type semiconductor with holes as majority charge carriers", "An n-type semiconductor with electrons as majority carriers", "A degenerate superconductor", "An intrinsic insulator"], "Semiconductor Electronics", "Trivalent Boron creates hole vacancies in the valence band, producing a p-type semiconductor."),
                ("When Silicon is doped with Phosphorus (pentavalent donor impurity)", ["An n-type semiconductor with electrons as majority charge carriers", "A p-type semiconductor with holes as majority carriers", "A p-n junction diode", "A metallic conductor"], "Semiconductor Electronics", "Pentavalent Phosphorus donates free conduction electrons, producing an n-type semiconductor."),
                ("When Silicon is doped with Indium (trivalent impurity)", ["A p-type semiconductor with holes as majority charge carriers", "An n-type semiconductor with electrons as majority carriers", "A high-temperature superconductor", "An intrinsic crystal"], "Semiconductor Electronics", "Indium is a Group 13 trivalent acceptor producing p-type conduction."),
                ("When Silicon is doped with Arsenic (pentavalent impurity)", ["An n-type semiconductor with electrons as majority charge carriers", "A p-type semiconductor with holes as majority carriers", "A p-n junction diode", "An insulator at room temperature"], "Semiconductor Electronics", "Arsenic is a Group 15 pentavalent donor producing n-type conduction."),
                ("In an unbiased p-n junction at thermal equilibrium, the direction of built-in electric field in the depletion layer is from:", ["n-region to p-region", "p-region to n-region", "Anode to cathode externally", "Zero at equilibrium"], "Semiconductor Electronics", "Positive uncompensated donor ions in n-side and negative acceptor ions in p-side direct the internal field from n to p."),
                ("A Zener diode is specially fabricated with heavy doping in order to operate stably in:", ["Reverse breakdown region under reverse bias", "Forward active region under forward bias", "Cutoff region with zero bias", "Saturation mode only"], "Semiconductor Electronics", "Zener diodes maintain a constant voltage specifically in the reverse breakdown (avalanche/Zener) region."),
                ("In a full-wave rectifier operating at an input AC mains frequency of 50 Hz, the output ripple frequency is:", ["100 Hz", "50 Hz", "25 Hz", "200 Hz"], "Semiconductor Electronics", "Full-wave rectifiers conduct on both positive and negative half cycles, doubling the ripple frequency to 2 * 50 = 100 Hz."),
                # Wave Optics & Modern Physics
                ("The classical optical phenomenon of polarization experimentally demonstrates that light waves possess:", ["Transverse wave nature", "Longitudinal wave nature", "Mechanical particulate nature", "Non-propagating standing nature"], "Wave Optics", "Only transverse waves whose vibrations are perpendicular to propagation can be polarized."),
                ("According to Brewster's law, when light reflects at Brewster angle i_B from a dielectric surface of refractive index n:", ["tan(i_B) = n", "sin(i_B) = n", "cos(i_B) = n", "cot(i_B) = n"], "Wave Optics", "Brewster's condition states tan(i_B) = n, at which the reflected and refracted rays are mutually perpendicular."),
                ("In Young's double slit experiment, if monochromatic light is replaced by white light, the central fringe is:", ["White, surrounded by colored fringes", "Dark black", "Completely absent", "Monochromatic red"], "Wave Optics", "At the central point, path difference is zero for all wavelengths, producing a central white fringe."),
                ("In the Bohr model of the hydrogen atom, the spectral series lying exclusively in the ultraviolet (UV) region is the:", ["Lyman series", "Balmer series", "Paschen series", "Brackett series"], "Atoms", "Transitions to n=1 (Lyman series) emit high-energy photons in the ultraviolet spectrum; Balmer series lies in the visible."),
                ("In the hydrogen emission spectrum, the Balmer series of spectral lines lies in which electromagnetic region?", ["Visible region", "Ultraviolet region", "Infrared region", "X-ray region"], "Atoms", "Transitions ending on the second orbit (n=2) produce wavelengths between 400 nm and 700 nm (visible spectrum)."),
                ("The nuclear density of an atomic nucleus of mass number A is approximately:", ["Independent of mass number A (~ 2.3 × 10¹⁷ kg/m³)", "Directly proportional to A", "Inversely proportional to A", "Proportional to A^(1/3)"], "Nuclei", "Since nuclear volume V ∝ R³ ∝ A and mass M ∝ A, density ρ = M/V is constant and independent of A."),
                ("Nuclear forces that bind protons and neutrons together in a nucleus are:", ["Short-range, charge-independent and non-central forces", "Long-range inverse-square forces", "Strongly dependent on electric charge", "Purely electrostatic attractive forces"], "Nuclei", "Nuclear forces are the strongest known forces, acting over ~1-2 fm, independent of charge (F_pp = F_nn = F_np)."),
                ("Total internal reflection (TIR) can occur only when light travels from:", ["An optically denser medium to a rarer medium with angle of incidence greater than critical angle", "A rarer medium to a denser medium", "Vacuum into glass at any angle", "Water into diamond at 90°"], "Ray Optics", "TIR requires propagation into a medium of lower refractive index with i > critical angle θ_c."),
            ]
            for concept, opts, top_name, expl in theory_catalog:
                q = {
                    "q": f"Which of the following statements correctly identifies the KCET principle regarding {concept}?",
                    "opts": opts,
                    "ans": 0,
                    "topic": top_name,
                    "subtype": "theory_definition",
                    "exp": expl
                }
                if _add_q(q): return generated

    # ── 2. Chemistry Variations ──────────────────────────────────────────────
    elif "chem" in topic_lower:
        # Physical Chemistry Numericals
        if not subtype_filter or subtype_filter == "physical_numerical":
            # 1. Mass percentage
            chem_compounds = [
                ("Methane", "CH₄", 16, "Carbon", 12), ("Water", "H₂O", 18, "Oxygen", 16),
                ("Sulfuric Acid", "H₂SO₄", 98, "Sulfur", 32), ("Glucose", "C₆H₁₂O₆", 180, "Carbon", 72),
                ("Sodium Hydroxide", "NaOH", 40, "Sodium", 23), ("Calcium Carbonate", "CaCO₃", 100, "Calcium", 40),
                ("Ammonia", "NH₃", 17, "Nitrogen", 14), ("Carbon Dioxide", "CO₂", 44, "Carbon", 12),
                ("Ethanol", "C₂H₅OH", 46, "Carbon", 24), ("Urea", "NH₂CONH₂", 60, "Nitrogen", 28),
                ("Acetic Acid", "CH₃COOH", 60, "Oxygen", 32), ("Methanol", "CH₃OH", 32, "Carbon", 12),
                ("Benzene", "C₆H₆", 78, "Carbon", 72), ("Acetone", "CH₃COCH₃", 58, "Carbon", 36),
                ("Sodium Chloride", "NaCl", 58.5, "Sodium", 23), ("Potassium Nitrate", "KNO₃", 101, "Nitrogen", 14),
                ("Magnesium Sulfate", "MgSO₄", 120, "Magnesium", 24), ("Iron(III) Oxide", "Fe₂O₃", 160, "Iron", 112)
            ]
            for name, fmla, mm, elem, em in chem_compounds:
                pct = round((em / mm) * 100, 1)
                q = {
                    "q": f"The percentage by mass of {elem} in {name} ({fmla}, molar mass = {mm} g/mol) is approximately:",
                    "opts": [f"{pct}%", f"{round(100 - pct, 1)}%", f"{round(pct * 0.5, 1)}%", f"{round(pct * 0.8, 1)}%"],
                    "ans": 0,
                    "topic": "Some Basic Concepts of Chemistry",
                    "subtype": "physical_numerical",
                    "exp": f"Mass % of {elem} = ({em} / {mm}) * 100 = {pct}%."
                }
                if _add_q(q): return generated

            # 2. Oxidation state calculations
            ox_species = [
                ("KMnO₄", "Mn", "+7"), ("K₂Cr₂O₇", "Cr", "+6"), ("H₂SO₄", "S", "+6"), ("HNO₃", "N", "+5"),
                ("HClO₄", "Cl", "+7"), ("CrO₃", "Cr", "+6"), ("H₃PO₄", "P", "+5"), ("K₂MnO₄", "Mn", "+6"),
                ("Na₂S₂O₃", "S", "+2"), ("Fe₃O₄", "Fe", "+8/3"), ("OF₂", "O", "+2"), ("H₂O₂", "O", "-1"),
                ("KO₂", "O", "-1/2"), ("Na₂O₂", "O", "-1"), ("Cr₂O₇²⁻", "Cr", "+6"), ("MnO₄⁻", "Mn", "+7"),
                ("S₂O₃²⁻", "S", "+2"), ("NH₄⁺", "N", "-3"), ("ClO₃⁻", "Cl", "+5"), ("NO₂⁻", "N", "+3")
            ]
            for comp, elem, ox_val in ox_species:
                q = {
                    "q": f"The oxidation state of {elem} in the chemical species {comp} is:",
                    "opts": [ox_val, "+4", "+2", "-2"],
                    "ans": 0,
                    "topic": "Redox Reactions",
                    "subtype": "physical_numerical",
                    "exp": f"Applying standard oxidation number rules to {comp}, the oxidation state of {elem} is {ox_val}."
                }
                if _add_q(q): return generated

            # 3. Chemical Kinetics First Order Half Life
            kinetics_data = [
                (0.0693, 10, "min"), (0.0231, 30, "min"), (0.01386, 50, "min"),
                (0.03465, 20, "min"), (0.00693, 100, "min"), (0.1386, 5, "min"),
                (0.693, 1, "s"), (0.001386, 500, "s"), (0.00231, 300, "s"),
                (0.003465, 200, "s"), (0.0462, 15, "min"), (0.017325, 40, "min")
            ]
            for k_val, t_half, u_time in kinetics_data:
                q = {
                    "q": f"A first-order chemical reaction has a rate constant k = {k_val} {u_time}⁻¹. The half-life (t₁/₂) of the reaction is:",
                    "opts": [f"{t_half} {u_time}", f"{t_half * 2} {u_time}", f"{round(t_half / 2, 1)} {u_time}", f"{t_half + 10} {u_time}"],
                    "ans": 0,
                    "topic": "Chemical Kinetics",
                    "subtype": "physical_numerical",
                    "exp": f"For a first order reaction, t₁/₂ = 0.693 / k = 0.693 / {k_val} = {t_half} {u_time}."
                }
                if _add_q(q): return generated

            # 4. Standard Cell EMF
            emf_data = [
                ("Zn | Zn²⁺ || Cu²⁺ | Cu (Daniell Cell)", -0.76, 0.34, 1.10),
                ("Mg | Mg²⁺ || Ag⁺ | Ag", -2.37, 0.80, 3.17),
                ("Fe | Fe²⁺ || Cd²⁺ | Cd", -0.44, -0.40, 0.04),
                ("Ni | Ni²⁺ || Ag⁺ | Ag", -0.25, 0.80, 1.05),
                ("Zn | Zn²⁺ || Fe²⁺ | Fe", -0.76, -0.44, 0.32),
                ("Al | Al³⁺ || Cu²⁺ | Cu", -1.66, 0.34, 2.00),
                ("Zn | Zn²⁺ || Ag⁺ | Ag", -0.76, 0.80, 1.56),
                ("Cr | Cr³⁺ || Fe²⁺ | Fe", -0.74, -0.44, 0.30),
                ("Sn | Sn²⁺ || Pb²⁺ | Pb", -0.14, -0.13, 0.01),
                ("Cu | Cu²⁺ || Ag⁺ | Ag", 0.34, 0.80, 0.46)
            ]
            for cell_name, e_a, e_c, e_cell in emf_data:
                q = {
                    "q": f"Given standard reduction potentials E°(anode) = {e_a} V and E°(cathode) = {e_c} V for the galvanic cell {cell_name}, the standard cell potential E°_cell is:",
                    "opts": [f"+{e_cell:.2f} V", f"-{e_cell:.2f} V", f"+{abs(e_a + e_c):.2f} V", "+0.00 V"],
                    "ans": 0,
                    "topic": "Electrochemistry",
                    "subtype": "physical_numerical",
                    "exp": f"E°_cell = E°_cathode - E°_anode = ({e_c}) - ({e_a}) = +{e_cell:.2f} V."
                }
                if _add_q(q): return generated

        # Direct Fact, Memory & Reaction-Based Catalog
        if not subtype_filter or subtype_filter == "fact_reaction":
            # 1. Hybridization and Geometry of Chemical Species
            geom_data = [
                ("SF₆", "Octahedral", "sp³d²"), ("PCl₅", "Trigonal bipyramidal", "sp³d"),
                ("CH₄", "Tetrahedral", "sp³"), ("BF₃", "Trigonal planar", "sp²"),
                ("BeCl₂", "Linear", "sp"), ("IF₇", "Pentagonal bipyramidal", "sp³d³"),
                ("NH₃", "Trigonal pyramidal", "sp³ with 1 lone pair"), ("H₂O", "Bent (V-shaped)", "sp³ with 2 lone pairs"),
                ("XeF₄", "Square planar", "sp³d² with 2 lone pairs"), ("XeF₂", "Linear", "sp³d with 3 lone pairs"),
                ("ClF₃", "T-shaped", "sp³d with 2 lone pairs"), ("BrF₅", "Square pyramidal", "sp³d² with 1 lone pair"),
                ("SO₂", "Bent (angular)", "sp² with 1 lone pair"), ("CO₂", "Linear", "sp"),
                ("XeO₃", "Trigonal pyramidal", "sp³ with 1 lone pair"), ("XeOF₄", "Square pyramidal", "sp³d² with 1 lone pair")
            ]
            for molec, geom_name, hyb_type in geom_data:
                q = {
                    "q": f"According to VSEPR theory and hybridization principles, the chemical species {molec} possesses which spatial molecular geometry?",
                    "opts": [geom_name, "Tetrahedral" if geom_name != "Tetrahedral" else "Trigonal planar", "Octahedral" if geom_name != "Octahedral" else "Bent (V-shaped)", "Trigonal bipyramidal" if geom_name != "Trigonal bipyramidal" else "Linear"],
                    "ans": 0,
                    "topic": "Chemical Bonding",
                    "subtype": "fact_reaction",
                    "exp": f"{molec} exhibits {hyb_type} resulting in a {geom_name} geometry."
                }
                if _add_q(q): return generated

            # 2. IUPAC Nomenclature of Coordination Complexes
            coord_names = [
                ("K₄[Fe(CN)₆]", "Potassium hexacyanidoferrate(II)"),
                ("K₃[Fe(CN)₆]", "Potassium hexacyanidoferrate(III)"),
                ("[Co(NH₃)₆]Cl₃", "Hexaamminecobalt(III) chloride"),
                ("[Co(NH₃)₅Cl]Cl₂", "Pentaamminechloridocobalt(III) chloride"),
                ("[Co(NH₃)₄Cl₂]Cl", "Tetraamminedichloridocobalt(III) chloride"),
                ("[Ni(CO)₄]", "Tetracarbonylnickel(0)"),
                ("[Ni(CN)₄]²⁻", "Tetracyanidonickelate(II) ion"),
                ("[Pt(NH₃)₂Cl₂]", "Diamminedichloridoplatinum(II)"),
                ("[Cr(H₂O)₆]Cl₃", "Hexaaquachromium(III) chloride"),
                ("[Fe(CO)₅]", "Pentacarbonyliron(0)"),
                ("K₂[PtCl₆]", "Potassium hexachloridoplatinate(IV)"),
                ("[Cu(NH₃)₄]SO₄", "Tetraamminecopper(II) sulfate"),
                ("[Ag(NH₃)₂]Cl", "Diamminesilver(I) chloride"),
                ("K[Ag(CN)₂]", "Potassium dicyanidoargentate(I)"),
                ("[Co(en)₃]Cl₃", "Tris(ethane-1,2-diamine)cobalt(III) chloride"),
            ]
            for complex_fmla, iupac_name in coord_names:
                q = {
                    "q": f"According to standard IUPAC nomenclature rules, the coordination compound {complex_fmla} is correctly named as:",
                    "opts": [iupac_name, "Tetraammine iron chloride", "Potassium cyano complex", "Hexaaquairon(III) chloride"],
                    "ans": 0,
                    "topic": "Coordination Compounds",
                    "subtype": "fact_reaction",
                    "exp": f"Following IUPAC conventions for coordination entities, {complex_fmla} is named {iupac_name}."
                }
                if _add_q(q): return generated

            # 3. Monomers of Polymers
            poly_data = [
                ("Polyvinyl chloride (PVC)", "Vinyl chloride (CH₂=CHCl)"),
                ("Teflon (PTFE)", "Tetrafluoroethene (CF₂=CF₂)"),
                ("Polystyrene", "Styrene (C₆H₅CH=CH₂)"),
                ("Polyacrylonitrile (PAN / Orlon)", "Acrylonitrile (CH₂=CHCN)"),
                ("Neoprene (polychloroprene)", "Chloroprene (2-chloro-1,3-butadiene)"),
                ("Natural rubber", "Isoprene (2-methyl-1,3-butadiene)"),
                ("Nylon-6", "Caprolactam"),
                ("Dacron / Terylene", "Ethylene glycol and Terephthalic acid"),
                ("Bakelite", "Phenol and Formaldehyde"),
                ("Melamine polymer", "Melamine and Formaldehyde"),
                ("Buna-S", "1,3-Butadiene and Styrene"),
                ("Buna-N", "1,3-Butadiene and Acrylonitrile"),
                ("Glyptal", "Ethylene glycol and Phthalic acid"),
                ("PHBV", "3-Hydroxybutanoic acid and 3-Hydroxypentanoic acid"),
            ]
            for poly_name, mono_name in poly_data:
                q = {
                    "q": f"The fundamental repeating monomer unit(s) utilized in the industrial manufacture of {poly_name} is/are:",
                    "opts": [mono_name, "Adipic acid alone", "Caprolactam and Glycine", "1,3-Butadiene alone"],
                    "ans": 0,
                    "topic": "Polymers",
                    "subtype": "fact_reaction",
                    "exp": f"{poly_name} is synthesized by the polymerization of {mono_name}."
                }
                if _add_q(q): return generated

            fact_reaction_pool = [
                # Organic Named Reactions & Tests
                ("When phenol is treated with chloroform (CHCl₃) in the presence of aqueous NaOH followed by acid hydrolysis, the major product formed is:",
                 ["Salicylaldehyde", "Salicylic acid", "Benzoic acid", "Picric acid"], 0, "Alcohols, Phenols and Ethers", "This is the Reimer-Tiemann reaction where electrophilic dichlorocarbene (:CCl₂) attacks phenol to synthesize salicylaldehyde."),
                ("The reaction of sodium phenoxide with carbon dioxide (CO₂) under pressure at 400 K followed by acidification produces salicylic acid. This reaction is known as:",
                 ["Kolbe's reaction", "Reimer-Tiemann reaction", "Friedel-Crafts acylation", "Wurtz reaction"], 0, "Alcohols, Phenols and Ethers", "Kolbe's synthesis involves electrophilic carboxylation of phenoxide ion by CO₂ followed by protonation to yield salicylic acid."),
                ("Lucas reagent, used to distinguish between primary, secondary, and tertiary alcohols, consists of an equimolar mixture of:",
                 ["Anhydrous ZnCl₂ and conc. HCl", "Dilute HCl and Zn dust", "Conc. H₂SO₄ and KMnO₄", "AlCl₃ and conc. HNO₃"], 0, "Alcohols, Phenols and Ethers", "Lucas reagent is an equimolar solution of anhydrous ZnCl₂ in conc. HCl."),
                ("Which of the following carbonyl compounds does NOT undergo Aldol condensation due to the complete absence of α-hydrogen atoms?",
                 ["Benzaldehyde (C₆H₅CHO)", "Acetaldehyde (CH₃CHO)", "Propanal (CH₃CH₂CHO)", "Acetone (CH₃COCH₃)"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Benzaldehyde lacks α-hydrogen atoms and undergoes the Cannizzaro disproportionation reaction instead of Aldol condensation."),
                ("The reduction of aldehydes and ketones directly to corresponding alkanes using zinc amalgam (Zn/Hg) and concentrated hydrochloric acid is called:",
                 ["Clemmensen reduction", "Wolff-Kishner reduction", "Rosenmund reduction", "Stephen reduction"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Clemmensen reduction employs Zn(Hg) and conc. HCl to convert carbonyl >C=O groups directly into methylene -CH₂- groups."),
                ("The reduction of acyl chlorides to aldehydes using hydrogen gas in the presence of palladium poisoned with barium sulfate (Pd/BaSO₄) is known as:",
                 ["Rosenmund reduction", "Clemmensen reduction", "Etard reaction", "Gatterman-Koch reaction"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Rosenmund reduction employs H₂ over Pd/BaSO₄ (poisoned with sulfur or quinoline) to selectively reduce acid chlorides to aldehydes."),
                ("Which of the following chemical tests is exclusively given by primary amines upon heating with chloroform and alcoholic KOH to produce a foul smell?",
                 ["Carbylamine test", "Hinsberg test", "Lucas test", "Tollens' test"], 0, "Amines", "The Carbylamine test (isocyanide test) produces extremely foul-smelling alkyl/aryl isocyanides only with primary amines."),
                ("Gabriel phthalimide synthesis is a versatile industrial reaction specifically employed for the preparation of pure:",
                 ["Primary aliphatic amines", "Aromatic primary amines", "Secondary amines", "Tertiary amines"], 0, "Amines", "Gabriel phthalimide synthesis yields exclusively pure 1° aliphatic amines; aromatic primary amines cannot be prepared due to lack of aryl halide nucleophilic substitution."),
                ("The degradation reaction of primary acid amides with bromine and aqueous sodium hydroxide to yield a primary amine with one less carbon atom is called:",
                 ["Hoffmann bromamide reaction", "Gabriel synthesis", "Curtius rearrangement", "Schmidt reaction"], 0, "Amines", "Hoffmann bromamide degradation converts R-CONH₂ to R-NH₂ with loss of the carbonyl carbon as carbonate."),
                ("Tollens' reagent (ammoniacal silver nitrate solution) produces a shining silver mirror upon heating with which class of organic compounds?",
                 ["Aldehydes", "Ketones", "Ethers", "Tertiary alcohols"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Tollens' reagent oxidizes both aliphatic and aromatic aldehydes to carboxylates while reducing Ag⁺ to metallic silver (silver mirror). Ketones do not react."),
                ("A bright yellow precipitate of iodoform (CHI₃) with iodine and aqueous NaOH is produced by compounds containing which structural group?",
                 ["CH₃-C=O or CH₃-CH(OH)-", "-CH₂-OH alone", "-COOH group", "-O-CH₃ ether linkage"], 0, "Aldehydes, Ketones and Carboxylic Acids", "The iodoform haloform reaction requires a methyl carbonyl group (CH₃-C=O) or a methyl carbinol group (CH₃-CH(OH)-)."),
                ("Williamson ether synthesis involves an SN2 nucleophilic substitution reaction between a primary alkyl halide and a:",
                 ["Sodium alkoxide (R-O⁻ Na⁺)", "Carboxylic acid", "Grignard reagent", "Ester"], 0, "Alcohols, Phenols and Ethers", "Williamson ether synthesis involves nucleophilic attack of alkoxide ion (R-O⁻) on primary alkyl halide (R'-X) to form ether (R-O-R')."),
                ("The reaction of alkyl chloride or bromide with sodium iodide (NaI) in dry acetone to synthesize alkyl iodides is known as:",
                 ["Finkelstein reaction", "Swarts reaction", "Wurtz reaction", "Sandmeyer reaction"], 0, "Haloalkanes and Haloarenes", "Finkelstein halide exchange utilizes the precipitation of NaCl/NaBr in dry acetone to drive conversion to alkyl iodides."),
                ("The synthesis of alkyl fluorides by heating alkyl chlorides or bromides in the presence of metallic fluorides (such as AgF, Hg₂F₂, or SbF₃) is called:",
                 ["Swarts reaction", "Finkelstein reaction", "Wurtz-Fittig reaction", "Ullmann reaction"], 0, "Haloalkanes and Haloarenes", "Swarts reaction is the standard method for preparing fluoroalkanes using inorganic fluorides like AgF or SbF₃."),
                ("The addition of hydrogen bromide (HBr) to propene in the presence of organic benzoyl peroxide yields 1-bromopropane instead of 2-bromopropane due to the:",
                 ["Kharasch peroxide effect (Free radical addition)", "Markovnikov electrophilic addition", "Carbocation rearrangement", "Elimination reaction"], 0, "Haloalkanes and Haloarenes", "In the presence of peroxides, HBr undergoes a free-radical chain reaction (Kharasch effect) leading to anti-Markovnikov regioselectivity."),
                # Inorganic Coordination Chemistry & Metallurgy
                ("In the coordination complex [Co(NH₃)₆]³⁺, the cobalt ion undergoes which hybridization resulting in a low-spin diamagnetic complex?",
                 ["d²sp³ (Inner orbital octahedral)", "sp³d² (Outer orbital octahedral)", "sp³d (Trigonal bipyramidal)", "dsp² (Square planar)"], 0, "Coordination Compounds", "[Co(NH₃)₆]³⁺ has Co³⁺ (d⁶ configuration). NH₃ acts as a strong field ligand pairing up d electrons into t₂g⁶, utilizing inner 3d orbitals (d²sp³)."),
                ("The coordination complex [Ni(CN)₄]²⁻ has a square planar geometry and is diamagnetic because nickel undergoes which hybridization?",
                 ["dsp²", "sp³", "d²sp³", "sp³d"], 0, "Coordination Compounds", "CN⁻ is a strong field ligand that forces pairing of the two unpaired 3d electrons in Ni²⁺ (3d⁸), freeing one 3d orbital for dsp² square planar hybridization."),
                ("In contrast to [Ni(CN)₄]²⁻, the complex ion [NiCl₄]²⁻ is paramagnetic with 2 unpaired electrons and possesses which geometry?",
                 ["Tetrahedral (sp³)", "Square planar (dsp²)", "Octahedral (sp³d²)", "Linear (sp)"], 0, "Coordination Compounds", "Cl⁻ is a weak field ligand that cannot force pairing in Ni²⁺ (3d⁸). It utilizes 4s and 4p orbitals (sp³), giving a tetrahedral paramagnetic complex."),
                ("The cis-isomer of which neutral coordination complex is widely used as an effective anti-cancer chemotherapeutic drug?",
                 ["cis-[Pt(NH₃)₂Cl₂] (Cisplatin)", "trans-[Pt(NH₃)₂Cl₂]", "cis-[Co(en)₂Cl₂]⁺", "[Ni(CO)₄]"], 0, "Coordination Compounds", "Cisplatin (cis-diamminedichloroplatinum(II)) binds to cancer cell DNA to inhibit replication and is a frontline anti-cancer agent."),
                ("Which of the following ligands acts as a hexadentate chelating ligand widely used for the quantitative estimation of Ca²⁺ and Mg²⁺ ions?",
                 ["EDTA⁴⁻ (Ethylenediaminetetraacetate)", "Oxalate ion (C₂O₄²⁻)", "Ethylenediamine (en)", "Dimethylglyoxime (DMG)"], 0, "Coordination Compounds", "EDTA⁴⁻ has two nitrogen and four oxygen donor atoms, forming an exceptionally stable hexadentate ring complex with metal ions."),
                ("Lanthanoid contraction observed across the inner transition 4f-series is fundamentally caused by:",
                 ["Poor shielding effect of 4f electrons against nuclear charge", "Complete filling of 5d subshell", "High shielding effect of 4f electrons", "Uniform decrease in atomic mass"], 0, "d and f Block Elements", "The diffused radial shape of 4f orbitals causes poor shielding, allowing nuclear charge to pull outer electrons inward uniformly."),
                ("Which of the following halogen atoms has the highest (most negative) electron gain enthalpy in Group 17?",
                 ["Chlorine (Cl)", "Fluorine (F)", "Bromine (Br)", "Iodine (I)"], 0, "p-Block Elements", "Due to the extremely small compact 2p subshell of Fluorine, strong interelectronic repulsions weaken incoming electron attraction, making Chlorine's electron gain enthalpy more negative."),
                ("In the Contact process for the large-scale industrial manufacture of sulfuric acid (H₂SO₄), the catalyst employed for the oxidation of SO₂ to SO₃ is:",
                 ["Vanadium pentoxide (V₂O₅)", "Finely divided Iron (Fe)", "Platinized asbestos alone", "Nickel catalyst"], 0, "p-Block Elements", "V₂O₅ operates at ~720 K as an efficient, poison-resistant heterogeneous catalyst for 2SO₂ + O₂ -> 2SO₃."),
                ("In metallurgy, the Froth Flotation process is universally applied for the concentration of which class of ores?",
                 ["Sulfide ores (e.g. Galena PbS, Zinc blende ZnS)", "Oxide ores (e.g. Bauxite, Haematite)", "Carbonate ores (e.g. Calamine, Siderite)", "Halide ores (e.g. Rock salt)"], 0, "General Principles and Processes of Isolation of Elements", "Sulfide ore particles are preferentially wetted by pine oil and collector frothers, floating to the surface froth."),
                ("The industrial metallurgical process used for the ultra-high refining of Nickel by thermal decomposition of volatile nickel tetracarbonyl is called:",
                 ["Mond process", "Van Arkel process", "Zone refining", "Liquation process"], 0, "General Principles and Processes of Isolation of Elements", "Nickel reacts with CO at 330-350 K to form volatile Ni(CO)₄, which decomposes at 450-470 K to deposit pure Nickel (Mond process)."),
                ("The Van Arkel de Boer method of refining metals to achieve ultra-pure status for aerospace applications is commonly used for:",
                 ["Zirconium (Zr) and Titanium (Ti)", "Copper (Cu) and Zinc (Zn)", "Iron (Fe) and Nickel (Ni)", "Aluminium (Al) and Lead (Pb)"], 0, "General Principles and Processes of Isolation of Elements", "Zirconium and Titanium are heated with iodine to form volatile iodides (ZrI₄/TiI₄) which decompose on a hot tungsten filament to yield ultra-pure metal."),
                ("During the Hall-Héroult electrolytic reduction of molten alumina (Al₂O₃), cryolite (Na₃AlF₆) and fluorspar (CaF₂) are added to:",
                 ["Lower the melting point and increase electrical conductivity", "Act as oxidizing agents", "Precipitate impurities", "Increase the boiling point of the electrolyte"], 0, "General Principles and Processes of Isolation of Elements", "Purified Al₂O₃ melts at >2300 K; dissolving it in molten Na₃AlF₆/CaF₂ lowers the operating temperature to ~1200 K and enhances conductivity."),
                ("Which of the following oxoacids of chlorine possesses the highest acidic strength in aqueous solution?",
                 ["Perchloric acid (HClO₄)", "Chloric acid (HClO₃)", "Chlorous acid (HClO₂)", "Hypochlorous acid (HClO)"], 0, "p-Block Elements", "HClO₄ has chlorine in its highest +7 oxidation state, producing the conjugate perchlorate base ClO₄⁻ which is stabilized by four equivalent resonance structures."),
                ("The primary covalent linkage connecting successive amino acid residues in the linear primary structure of proteins is called the:",
                 ["Peptide bond (-CO-NH-)", "Glycosidic bond", "Phosphodiester bond", "Disulfide bridge"], 0, "Biomolecules", "Peptide bonds are formed between the α-amino group of one amino acid and the α-carboxyl group of another via condensation."),
                ("Which of the following vitamins is water-soluble and must be regularly supplied in human dietary intake?",
                 ["Vitamin C (Ascorbic acid)", "Vitamin A", "Vitamin D", "Vitamin K"], 0, "Biomolecules", "Vitamins B and C are water-soluble and excreted in urine, requiring regular dietary intake. Vitamins A, D, E, K are fat-soluble and stored in liver/adipose tissue."),
                # Additional high-yield organic reactions and reagent mechanisms
                ("In the conversion of ethanol to ethene by dehydration, the required reaction conditions are:",
                 ["Concentrated H₂SO₄ at 443 K", "Concentrated H₂SO₄ at 413 K", "Alkaline KMnO₄ at room temperature", "Dilute HCl at 373 K"], 0, "Alcohols, Phenols and Ethers", "Ethanol dehydrates to ethene at 443 K with conc. H₂SO₄; at lower temperature (413 K) it yields diethyl ether."),
                ("The reaction of phenol with bromine water (Br₂/H₂O) gives an immediate white precipitate of:",
                 ["2,4,6-Tribromophenol", "o-Bromophenol", "p-Bromophenol", "m-Bromophenol"], 0, "Alcohols, Phenols and Ethers", "The strongly activating -OH group facilitates trisubstitution by bromine water to form insoluble 2,4,6-tribromophenol."),
                ("When aniline is treated with bromine water at room temperature, the white precipitate formed is:",
                 ["2,4,6-Tribromoaniline", "p-Bromoaniline", "o-Bromoaniline", "Bromobenzene"], 0, "Amines", "The powerful activating effect of the -NH₂ group causes electrophilic substitution at all ortho and para positions."),
                ("The nitration of benzene to form nitrobenzene requires a nitrating mixture containing concentrated HNO₃ and:",
                 ["Concentrated H₂SO₄ (generates NO₂⁺ electrophile)", "Dilute HCl", "Anhydrous AlCl₃ alone", "Acetic acid"], 0, "Hydrocarbons", "Conc. H₂SO₄ acts as a Brønsted acid protonating HNO₃ to generate the active nitronium ion (NO₂⁺) electrophile."),
                ("The reduction of nitrobenzene to aniline in laboratory synthesis is best achieved using:",
                 ["Sn and concentrated HCl (or Fe + HCl)", "LiAlH₄ in dry ether", "H₂ with Ni at 500 K", "Sodium amalgam and water"], 0, "Amines", "Reduction with Fe/HCl or Sn/HCl is the standard laboratory and industrial route to aniline from nitrobenzene."),
                ("The conversion of toluene into benzaldehyde using chromyl chloride (CrO₂Cl₂) in CS₂ is known as:",
                 ["Etard reaction", "Gattermann-Koch reaction", "Cannizzaro reaction", "Stephen reaction"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Chromyl chloride oxidizes the methyl group of toluene into a brown chromium complex, which on hydrolysis yields benzaldehyde (Etard reaction)."),
                ("The conversion of benzene to benzaldehyde by treatment with carbon monoxide (CO) and HCl in the presence of anhydrous AlCl₃ is called:",
                 ["Gattermann-Koch reaction", "Etard reaction", "Friedel-Crafts acylation", "Rosenmund reaction"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Gattermann-Koch formylation uses CO + HCl in the presence of AlCl₃/CuCl to form benzaldehyde from benzene."),
                ("Heating sodium acetate with sodalime (NaOH + CaO) results in decarboxylation to produce:",
                 ["Methane (CH₄)", "Ethane", "Propane", "Acetone"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Decarboxylation of sodium salt of carboxylic acid with sodalime eliminates Na₂CO₃, yielding an alkane with one less carbon."),
                ("Selective oxidation of primary alcohols to aldehydes without over-oxidation to carboxylic acids is achieved using:",
                 ["Pyridinium chlorochromate (PCC)", "Acidified KMnO₄", "Chromic acid (H₂CrO₄)", "Conc. HNO₃"], 0, "Alcohols, Phenols and Ethers", "PCC in CH₂Cl₂ selectively oxidizes 1° alcohols to aldehydes and 2° alcohols to ketones without further oxidation."),
                ("Acid-catalyzed hydration of propene (CH₃-CH=CH₂ + H₂O/H⁺) yields as the major product:",
                 ["Propan-2-ol (Markovnikov product)", "Propan-1-ol", "Propanoic acid", "Acetone"], 0, "Alcohols, Phenols and Ethers", "Hydration follows Markovnikov's rule where proton attacks terminal carbon to form the more stable 2° carbocation intermediate."),
                ("Hydroboration-oxidation of propene with diborane (B₂H₆) followed by alkaline H₂O₂ yields:",
                 ["Propan-1-ol (Anti-Markovnikov alcohol)", "Propan-2-ol", "Propene oxide", "Propanoic acid"], 0, "Alcohols, Phenols and Ethers", "Hydroboration-oxidation achieves overall anti-Markovnikov addition of water across the alkene to yield 1° alcohol."),
                ("The reaction of chlorobenzene with chloromethane and sodium in dry ether to form toluene is called:",
                 ["Wurtz-Fittig reaction", "Fittig reaction", "Wurtz reaction", "Frankland reaction"], 0, "Haloalkanes and Haloarenes", "Wurtz-Fittig reaction couples an aryl halide with an alkyl halide in the presence of sodium metal in dry ether."),
                ("The reaction of two molecules of chlorobenzene with sodium metal in dry ether to yield diphenyl is called:",
                 ["Fittig reaction", "Wurtz reaction", "Ullmann reaction", "Sandmeyer reaction"], 0, "Haloalkanes and Haloarenes", "Fittig reaction couples two aryl halides via sodium in dry ether to form diaryl compounds (biphenyl)."),
                ("Conversion of aniline to benzenediazonium chloride using NaNO₂ and dilute HCl at 273-278 K is called:",
                 ["Diazotization", "Sandmeyer reaction", "Gattermann reaction", "Coupling reaction"], 0, "Amines", "Diazotization transforms primary aromatic amines into diazonium salts at low temperatures (0-5 °C)."),
                ("The reaction of benzenediazonium chloride with fluoroboric acid (HBF₄) followed by heating to yield fluorobenzene is called:",
                 ["Balz-Schiemann reaction", "Sandmeyer reaction", "Gattermann reaction", "Swarts reaction"], 0, "Haloalkanes and Haloarenes", "Thermal decomposition of benzenediazonium fluoroborate yields fluorobenzene, known as the Balz-Schiemann reaction."),
                ("Reaction of benzenediazonium chloride with cuprous cyanide (CuCN) and KCN yields:",
                 ["Benzonitrile (Cyanobenzene)", "Chlorobenzene", "Nitrobenzene", "Aniline"], 0, "Amines", "Sandmeyer cyanidation replaces the diazonium group with -CN using CuCN/KCN."),
                # Additional Coordination & Inorganic Chemistry
                ("According to IUPAC nomenclature conventions, the coordination compound K₄[Fe(CN)₆] is named as:",
                 ["Potassium hexacyanidoferrate(II)", "Potassium hexacyanoiron(II)", "Potassium ferricyanide", "Tetrapotassium ferrocyanide"], 0, "Coordination Compounds", "K₄[Fe(CN)₆] has complex anion [Fe(CN)₆]⁴⁻ where iron is in +2 oxidation state, named potassium hexacyanidoferrate(II)."),
                ("The coordination compound [Co(NH₃)₅(SO₄)]Br and [Co(NH₃)₅Br]SO₄ represent which type of isomerism?",
                 ["Ionization isomerism", "Linkage isomerism", "Coordination isomerism", "Geometrical isomerism"], 0, "Coordination Compounds", "They give different ions in aqueous solution (one gives Br⁻ while the other gives SO₄²⁻), exhibiting ionization isomerism."),
                ("The coordination compound [Co(NH₃)₅(NO₂)]Cl₂ and [Co(NH₃)₅(ONO)]Cl₂ represent which type of isomerism?",
                 ["Linkage isomerism", "Ionization isomerism", "Hydrate isomerism", "Optical isomerism"], 0, "Coordination Compounds", "The ambidentate ligand NO₂⁻ can coordinate through nitrogen (nitro) or oxygen (nitrito), displaying linkage isomerism."),
                ("The magnetic moment (spin-only) of a transition metal complex with 4 unpaired electrons is approximately:",
                 ["4.90 BM", "3.87 BM", "5.92 BM", "2.83 BM"], 0, "Coordination Compounds", "μ = √(n(n + 2)) BM = √(4(6)) = √24 ≈ 4.90 Bohr Magnetons."),
                ("The spin-only magnetic moment of [Mn(H₂O)₆]²⁺ containing 5 unpaired d-electrons is:",
                 ["5.92 BM", "4.90 BM", "3.87 BM", "1.73 BM"], 0, "Coordination Compounds", "With 5 unpaired electrons (3d⁵ high spin): μ = √(5(7)) = √35 ≈ 5.92 BM."),
                ("In the qualitative brown ring test for nitrate ions, the brown ring complex formed at the liquid junction is:",
                 ["[Fe(H₂O)₅(NO)]SO₄", "[Fe(H₂O)₆]SO₄", "[Fe(NO)₆]SO₄", "[Fe(CN)₅(NO)]²⁻"], 0, "p-Block Elements", "Nitrate reduction produces nitric oxide (NO) which reacts with Fe²⁺ to form the pentaaquanitrosyliron(I) sulfate brown ring complex."),
                ("Which of the following transition elements exhibits the highest oxidation state of +8 in its oxides?",
                 ["Osmium (Os in OsO₄) and Ruthenium (Ru)", "Manganese (Mn)", "Chromium (Cr)", "Iron (Fe)"], 0, "d and f Block Elements", "Osmium and Ruthenium form volatile tetroxides (OsO₄, RuO₄) where the metal attains the maximum +8 oxidation state."),
                ("In qualitative group analysis of cations, Group II basic radicals are selectively precipitated as sulfides using:",
                 ["H₂S in the presence of dilute HCl", "H₂S in the presence of NH₄OH", "Ammonium carbonate", "Dilute NaOH alone"], 0, "General Principles and Processes of Isolation of Elements", "HCl suppresses the ionization of H₂S (common ion effect of H⁺), keeping [S²⁻] low enough to precipitate only sparingly soluble Group II sulfides."),
                ("Group III basic radicals (Fe³⁺, Al³⁺, Cr³⁺) are selectively precipitated as hydroxides using:",
                 ["NH₄OH in the presence of NH₄Cl", "Dilute NaOH", "H₂S in alkaline medium", "Ammonium oxalate"], 0, "General Principles and Processes of Isolation of Elements", "NH₄Cl suppresses the ionization of NH₄OH (common ion effect of NH₄⁺) so that only less soluble Group III hydroxides precipitate."),
                ("The Ziegler-Natta catalyst used for the low-pressure polymerization of ethene into high-density polythene (HDPE) is:",
                 ["Triethylaluminium and Titanium tetrachloride (Al(C₂H₅)₃ + TiCl₄)", "Nickel tetracarbonyl", "Vanadium pentoxide", "Palladium chloride"], 0, "Polymers", "Ziegler-Natta coordination catalyst Al(C₂H₅)₃ + TiCl₄ enables stereospecific linear coordination polymerization of ethylene."),
                ("The monomer units of the step-growth condensation polymer Dacron (Terylene) are:",
                 ["Ethylene glycol and Terephthalic acid", "Adipic acid and Hexamethylenediamine", "Phenol and Formaldehyde", "Caprolactam alone"], 0, "Polymers", "Dacron is a polyester prepared by condensation polymerization of ethylene glycol with terephthalic acid with elimination of water."),
                ("Natural rubber is a linear polymer of which repeating diene hydrocarbon monomer?",
                 ["Isoprene (2-methyl-1,3-butadiene)", "Chloroprene (2-chloro-1,3-butadiene)", "1,3-Butadiene", "Neoprene"], 0, "Polymers", "Natural rubber is cis-1,4-polyisoprene formed by 1,4-addition polymerization of isoprene units."),
                ("Which of the following carbohydrates is classified as a non-reducing disaccharide that does not reduce Tollens' or Fehling's reagents?",
                 ["Sucrose", "Maltose", "Lactose", "Glucose"], 0, "Biomolecules", "In sucrose, both anomeric carbons of glucose (C1) and fructose (C2) are involved in the glycosidic bond, preventing hemiacetal formation."),
                ("Which of the following 20 standard proteinogenic amino acids is optically inactive due to having two identical hydrogen atoms on its α-carbon?",
                 ["Glycine (H₂N-CH₂-COOH)", "Alanine", "Valine", "Leucine"], 0, "Biomolecules", "Glycine is the only achiral amino acid as its α-carbon is bonded to two hydrogen atoms, lacking an asymmetric carbon center."),
                ("In the human body, excess glucose is stored primarily in the liver and skeletal muscles in the form of the animal polysaccharide:",
                 ["Glycogen", "Starch", "Cellulose", "Amylose"], 0, "Biomolecules", "Glycogen (animal starch) is a highly branched polymer of α-D-glucose that serves as the secondary long-term energy storage in animals."),
                ("Deficiency of Vitamin B₁ (Thiamine) in human nutrition leads to the clinical disorder called:",
                 ["Beriberi", "Scurvy", "Rickets", "Pellagra"], 0, "Biomolecules", "Thiamine deficiency causes beriberi, affecting the cardiovascular and peripheral nervous systems."),
                ("Deficiency of Vitamin D in children impairs calcium absorption from the intestine and causes:",
                 ["Rickets", "Scurvy", "Night blindness", "Osteomalacia"], 0, "Biomolecules", "Vitamin D regulates calcium and phosphate homeostasis; deficiency in children leads to softening and weakening of bones (rickets)."),
                ("The noble gas that does NOT occur naturally in the atmosphere and is obtained from radioactive disintegration of Radium is:",
                 ["Radon (Rn)", "Xenon (Xe)", "Krypton (Kr)", "Argon (Ar)"], 0, "p-Block Elements", "Radon is a radioactive noble gas produced as a decay product of Radium-226 (²²⁶Ra -> ²²²Rn + ⁴He)."),
                ("Helium gas is added to the breathing gas mixtures of deep-sea commercial divers to prevent nitrogen narcosis because of its:",
                 ["Extremely low solubility in human blood and plasma", "High density", "Chemical reactivity", "High solubility in fats"], 0, "p-Block Elements", "Helium has very low solubility in blood under high ambient pressures, preventing decompression sickness ('the bends')."),
                ("In crystal lattices, Schottky defects are stoichiometric point defects characterized by:",
                 ["Equal number of cation and anion vacancies leaving the overall lattice electrically neutral but lowering density", "Interstitially displaced cations with constant density", "Excess metal ions in interstitial positions", "Non-stoichiometric metal deficiency"], 0, "Solid State", "Schottky defects occur in ionic solids where cations and anions are missing in equal stoichiometric ratios, lowering density (e.g. NaCl, KCl)."),
                ("Which of the following ionic crystals displays both Schottky defect and Frenkel defect in its crystal lattice?",
                 ["Silver bromide (AgBr)", "Sodium chloride (NaCl)", "Cesium chloride (CsCl)", "Zinc sulfide (ZnS)"], 0, "Solid State", "AgBr uniquely exhibits both Schottky and Frenkel defects due to intermediate ionic radius ratio between Ag⁺ and Br⁻."),
                ("According to the Hardy-Schulze rule in colloid chemistry, the coagulating power of an electrolyte for a negatively charged sol increases in the order of:",
                 ["Na⁺ < Ba²⁺ < Al³⁺", "Al³⁺ < Ba²⁺ < Na⁺", "Ba²⁺ < Na⁺ < Al³⁺", "Na⁺ < Al³⁺ < Ba²⁺"], 0, "Surface Chemistry", "The coagulating power of an active ion is directly proportional to the fourth power of its valency (Hardy-Schulze rule)."),
                ("A solution that shows positive deviation from Raoult's law exhibits:",
                 ["ΔH_mix > 0 (endothermic) and ΔV_mix > 0 with higher vapor pressure than ideal", "ΔH_mix < 0 and ΔV_mix < 0", "Lower vapor pressure than ideal", "Formation of maximum boiling azeotrope"], 0, "Solutions", "Positive deviation occurs when solute-solvent interactions are weaker than pure components (e.g. Ethanol + Acetone), giving ΔH_mix > 0 and ΔV_mix > 0."),
                ("Which of the following pairs of liquids forms an ideal solution obeying Raoult's law over the entire concentration range?",
                 ["n-Hexane and n-Heptane", "Ethanol and Acetone", "Chloroform and Acetone", "Phenol and Aniline"], 0, "Solutions", "Pairs with nearly identical molecular sizes and intermolecular forces (e.g. n-hexane + n-heptane, benzene + toluene) form near-ideal solutions."),
                # Coordination Chemistry Nomenclature, Magnetic Moments & Theories
                ("What is the primary valency (oxidation state) and secondary valency (coordination number) of cobalt in [Co(NH₃)₆]Cl₃?",
                 ["3 and 6", "6 and 3", "2 and 6", "3 and 3"], 0, "Coordination Compounds", "Primary valency is the oxidation state (+3), satisfied by 3 Cl⁻; secondary valency is coordination number (6), satisfied by 6 NH₃."),
                ("According to Werner's coordination theory, secondary valencies of a central transition metal ion are:",
                 ["Directional and satisfied by neutral molecules or negative ions", "Non-directional and ionizable", "Satisfied only by negative ions", "Variable with temperature"], 0, "Coordination Compounds", "Werner's secondary valency corresponds to coordination number; they are directed towards fixed positions in space."),
                ("Which of the following complex ions does NOT exhibit geometrical (cis-trans) isomerism?",
                 ["[Co(NH₃)₅Cl]²⁺", "[Pt(NH₃)₂Cl₂]", "[Co(NH₃)₄Cl₂]⁺", "[Pt(NH₃)₂Cl(Br)]"], 0, "Coordination Compounds", "Complexes of type [Ma₅b] have only one spatial arrangement and cannot form cis-trans isomers."),
                ("The coordination complex [Co(en)₃]³⁺ exhibits optical isomerism (enantiomerism) because its structure:",
                 ["Lacks any plane or center of symmetry (chiral)", "Has a square planar geometry", "Contains monodentate ligands only", "Is high-spin paramagnetic"], 0, "Coordination Compounds", "Octahedral complexes with three bidentate chelating ligands [M(aa)₃] are non-superimposable on their mirror images."),
                ("The systematic IUPAC name of the coordination compound [Pt(NH₃)₂Cl(NO₂)] is:",
                 ["Diamminechloridonitrito-N-platinum(II)", "Diamminechloronitroplatinum(IV)", "Dichlorodiammineplatinum(II)", "Platinumdiamminechloronitrite"], 0, "Coordination Compounds", "Ligands are listed alphabetically: ammine, chlorido, nitrito-N; platinum is in +2 oxidation state."),
                ("The systematic IUPAC name of the complex compound K₃[Al(C₂O₄)₃] is:",
                 ["Potassium trioxalatoaluminate(III)", "Potassium aluminium oxalate", "Tripotassium trioxalatocobaltate", "Potassium aluminium trioxalate"], 0, "Coordination Compounds", "K⁺ counter ion followed by trioxalatoaluminate(III) where -ate is added because the complex entity is an anion."),
                ("The systematic IUPAC name of the neutral metal carbonyl [Ni(CO)₄] is:",
                 ["Tetracarbonylnickel(0)", "Tetracarbonylnickelate(II)", "Nickel tetracarbonyl(II)", "Tetracarbonnickel"], 0, "Coordination Compounds", "CO is a neutral ligand and nickel has zero oxidation state, named tetracarbonylnickel(0)."),
                ("Which of the following transition metal ions is completely colorless in aqueous solution due to a d¹⁰ configuration?",
                 ["Zn²⁺ (Zinc ion)", "Cu²⁺ (Copper ion)", "Fe³⁺ (Ferric ion)", "Co²⁺ (Cobalt ion)"], 0, "d and f Block Elements", "Zn²⁺ has [Ar] 3d¹⁰ configuration with completely filled d-subshell; d-d transitions cannot occur, making it colorless."),
                ("Which of the following transition metal ions is completely colorless in aqueous solution due to an empty d⁰ configuration?",
                 ["Sc³⁺ (Scandium ion)", "Fe²⁺ (Ferrous ion)", "Ni²⁺ (Nickel ion)", "Mn²⁺ (Manganous ion)"], 0, "d and f Block Elements", "Sc³⁺ has [Ar] 3d⁰ configuration with no d-electrons, preventing d-d absorption transitions."),
                ("The spin-only magnetic moment of Fe²⁺ ion ([Ar] 3d⁶, 4 unpaired electrons) is approximately:",
                 ["4.90 BM", "3.87 BM", "5.92 BM", "1.73 BM"], 0, "Coordination Compounds", "μ = √(n(n+2)) BM = √(4×6) = √24 ≈ 4.90 Bohr Magnetons."),
                ("The spin-only magnetic moment of Cr³⁺ ion ([Ar] 3d³, 3 unpaired electrons) is approximately:",
                 ["3.87 BM", "4.90 BM", "2.83 BM", "1.73 BM"], 0, "Coordination Compounds", "μ = √(3×5) = √15 ≈ 3.87 Bohr Magnetons."),
                ("The spin-only magnetic moment of Cu²⁺ ion ([Ar] 3d⁹, 1 unpaired electron) is approximately:",
                 ["1.73 BM", "2.83 BM", "3.87 BM", "0 BM"], 0, "Coordination Compounds", "μ = √(1×3) = √3 ≈ 1.73 Bohr Magnetons."),
                ("The spin-only magnetic moment of Ni²⁺ ion ([Ar] 3d⁸, 2 unpaired electrons) is approximately:",
                 ["2.83 BM", "3.87 BM", "4.90 BM", "1.73 BM"], 0, "Coordination Compounds", "μ = √(2×4) = √8 ≈ 2.83 Bohr Magnetons."),
                ("The spin-only magnetic moment of Fe³⁺ ion ([Ar] 3d⁵, 5 unpaired electrons) in high-spin state is:",
                 ["5.92 BM", "4.90 BM", "3.87 BM", "2.83 BM"], 0, "Coordination Compounds", "μ = √(5×7) = √35 ≈ 5.92 Bohr Magnetons."),
                ("The hexacyanidoferrate(II) complex ion [Fe(CN)₆]⁴⁻ is diamagnetic because CN⁻ is a:",
                 ["Strong field ligand that forces pairing of all 6 d-electrons into t₂g subshell", "Weak field ligand with high spin", "Neutral ligand", "Chelating multidentate ligand"], 0, "Coordination Compounds", "CN⁻ produces large crystal field splitting Δo > P, forcing electron pairing into t₂g⁶ eg⁰ (diamagnetic)."),
                # Organic Conversions, Distinctions & Reaction Mechanisms
                ("The coupling conversion of an alkyl halide to an alkane with double the carbon atoms using sodium in dry ether is called the:",
                 ["Wurtz reaction", "Frankland reaction", "Kolbe reaction", "Fittig reaction"], 0, "Haloalkanes and Haloarenes", "2 R-X + 2 Na -> R-R + 2 NaX (Wurtz reaction)."),
                ("The cross-coupling of two aryl halides in the presence of copper powder at elevated temperature to form biphenyl is the:",
                 ["Ullmann reaction", "Wurtz reaction", "Frankland reaction", "Sandmeyer reaction"], 0, "Haloalkanes and Haloarenes", "Ullmann condensation utilizes copper powder to couple aryl iodides/bromides into biaryls."),
                ("In the Hinsberg test, the sulfonamide product obtained from a primary amine dissolves in aqueous KOH because:",
                 ["The sulfonamide nitrogen atom still bears an acidic hydrogen atom", "It forms a covalent ether linkage", "It hydrolyzes to benzoic acid", "Primary amines cannot form sulfonamides"], 0, "Amines", "R-NH-SO₂Ph has an acidic hydrogen on nitrogen due to strong electron-withdrawing -SO₂- group, forming soluble potassium salt."),
                ("In the Hinsberg test to distinguish amines, secondary amines react to produce a sulfonamide that is:",
                 ["Insoluble in aqueous KOH", "Soluble in aqueous KOH", "A gaseous product", "Unreactive towards benzenesulfonyl chloride"], 0, "Amines", "R₂N-SO₂Ph lacks any hydrogen atom on nitrogen and cannot form a water-soluble potassium salt."),
                ("Tertiary amines do NOT react with Hinsberg's reagent (benzenesulfonyl chloride) because they:",
                 ["Completely lack any replaceable hydrogen atom on the nitrogen atom", "Are too acidic to react", "Undergo immediate cleavage", "Form explosive diazonium salts"], 0, "Amines", "3° amines (R₃N) have no replaceable hydrogen on nitrogen to eliminate HCl with Ar-SO₂Cl."),
                ("The Hell-Volhard-Zelinsky (HVZ) reaction specifically chlorinates or brominates carboxylic acids at which position?",
                 ["α-Carbon position (bearing α-hydrogen)", "β-Carbon position", "Carboxyl carbon position", "Terminal methyl position"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Carboxylic acids with α-hydrogen react with Cl₂/Br₂ in the presence of red phosphorus to yield α-halocarboxylic acids."),
                ("The alkaline hydrolysis of esters using aqueous sodium hydroxide to yield carboxylate salts and alcohol is termed:",
                 ["Saponification", "Esterification", "Transesterification", "Decarboxylation"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Base-promoted ester hydrolysis is known as saponification because it is traditionally used in soap manufacturing."),
                ("When benzaldehyde is heated with concentrated 50% aqueous NaOH, it undergoes disproportionation into benzyl alcohol and sodium benzoate. This is the:",
                 ["Cannizzaro reaction", "Aldol condensation", "Perkin reaction", "Benzoin condensation"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Aldehydes lacking α-hydrogen (such as HCHO and C₆H₅CHO) undergo self-oxidation and reduction (Cannizzaro reaction)."),
                ("The reduction of alkyl cyanides (nitriles) to corresponding aldehydes using SnCl₂ and concentrated HCl followed by steam hydrolysis is the:",
                 ["Stephen reduction", "Clemmensen reduction", "Rosenmund reduction", "Etard reaction"], 0, "Aldehydes, Ketones and Carboxylic Acids", "R-CN + SnCl₂/HCl -> R-CH=NH·HCl --(H₂O)--> R-CHO + NH₄Cl (Stephen reaction)."),
                ("The selective reduction of carboxylic esters and nitriles to aldehydes at -78 °C is best accomplished using:",
                 ["DIBAL-H (Diisobutylaluminium hydride)", "LiAlH₄ in dry ether", "NaBH₄ in ethanol", "H₂ over Raney Nickel"], 0, "Aldehydes, Ketones and Carboxylic Acids", "DIBAL-H selectively reduces esters and nitriles to aldehydes without reducing to alcohols at low temperatures."),
                ("Fehling's solution A contains aqueous copper sulfate, while Fehling's solution B consists of alkaline solution of:",
                 ["Sodium potassium tartrate (Rochelle salt)", "Sodium citrate", "Ammonium carbonate", "Potassium permanganate"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Rochelle salt (sodium potassium tartrate) acts as a chelating agent to keep Cu²⁺ ions in alkaline solution."),
                ("Aliphatic aldehydes reduce alkaline Fehling's solution upon heating to produce a red precipitate of:",
                 ["Cuprous oxide (Cu₂O)", "Cupric oxide (CuO)", "Metallic copper (Cu)", "Copper hydroxide (Cu(OH)₂)"], 0, "Aldehydes, Ketones and Carboxylic Acids", "R-CHO + 2 Cu²⁺ + 5 OH⁻ -> R-COO⁻ + Cu₂O↓ (red ppt) + 3 H₂O."),
                ("Schiff's reagent is prepared by decoloring an aqueous solution of magenta (rosaniline hydrochloride) dye with:",
                 ["Sulfur dioxide (SO₂)", "Chlorine gas", "Hydrogen peroxide", "Nitrous acid"], 0, "Aldehydes, Ketones and Carboxylic Acids", "Sulfurous acid / SO₂ decolors magenta dye to produce colorless Schiff's reagent, which restores pink color with aldehydes."),
                ("Cold, dilute neutral or alkaline potassium permanganate (KMnO₄) used for testing unsaturation in alkenes is known as:",
                 ["Baeyer's reagent", "Lucas reagent", "Tollens' reagent", "Fehling's reagent"], 0, "Hydrocarbons", "Baeyer's reagent oxidizes alkenes into vicinal glycols while discharging its characteristic purple permanganate color."),
                ("According to Markovnikov's rule, the addition of unsymmetrical HX to an unsymmetrical alkene adds the halide atom to the carbon with:",
                 ["Fewer hydrogen atoms (forming the more stable carbocation)", "More hydrogen atoms", "Equal number of hydrogens", "The terminal methyl group"], 0, "Haloalkanes and Haloarenes", "Electrophilic addition proceeds via the more stable carbocation intermediate (3° > 2° > 1°)."),
                ("The reaction of alcohols with thionyl chloride (SOCl₂) in pyridine yields exceptionally pure alkyl chlorides because:",
                 ["Both byproducts SO₂ and HCl are gases and escape from the reaction mixture", "It is an irreversible equilibrium", "Pyridine acts as an oxidizing agent", "No heat is required"], 0, "Haloalkanes and Haloarenes", "Darzens thionyl chloride process yields pure haloalkanes because SO₂ and HCl escape as gases."),
                ("Reaction of a Grignard reagent (RMgX) with formaldehyde (HCHO) followed by acid hydrolysis yields a:",
                 ["Primary alcohol (1° alcohol)", "Secondary alcohol (2° alcohol)", "Tertiary alcohol (3° alcohol)", "Carboxylic acid"], 0, "Alcohols, Phenols and Ethers", "Formaldehyde yields 1° alcohols with Grignard reagents; all other aldehydes yield 2° alcohols."),
                ("Reaction of a Grignard reagent (RMgX) with acetaldehyde (CH₃CHO) followed by acid hydrolysis produces a:",
                 ["Secondary alcohol (2° alcohol)", "Primary alcohol (1° alcohol)", "Tertiary alcohol (3° alcohol)", "Ketone"], 0, "Alcohols, Phenols and Ethers", "Nucleophilic attack on acetaldehyde carbonyl carbon produces a 2° alcohol upon protonation."),
                ("Reaction of a Grignard reagent (RMgX) with acetone (CH₃COCH₃) followed by acid hydrolysis produces a:",
                 ["Tertiary alcohol (3° alcohol)", "Secondary alcohol (2° alcohol)", "Primary alcohol (1° alcohol)", "Carboxylic acid"], 0, "Alcohols, Phenols and Ethers", "Addition of RMgX across ketone carbonyl yields a branched 3° alcohol."),
                ("Reaction of a Grignard reagent (RMgX) with solid carbon dioxide (dry ice) followed by acid hydrolysis produces a:",
                 ["Carboxylic acid (R-COOH)", "Aldehyde", "Primary alcohol", "Ester"], 0, "Aldehydes, Ketones and Carboxylic Acids", "RMgX adds across C=O bond of CO₂ to form halomagnesium carboxylate, which on hydrolysis yields R-COOH."),
                # Biomolecules, Polymers & Everyday Chemistry
                ("In amylose (the water-soluble fraction of starch), α-D-glucose units are linked exclusively by:",
                 ["α-1,4-Glycosidic linkages", "α-1,6-Glycosidic linkages", "β-1,4-Glycosidic linkages", "β-1,2-Glycosidic linkages"], 0, "Biomolecules", "Amylose is a linear unbranched polymer of α-D-glucose units joined by α-1,4-glycosidic bonds."),
                ("In amylopectin and glycogen, branching from the main linear chain occurs via which glycosidic linkage?",
                 ["α-1,6-Glycosidic linkage", "α-1,4-Glycosidic linkage", "β-1,4-Glycosidic linkage", "β-1,6-Glycosidic linkage"], 0, "Biomolecules", "Branch points along the α-1,4 linear backbone occur every 20-30 glucose units via α-1,6-glycosidic bonds."),
                ("Complete enzymatic or acid hydrolysis of the disaccharide maltose yields:",
                 ["Two molecules of D-glucose", "One glucose and one fructose", "One glucose and one galactose", "Two molecules of D-fructose"], 0, "Biomolecules", "Maltose is a reducing disaccharide composed of two α-D-glucose units linked by an α-1,4 bond."),
                ("Complete enzymatic or acid hydrolysis of the milk sugar lactose produces:",
                 ["One molecule of D-glucose and one molecule of D-galactose", "Two molecules of D-glucose", "One glucose and one fructose", "Two molecules of D-galactose"], 0, "Biomolecules", "Lactose consists of β-D-galactose and β-D-glucose joined by a β-1,4-glycosidic bond."),
                ("The spontaneous change in optical rotation of an optically active carbohydrate solution over time until equilibrium is reached is called:",
                 ["Mutarotation", "Inversion of cane sugar", "Optical resolution", "Racemization"], 0, "Biomolecules", "Mutarotation is the interconversion between α and β anomers via the open-chain form in solution."),
                ("The dipolar ionic form of an amino acid containing both positive and negative formal charges with net neutral charge is called a:",
                 ["Zwitterion", "Carbocation", "Carbanion", "Micelle"], 0, "Biomolecules", "Internal proton transfer from -COOH to -NH₂ produces the dipolar zwitterion H₃N⁺-CH(R)-COO⁻."),
                ("The characteristic pH at which an amino acid molecule carries zero net electrical charge and does not migrate in an electric field is called its:",
                 ["Isoelectric point (pI)", "Equivalence point", "Buffer capacity", "Neutrality index"], 0, "Biomolecules", "At the isoelectric point (pI), the zwitterion concentration is maximized with zero net charge."),
                ("The α-helix and β-pleated sheet secondary conformations of proteins are maintained and stabilized by:",
                 ["Hydrogen bonds between peptide >C=O and -NH- groups", "Covalent peptide bonds", "Disulfide covalent bonds alone", "Hydrophobic interactions alone"], 0, "Biomolecules", "Regular folding into α-helix and β-sheet is stabilized by hydrogen bonding between amide groups of the polypeptide chain."),
                ("In the double helical structure of DNA, complementary adenine (A) and thymine (T) bases are paired together by:",
                 ["Two hydrogen bonds", "Three hydrogen bonds", "One covalent bond", "Phosphodiester linkage"], 0, "Biomolecules", "Watson-Crick base pairing specifies 2 hydrogen bonds between A and T (A=T) and 3 between G and C (G≡C)."),
                ("In the double helical structure of DNA, complementary guanine (G) and cytosine (C) bases are paired together by:",
                 ["Three hydrogen bonds", "Two hydrogen bonds", "A disulfide bridge", "Four hydrogen bonds"], 0, "Biomolecules", "Guanine and cytosine form three specific hydrogen bonds (G≡C), making GC-rich DNA thermally more stable."),
                ("The pentose sugar present in the RNA polynucleotide backbone is:",
                 ["β-D-Ribose", "β-D-2-Deoxyribose", "α-D-Glucose", "β-D-Fructose"], 0, "Biomolecules", "RNA contains D-ribose (with 2'-OH group), whereas DNA contains 2'-deoxyribose (lacking 2'-OH)."),
                ("Deficiency of Vitamin B₁₂ (Cyanocobalamin) in human nutrition leads to the severe clinical condition:",
                 ["Pernicious anemia (RBC deficiency)", "Scurvy", "Rickets", "Beriberi"], 0, "Biomolecules", "Vitamin B₁₂ is essential for erythrocyte maturation; lack of intrinsic factor/dietary deficiency causes pernicious anemia."),
                ("Deficiency of Vitamin A (Retinol) causes dry, keratinized cornea and night blindness, medically diagnosed as:",
                 ["Xerophthalmia and Nyctalopia", "Pellagra", "Cheilosis", "Osteomalacia"], 0, "Biomolecules", "Vitamin A forms rhodopsin in retinal rod cells; deficiency causes night blindness and hardening of the cornea (xerophthalmia)."),
                ("Aspirin (acetylsalicylic acid) is commonly synthesized by acetylating salicylic acid using:",
                 ["Acetic anhydride in the presence of concentrated H₂SO₄", "Acetyl chloride alone", "Glacial acetic acid alone", "Ethanol and HCl"], 0, "Chemistry in Everyday Life", "Salicylic acid + (CH₃CO)₂O --(H⁺)--> Acetylsalicylic acid (Aspirin) + CH₃COOH."),
                ("Dettol, the widely used household antiseptic and wound cleansing solution, is an active formulated mixture of:",
                 ["Chloroxylenol and α-terpineol", "Bithionol and phenol", "Chloramphenicol and ethanol", "Formaldehyde and glycerol"], 0, "Chemistry in Everyday Life", "Dettol active ingredients are chloroxylenol (4.8% w/v) and α-terpineol dissolved in pine oil and soap solution."),
                ("The artificial sweetener that is unstable at elevated baking/cooking temperatures and used only in cold drinks and cold foods is:",
                 ["Aspartame", "Sucralose", "Saccharin", "Alitame"], 0, "Chemistry in Everyday Life", "Aspartame (methyl ester of aspartic acid-phenylalanine dipeptide) decomposes at cooking temperatures."),
                ("Nylon-6 is an industrial polyamide manufactured by heating which cyclic monomer with water at 533-543 K?",
                 ["Caprolactam", "Adipic acid", "Hexamethylenediamine", "Acrylonitrile"], 0, "Polymers", "Ring-opening polymerization of caprolactam yields the linear polyamide Nylon-6."),
                ("Nylon-6,6 is a step-growth condensation copolymer prepared from the industrial monomers:",
                 ["Hexamethylenediamine and Adipic acid", "Caprolactam and Glycine", "Ethylene glycol and Phthalic acid", "Phenol and Formaldehyde"], 0, "Polymers", "Hexamethylenediamine (6 carbons) and adipic acid (6 carbons) eliminate water to produce Nylon-6,6."),
                ("Teflon (polytetrafluoroethene, PTFE), celebrated for its non-stick and chemical inertness, is polymerized from:",
                 ["Tetrafluoroethene (F₂C=CF₂)", "Vinyl fluoride", "Chlorotrifluoroethene", "Fluoroethane"], 0, "Polymers", "Free-radical addition polymerization of tetrafluoroethene under high pressure with persulfate catalyst forms Teflon."),
                ("Neoprene is a synthetic rubber manufactured by the free-radical coordination polymerization of:",
                 ["Chloroprene (2-chloro-1,3-butadiene)", "Isoprene (2-methyl-1,3-butadiene)", "1,3-Butadiene", "Styrene"], 0, "Polymers", "Chloroprene polymerizes to form polychloroprene (Neoprene), which is highly resistant to oils and petroleum."),
                ("Buna-N is a synthetic elastomer copolymerized from:",
                 ["1,3-Butadiene and Acrylonitrile", "1,3-Butadiene and Styrene", "Isobutylene and Isoprene", "Chloroprene and Styrene"], 0, "Polymers", "Buna-N (nitrile rubber) combines 1,3-butadiene and acrylonitrile, offering exceptional resistance to oils and solvents."),
                ("Buna-S is an elastomer prepared by the copolymerization of:",
                 ["1,3-Butadiene and Styrene", "1,3-Butadiene and Acrylonitrile", "Isoprene and Ethylene", "Propene and Butene"], 0, "Polymers", "Buna-S (styrene-butadiene rubber, SBR) is synthesized from 1,3-butadiene and styrene with sodium catalyst."),
                ("Bakelite is an infusible, cross-linked thermosetting resin prepared by the step-growth condensation of:",
                 ["Phenol and Formaldehyde", "Melamine and Formaldehyde", "Urea and Formaldehyde", "Ethylene glycol and Terephthalic acid"], 0, "Polymers", "Novolac linear chains cross-link upon heating with formaldehyde to produce infusible three-dimensional Bakelite."),
                # Inorganic p-Block, d-Block & Metallurgy Principles
                ("In the Ostwald process for the industrial manufacture of nitric acid (HNO₃), the catalytic oxidation of ammonia uses:",
                 ["Platinum-Rhodium gauze at 1100 K", "Vanadium pentoxide (V₂O₅)", "Finely divided iron with molybdenum", "Copper wire at 573 K"], 0, "p-Block Elements", "4 NH₃ + 5 O₂ --(Pt/Rh, 1100 K)--> 4 NO + 6 H₂O is the initial catalytic step in the Ostwald process."),
                ("The basicity (number of replaceable ionizable protons) of hypophosphorous acid (H₃PO₂) is equal to:",
                 ["1 (monobasic)", "2 (dibasic)", "3 (tribasic)", "0"], 0, "p-Block Elements", "H₃PO₂ has only one P-OH bond and two P-H bonds, acting as a monobasic acid."),
                ("Hypophosphorous acid (H₃PO₂) acts as a powerful chemical reducing agent primarily due to the presence of:",
                 ["Two P-H covalent bonds", "One P=O bond", "One P-OH bond", "High oxidation state of phosphorus"], 0, "p-Block Elements", "P-H bonds have low bond energy and readily donate hydrogen atoms, making H₃PO₂ a powerful reducing agent."),
                ("In the commercial Deacon process for the manufacture of chlorine from HCl, the heterogeneous catalyst used is:",
                 ["Cupric chloride (CuCl₂)", "Vanadium pentoxide", "Finely divided iron", "Manganese dioxide"], 0, "p-Block Elements", "4 HCl + O₂ --(CuCl₂, 723 K)--> 2 Cl₂ + 2 H₂O (Deacon's process)."),
                ("Among the Group 15 pnictogen hydrides, the strongest reducing agent is:",
                 ["BiH₃ (Bismuthine)", "SbH₃", "AsH₃", "NH₃"], 0, "p-Block Elements", "Down the group, the E-H bond length increases and bond dissociation enthalpy decreases, making BiH₃ the strongest reducing hydride."),
                ("Neil Bartlett discovered the first noble gas compound Xe⁺[PtF₆]⁻ by drawing an analogy between the ionization enthalpy of xenon and that of:",
                 ["Molecular oxygen (O₂)", "Molecular nitrogen (N₂)", "Argon gas", "Fluorine gas"], 0, "p-Block Elements", "O₂ has first ionization energy of 1175 kJ/mol while Xe is 1170 kJ/mol, leading Bartlett to oxidize Xe with PtF₆."),
                ("According to VSEPR theory, the molecular geometry and hybridization of xenon difluoride (XeF₂) are:",
                 ["Linear geometry with sp³d hybridization (3 equatorial lone pairs)", "Bent shape with sp² hybridization", "T-shaped with sp³d hybridization", "Tetrahedral with sp³ hybridization"], 0, "p-Block Elements", "XeF₂ has 2 bond pairs and 3 equatorial lone pairs in a trigonal bipyramid, giving a linear molecule."),
                ("In the metallurgy of copper, the molten matte obtained from the blast furnace is a mixture of:",
                 ["Cu₂S and FeS", "Cu₂O and FeO", "CuSO₄ and FeS", "Metallic Cu and Fe"], 0, "General Principles and Processes of Isolation of Elements", "Cuprous sulfide (Cu₂S) and ferrous sulfide (FeS) constitute the molten copper matte transferred to the Bessemer converter."),
                ("Zone refining (fractional crystallization) is widely used for the ultra-refining of semiconductors based on the principle that:",
                 ["Impurities are more soluble in the molten melt zone than in the solid metal", "Impurities have higher boiling points", "Impurities form volatile iodides", "Metals expand upon cooling"], 0, "General Principles and Processes of Isolation of Elements", "A circular heater melts a narrow zone of the rod; impurities concentrate in the melt and are driven to one end."),
                ("In the extraction of iron in a blast furnace, the chemical composition of the molten slag that floats on molten iron is:",
                 ["Calcium silicate (CaSiO₃)", "Calcium carbonate (CaCO₃)", "Ferrous silicate (FeSiO₃)", "Aluminium silicate"], 0, "General Principles and Processes of Isolation of Elements", "CaO (basic flux from limestone) reacts with SiO₂ (acidic gangue) to form molten slag CaSiO₃."),
                ("In the chromyl chloride confirmatory test for chloride ions, the red-orange vapors formed when chloride salt is heated with K₂Cr₂O₇ and conc. H₂SO₄ consist of:",
                 ["Chromyl chloride (CrO₂Cl₂)", "Chromic chloride (CrCl₃)", "Chromium trioxide (CrO₃)", "Chlorine dioxide (ClO₂)"], 0, "d and f Block Elements", "4 Cl⁻ + K₂Cr₂O₇ + 6 H₂SO₄ -> 2 CrO₂Cl₂↑ (red vapors) + 2 KHSO₄ + 4 HSO₄⁻ + 3 H₂O."),
                # Solid State, Electrochemistry & Colligative Properties
                ("The number of atoms per unit cell in a face-centered cubic (FCC) crystal lattice is:",
                 ["4", "2", "1", "8"], 0, "Solid State", "FCC has 8 corner atoms (8 × 1/8 = 1) and 6 face-centered atoms (6 × 1/2 = 3), total = 4 atoms/unit cell."),
                ("The number of atoms per unit cell in a body-centered cubic (BCC) crystal lattice is:",
                 ["2", "4", "1", "6"], 0, "Solid State", "BCC has 8 corner atoms (8 × 1/8 = 1) and 1 center atom (1 × 1 = 1), total = 2 atoms/unit cell."),
                ("The atomic packing efficiency in a face-centered cubic (FCC/CCP) crystal lattice is equal to:",
                 ["74%", "68%", "52.4%", "78%"], 0, "Solid State", "FCC has the highest cubic packing efficiency of 74% (empty space = 26%)."),
                ("The atomic packing efficiency in a body-centered cubic (BCC) crystal lattice is equal to:",
                 ["68%", "74%", "52.4%", "60%"], 0, "Solid State", "BCC packing efficiency is 68% (empty space = 32%)."),
                ("The coordination number of each sphere in a face-centered cubic (FCC/CCP) close-packed lattice is:",
                 ["12", "8", "6", "4"], 0, "Solid State", "Each sphere in FCC touches 6 neighbors in its own layer, 3 in the layer above, and 3 in the layer below (total = 12)."),
                ("The intense yellow color of sodium chloride crystals heated in sodium metal vapor is caused by:",
                 ["F-centres (electrons trapped in anion vacancies)", "Schottky defects alone", "Interstitial sodium cations", "Frenkel defects"], 0, "Solid State", "Cl⁻ ions diffuse to the surface leaving anion vacancies occupied by electrons from Na atoms, forming color F-centres."),
                ("In a commercial lead storage battery, the chemical substance composing the positive electrode (cathode) during discharge is:",
                 ["Lead dioxide (PbO₂)", "Spongy lead (Pb)", "Lead sulfate (PbSO₄)", "Lead monoxide (PbO)"], 0, "Electrochemistry", "Cathode is a grid of lead packed with lead dioxide (PbO₂); anode is spongy lead."),
                ("A binary liquid mixture of chloroform and acetone shows negative deviation from Raoult's law because:",
                 ["Strong intermolecular hydrogen bonds form between chloroform and acetone molecules", "Vapor pressure increases", "Intermolecular forces are weaker than pure components", "Enthalpy of mixing is highly endothermic"], 0, "Solutions", "Cl₃C-H forms an intermolecular hydrogen bond with the carbonyl oxygen of (CH₃)₂C=O, lowering vapor pressure."),
                ("A maximum boiling azeotrope is formed by binary liquid solutions that exhibit:",
                 ["Large negative deviation from Raoult's law (e.g. 68% HNO₃ + 32% H₂O)", "Large positive deviation from Raoult's law", "Ideal solution behavior", "Complete immiscibility"], 0, "Solutions", "Negative deviation creates stronger intermolecular attraction, lowering vapor pressure and elevating boiling point above components."),
                ("Phenol is significantly more acidic than ethanol primarily because:",
                 ["The phenoxide conjugate base is stabilized by resonance delocalization of negative charge into the benzene ring", "Ethanol has higher molecular weight", "Phenol has an sp³ oxygen", "Ethanol forms no hydrogen bonds"], 0, "Alcohols, Phenols and Ethers", "Resonance stabilizes the phenoxide ion over non-resonance-stabilized ethoxide ion, increasing phenol acidity."),
                ("o-Nitrophenol is steam volatile and possesses a lower boiling point than p-nitrophenol because of:",
                 ["Intramolecular hydrogen bonding (chelation)", "Intermolecular hydrogen bonding", "High dipole moment", "Resonance inhibition"], 0, "Alcohols, Phenols and Ethers", "Intramolecular H-bonding within the same molecule in o-nitrophenol prevents intermolecular association, enhancing steam volatility."),
                ("The inversion of stereochemical configuration at an asymmetric chiral carbon during an SN2 nucleophilic substitution is termed:",
                 ["Walden inversion", "Racemization", "Retention of configuration", "Mutarotation"], 0, "Haloalkanes and Haloarenes", "Backside nucleophilic attack in SN2 forces the three substituents to umbrella-invert, known as Walden inversion."),
                ("The dehydrohalogenation of 2-bromobutane with alcoholic KOH predominantly yields but-2-ene according to:",
                 ["Saytzeff's (Zaitsev's) rule", "Markovnikov's rule", "Hofmann's rule", "Kharasch effect"], 0, "Haloalkanes and Haloarenes", "Saytzeff's rule states that the major alkene product is the more substituted, thermodynamically more stable alkene."),
            ]

            for q_text, opts, ans_idx, topic_name, exp_text in fact_reaction_pool:
                q = {
                    "q": q_text,
                    "opts": opts,
                    "ans": ans_idx,
                    "topic": topic_name,
                    "subtype": "fact_reaction",
                    "exp": exp_text
                }
                if _add_q(q): return generated

    # ── 3. Mathematics Templates ─────────────────────────────────────────────
    elif "math" in topic_lower:
        det_data = [
            (2, 3, 1, 4), (5, 2, 3, 1), (4, 1, 2, 3), (6, 2, 4, 3),
            (3, 1, 2, 5), (7, 2, 3, 1), (1, 4, 2, 5), (8, 3, 2, 4),
            (9, 1, 3, 2), (6, 5, 2, 3), (7, 4, 1, 2), (5, 3, 4, 2)
        ]
        for a, b, c, d in det_data:
            val = a * d - b * c
            q = {
                "q": f"If A is the 2x2 matrix [[{a}, {b}], [{c}, {d}]], then the determinant |A| is equal to:",
                "opts": [f"{val}", f"{val + 2}", f"{val - 3}", f"{val * 2}"],
                "ans": 0,
                "topic": "Determinants",
                "subtype": "direct_formula",
                "exp": f"|A| = ({a})({d}) - ({b})({c}) = {a*d} - {b*c} = {val}."
            }
            if _add_q(q): return generated

    # ── 3. Mathematics Variations ───────────────────────────────────────────
    elif "math" in topic_lower:
        from .mathematics_bank import MATHEMATICS_BANK
        for q_item in MATHEMATICS_BANK:
            q = {
                "q": q_item["q"],
                "opts": list(q_item["opts"]),
                "ans": q_item["ans"],
                "topic": q_item.get("topic", "Mathematics"),
                "subtype": q_item.get("subtype", "direct_formula"),
                "exp": q_item.get("exp", "")
            }
            if _add_q(q): return generated

    # ── 4. Biology Templates ─────────────────────────────────────────────────
    else:
        bio_pool = [bq for bq in BIOLOGY_BANK if (not allowed_list or is_topic_matching(bq.get("topic", ""), allowed_list))]
        for bq in bio_pool:
            if bq["q"] not in used_texts:
                q = {
                    "q": bq["q"],
                    "opts": list(bq["opts"]),
                    "ans": bq["ans"],
                    "topic": bq["topic"],
                    "subtype": "theory_definition",
                    "exp": bq.get("exp", "")
                }
                if _add_q(q): return generated

    return generated


def generate_fallback_mcqs(
    text: str,
    topic: str = "General",
    max_questions: int = 60,
    used_questions: Optional[set[str]] = None,
    allowed_topics: Optional[Iterable[str]] = None,
) -> List[dict]:

    """Generate high-quality fallback questions adhering strictly to KCET blueprint percentages:
    
    Physics (60 Questions per Set):
    - Direct formula substitution: ~35% (21 questions)
    - Multi-step conceptual problem solving: ~20% (12 questions)
    - Pure theory & definition-based: ~45% (27 questions)
    Total calculations in Physics: 33/60 = 55.0% (strictly within 50% to 60%).
    
    Chemistry (60 Questions per Set):
    - Numerical problems (Physical Chemistry): 10% (6 questions, strictly within 5 to 8 out of 60 / ~8% to 12%)
    - Direct fact, memory, or reaction-based (Organic & Inorganic): 90% (54 questions, strictly ~88% to 92%)
    Total calculations in Chemistry: 6/60 = 10.0% (strictly within 10% to 15%).
    """
    topic_lower = topic.lower()
    results = []
    used_texts: set[str] = set(used_questions) if used_questions else set()

    if "physic" in topic_lower:
        # Physics Blueprint Quotas at 60 questions
        n_direct = round(0.35 * max_questions)  # 21 when max_questions=60
        n_multi = round(0.20 * max_questions)   # 12 when max_questions=60
        n_theory = max(1, max_questions - n_direct - n_multi)  # 27 when max_questions=60

        # 1. Direct Formula Substitution Bucket
        avail_direct = [q for q in PHYSICS_DIRECT_FORMULA_BANK if q["q"] not in used_texts]
        random.shuffle(avail_direct)
        sel_direct = avail_direct[:n_direct]
        for q in sel_direct:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "direct_formula", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(sel_direct) < n_direct:
            topup = _generate_subject_variations(topic, n_direct - len(sel_direct), used_texts, subtype_filter="direct_formula")
            results.extend(topup)

        # 2. Multi-Step Problem Solving Bucket
        avail_multi = [q for q in PHYSICS_MULTI_STEP_BANK if q["q"] not in used_texts]
        random.shuffle(avail_multi)
        sel_multi = avail_multi[:n_multi]
        for q in sel_multi:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "multi_step", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(sel_multi) < n_multi:
            topup = _generate_subject_variations(topic, n_multi - len(sel_multi), used_texts, subtype_filter="multi_step")
            results.extend(topup)

        # 3. Pure Theory & Definition Bucket
        avail_theory = [q for q in PHYSICS_THEORY_BANK if q["q"] not in used_texts]
        random.shuffle(avail_theory)
        sel_theory = avail_theory[:n_theory]
        for q in sel_theory:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "theory_definition", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(sel_theory) < n_theory:
            topup = _generate_subject_variations(topic, n_theory - len(sel_theory), used_texts, subtype_filter="theory_definition")
            results.extend(topup)
        if len(results) < max_questions:
            needed = max_questions - len(results)
            topup = _generate_subject_variations(topic, needed, used_texts)
            results.extend(topup)

    elif "chem" in topic_lower:
        # Chemistry Blueprint Quotas at 60 questions: 6 numericals, 54 reaction & memory facts
        n_num = max(1, round(0.10 * max_questions))  # 6 when max_questions=60
        n_fact = max_questions - n_num              # 54 when max_questions=60

        # 1. Physical Chemistry Numericals Bucket
        avail_num = [q for q in CHEMISTRY_NUMERICAL_BANK if q["q"] not in used_texts]
        random.shuffle(avail_num)
        sel_num = avail_num[:n_num]
        for q in sel_num:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "physical_numerical", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(sel_num) < n_num:
            topup = _generate_subject_variations(topic, n_num - len(sel_num), used_texts, subtype_filter="physical_numerical")
            results.extend(topup)

        # 2. Direct Fact, Memory & Reaction Bucket
        avail_fact = [q for q in CHEMISTRY_FACT_REACTION_BANK if q["q"] not in used_texts]
        random.shuffle(avail_fact)
        sel_fact = avail_fact[:n_fact]
        for q in sel_fact:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "fact_reaction", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(sel_fact) < n_fact:
            topup = _generate_subject_variations(topic, n_fact - len(sel_fact), used_texts, subtype_filter="fact_reaction")
            results.extend(topup)
        if len(results) < max_questions:
            needed = max_questions - len(results)
            topup = _generate_subject_variations(topic, needed, used_texts)
            results.extend(topup)

    elif "math" in topic_lower:
        bank = [q for q in MATHEMATICS_BANK if q["q"] not in used_texts and is_valid_question(q["q"], q["opts"], subject="Mathematics")]
        random.shuffle(bank)
        pool_size = max(max_questions * 3, len(bank))
        selected = bank[:pool_size]
        for q in selected:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": q.get("subtype", "direct_formula"), "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(results) < max_questions:
            needed = max_questions - len(results)
            variations = _generate_subject_variations(topic, needed, used_texts)
            results.extend(variations)

    else:
        allowed_list = list(allowed_topics) if allowed_topics else None
        bank = [
            q for q in BIOLOGY_BANK
            if q["q"] not in used_texts and (not allowed_list or is_topic_matching(q.get("topic", ""), allowed_list))
        ]
        random.shuffle(bank)
        selected = bank[:min(max_questions, len(bank))]
        for q in selected:
            results.append({
                "q": q["q"], "opts": list(q["opts"]), "ans": q["ans"],
                "topic": q["topic"], "subtype": "theory_definition", "exp": q.get("exp", "")
            })
            used_texts.add(q["q"])
        if len(results) < max_questions:
            needed = max_questions - len(results)
            variations = _generate_subject_variations(topic, needed, used_texts, allowed_topics=allowed_list)
            results.extend(variations)

    # Randomize order while preserving balanced representation
    random.shuffle(results)
    logger.info("Provided %d authentic blueprint-balanced questions for %s", len(results), topic)
    return results


def extract_or_generate_mcqs(
    text: str,
    topic: str = "General",
    min_questions: int = 60,
    used_questions: Optional[set[str]] = None,
    allowed_topics: Optional[Iterable[str]] = None,
) -> List[dict]:
    """Extract MCQs from uploaded text via pattern matching or Groq LLM RAG extraction,
    ensuring all returned MCQs strictly contain valid 'subtype' blueprint classifications.
    Defaults to 60 questions per set.
    """
    used_set: set[str] = set(used_questions) if used_questions else set()
    allowed_list = list(allowed_topics) if allowed_topics else None

    extracted = extract_mcqs_from_text(text, topic=topic)
    extracted = [
        q for q in extracted
        if q["q"] not in used_set
        and is_valid_question(q["q"], q["opts"], subject=topic)
        and (not allowed_list or is_topic_matching(q.get("topic", ""), allowed_list))
    ]

    for q in extracted:
        if "subtype" not in q or not q["subtype"]:
            q["subtype"] = infer_question_subtype(q["q"], q["opts"], topic)
        used_set.add(q["q"])

    if len(extracted) >= min_questions:
        logger.info("Extracted %d valid MCQs from text patterns for %s", len(extracted), topic)
        return extracted[:min_questions]

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
                used_questions=used_set,
                questions_needed=needed,
            )
            for q in llm_results:
                if q.get("q") not in used_set and is_valid_question(q.get("q", ""), q.get("opts", []), subject=topic):
                    if allowed_list and not is_topic_matching(q.get("topic", ""), allowed_list):
                        continue
                    if "subtype" not in q or not q["subtype"]:
                        q["subtype"] = infer_question_subtype(q.get("q", ""), q.get("opts", []), topic)
                    rag_questions.append(q)
                    used_set.add(q.get("q"))
            logger.info("RAG LLM extracted %d valid MCQs from uploaded content for %s", len(rag_questions), topic)
        except Exception as exc:
            logger.warning("RAG LLM extraction failed (%s), falling back to authentic question bank", exc)

    combined = extracted + rag_questions
    if len(combined) < min_questions:
        still_needed = min_questions - len(combined)
        fallback = generate_fallback_mcqs(
            text, topic=topic, max_questions=still_needed, used_questions=used_set, allowed_topics=allowed_list
        )
        combined.extend(fallback)

    # Ensure every question has subtype
    for q in combined:
        if "subtype" not in q or not q["subtype"]:
            q["subtype"] = infer_question_subtype(q.get("q", ""), q.get("opts", []), topic)

    logger.info("Total MCQs for %s after RAG extraction & fallback: %d", topic, len(combined))
    return combined[:min_questions]


__all__ = [
    "extract_mcqs_from_text",
    "generate_fallback_mcqs",
    "extract_or_generate_mcqs",
    "is_valid_question",
    "is_valid_physics_question",
    "infer_question_subtype",
    "PHYSICS_DIRECT_FORMULA_BANK",
    "PHYSICS_MULTI_STEP_BANK",
    "PHYSICS_THEORY_BANK",
    "PHYSICS_NUMERICAL_BANK",
    "CHEMISTRY_NUMERICAL_BANK",
    "CHEMISTRY_FACT_REACTION_BANK",
    "CHEMISTRY_BANK",
    "MATHEMATICS_BANK",
    "BIOLOGY_BANK",
]

