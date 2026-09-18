"""Official KCET 2026 Chapter-Wise Weightage Blueprint & Subtype Distribution Engine.

Transcribed directly from official KCET 2026 examination blueprint tables and calculation targets:
- Physics: 50% to 60% calculations (Direct formula: 30-40%, Multi-step: 15-20%, Theory/definition: 40-50%).
- Chemistry: 10% to 15% calculations (Physical Chemistry numericals: 5-8 Qs / 8-12%, Reactions/Facts: 88-92%).
- Mathematics: Calculus, Algebra, Coordinate Geometry, Vectors & Probability balanced across 1st & 2nd PUC.
- Biology: Comprehensive 1st & 2nd PUC factual, physiology, genetic, and diagram-based concept questions.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("smartkcet.rag.blueprint")

# ─────────────────────────────────────────────────────────────────────────────
# 1. KCET 2026 Chapter-Wise Weightage Blueprint Definitions
# ─────────────────────────────────────────────────────────────────────────────

KCET_BLUEPRINT_2026: Dict[str, List[Dict[str, Any]]] = {
    "Physics": [
        # ── 1st PUC (Approx 30% of paper = ~18 questions) ──
        {
            "name": "Physical World, Units & Measurements",
            "puc": "1st PUC",
            "weight_pct_range": (2, 4),
            "expected_q": (1, 2),
            "avg_weight": 3.0,
            "aliases": ["physical world", "units and measurements", "units & measurements", "units"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Kinematics (Motion in Straight Line & Plane)",
            "puc": "1st PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["kinematics", "motion in a straight line", "motion in a plane", "projectile motion"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Laws of Motion & Friction",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["laws of motion", "friction", "newton's laws"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Work, Energy, Power & Collisions",
            "puc": "1st PUC",
            "weight_pct_range": (4, 6),
            "expected_q": (2, 4),
            "avg_weight": 5.0,
            "aliases": ["work, energy and power", "work energy power", "collisions", "power"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Gravitation",
            "puc": "1st PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["gravitation", "universal gravitation", "gravity", "satellites"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Mechanics of Solids & Fluids",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["mechanical properties of solids and fluids", "mechanical properties of fluids", "mechanical properties of solids", "solids and fluids", "fluid mechanics"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Thermodynamics & Kinetic Theory",
            "puc": "1st PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["thermodynamics", "kinetic theory of gases", "kinetic theory", "thermal properties of matter"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Oscillations & Waves",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["oscillations", "waves", "shm", "simple harmonic motion", "sound waves"],
            "primary_subtype": "direct_formula",
        },
        # ── 2nd PUC (Approx 70% of paper = ~42 questions) ──
        {
            "name": "Electrostatics (Charges, Fields, Potential)",
            "puc": "2nd PUC",
            "weight_pct_range": (10, 12),
            "expected_q": (6, 7),
            "avg_weight": 11.0,
            "aliases": ["electric charges and fields", "electrostatic potential and capacitance", "electrostatics", "capacitors"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Current Electricity",
            "puc": "2nd PUC",
            "weight_pct_range": (8, 10),
            "expected_q": (5, 6),
            "avg_weight": 9.0,
            "aliases": ["current electricity", "circuits", "kirchhoff's laws", "wheatstone bridge"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Magnetic Effects of Current & Magnetism",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["moving charges and magnetism", "magnetism and matter", "magnetism", "biot savart"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Electromagnetic Induction & AC",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["electromagnetic induction", "alternating current", "ac circuits", "faraday's laws", "emi"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Ray Optics & Wave Optics",
            "puc": "2nd PUC",
            "weight_pct_range": (10, 12),
            "expected_q": (6, 7),
            "avg_weight": 11.0,
            "aliases": ["ray optics and optical instruments", "wave optics", "optics", "lenses", "interference", "diffraction"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Modern Physics (Dual Nature, Atoms, Nuclei)",
            "puc": "2nd PUC",
            "weight_pct_range": (8, 10),
            "expected_q": (5, 6),
            "avg_weight": 9.0,
            "aliases": ["dual nature of radiation and matter", "atoms", "nuclei", "photoelectric effect", "bohr model", "radioactivity"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Semiconductors & Electronics",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["semiconductor electronics", "semiconductors", "diodes", "logic gates", "transistors"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Electromagnetic Waves & Communication",
            "puc": "2nd PUC",
            "weight_pct_range": (3, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.0,
            "aliases": ["electromagnetic waves", "communication systems", "em waves"],
            "primary_subtype": "theory_definition",
        },
    ],

    "Chemistry": [
        # ── 1st PUC ──
        {
            "name": "Some Basic Concepts of Chemistry",
            "puc": "1st PUC",
            "weight_pct_range": (7, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.5,
            "aliases": ["some basic concepts of chemistry", "mole concept", "stoichiometry"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Structure of Atom",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["structure of atom", "atomic structure", "quantum numbers"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Classification of Elements & Periodicity in Properties",
            "puc": "1st PUC",
            "weight_pct_range": (7, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.5,
            "aliases": ["classification of elements and periodicity in properties", "periodicity", "periodic table"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Chemical Bonding & Molecular Structure",
            "puc": "1st PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["chemical bonding and molecular structure", "chemical bonding", "vsepr", "hybridisation"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "States of Matter: Gases and Liquids",
            "puc": "1st PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["states of matter", "gaseous state", "gas laws"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Thermodynamics",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["thermodynamics", "chemical thermodynamics", "enthalpy"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Equilibrium",
            "puc": "1st PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 3),
            "avg_weight": 5.5,
            "aliases": ["equilibrium", "chemical equilibrium", "ionic equilibrium", "le chatelier"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Redox Reactions",
            "puc": "1st PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["redox reactions", "oxidation reduction"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Hydrogen",
            "puc": "1st PUC",
            "weight_pct_range": (3, 4),
            "expected_q": (2, 2),
            "avg_weight": 3.5,
            "aliases": ["hydrogen", "heavy water", "hydrides"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "s-Block Elements",
            "puc": "1st PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["s-block elements", "alkali metals", "alkaline earth metals"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Some p-Block Elements",
            "puc": "1st PUC",
            "weight_pct_range": (6, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.5,
            "aliases": ["some p-block elements", "group 13 and 14 elements", "boron carbon family"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Organic Chemistry – Basic Principles & Techniques",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["organic chemistry - some basic principles and techniques", "basic principles of organic chemistry", "goc", "iupac nomenclature"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Hydrocarbons",
            "puc": "1st PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["hydrocarbons", "alkanes", "alkenes", "alkynes", "aromatic hydrocarbons"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Environmental Chemistry",
            "puc": "1st PUC",
            "weight_pct_range": (2, 3),
            "expected_q": (1, 2),
            "avg_weight": 2.5,
            "aliases": ["environmental chemistry", "pollution", "green chemistry"],
            "primary_subtype": "fact_reaction",
        },
        # ── 2nd PUC ──
        {
            "name": "Solid State",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 4),
            "avg_weight": 7.0,
            "aliases": ["solid state", "crystal lattices", "bragg's law"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Solutions",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.5,
            "aliases": ["solutions", "colligative properties", "raoult's law", "osmotic pressure"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Electrochemistry",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["electrochemistry", "nernst equation", "galvanic cells", "kohlrausch law"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Chemical Kinetics",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["chemical kinetics", "rate of reaction", "arrhenius equation", "order of reaction"],
            "primary_subtype": "physical_numerical",
        },
        {
            "name": "Surface Chemistry",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 6),
            "expected_q": (2, 3),
            "avg_weight": 5.0,
            "aliases": ["surface chemistry", "adsorption", "colloids", "catalysis"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "General Principles & Processes of Isolation of Elements",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["general principles and processes of isolation of elements", "metallurgy", "isolation of elements", "general principal"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "p-Block Elements",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["p-block elements", "group 15 16 17 18 elements", "halogens", "noble gases"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "d & f Block Elements",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 4),
            "avg_weight": 7.0,
            "aliases": ["d and f block elements", "transition elements", "lanthanoids", "actinoids"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Coordination Compounds",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["coordination compounds", "werner's theory", "cft", "ligands"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Haloalkanes & Haloarenes",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 7),
            "expected_q": (4, 4),
            "avg_weight": 6.5,
            "aliases": ["haloalkanes and haloarenes", "haloalkanes", "alkyl halides", "sn1 sn2"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Alcohols, Phenols & Ethers",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["alcohols, phenols and ethers", "alcohols phenols ethers", "alcohols", "phenols"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Aldehydes, Ketones & Carboxylic Acids",
            "puc": "2nd PUC",
            "weight_pct_range": (8, 10),
            "expected_q": (5, 6),
            "avg_weight": 9.0,
            "aliases": ["aldehydes, ketones and carboxylic acids", "aldehydes and ketones", "carboxylic acids", "carbonyl compounds"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Amines (Organic Compounds Containing Nitrogen)",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["amines", "organic compounds containing nitrogen", "diazonium salts"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Biomolecules",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["biomolecules", "carbohydrates", "proteins", "nucleic acids", "vitamins"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Polymers",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 6),
            "expected_q": (2, 3),
            "avg_weight": 5.0,
            "aliases": ["polymers", "addition polymers", "condensation polymers", "synthetic rubbers"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Chemistry in Everyday Life",
            "puc": "2nd PUC",
            "weight_pct_range": (3, 5),
            "expected_q": (2, 2),
            "avg_weight": 4.0,
            "aliases": ["chemistry in everyday life", "drugs", "medicines", "detergents"],
            "primary_subtype": "fact_reaction",
        },
    ],

    "Mathematics": [
        # ── 1st PUC ──
        {
            "name": "Trigonometric Functions",
            "puc": "1st PUC",
            "weight_pct_range": (8, 10),
            "expected_q": (5, 6),
            "avg_weight": 9.0,
            "aliases": ["trigonometric functions", "trigonometry", "inverse trigonometry"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Straight Lines & Conic Sections",
            "puc": "1st PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["straight lines", "conic sections", "parabola", "ellipse", "hyperbola", "coordinate geometry"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Limits & Derivatives",
            "puc": "1st PUC",
            "weight_pct_range": (6, 7),
            "expected_q": (4, 4),
            "avg_weight": 6.5,
            "aliases": ["limits and derivatives", "limits", "derivatives"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Sets, Relations & Functions",
            "puc": "1st PUC",
            "weight_pct_range": (4, 6),
            "expected_q": (2, 4),
            "avg_weight": 5.0,
            "aliases": ["sets", "relations and functions", "relations & functions"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Complex Numbers & Quadratic Equations",
            "puc": "1st PUC",
            "weight_pct_range": (5, 7),
            "expected_q": (3, 4),
            "avg_weight": 6.0,
            "aliases": ["complex numbers and quadratic equations", "complex numbers", "quadratic equations"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Permutations & Combinations",
            "puc": "1st PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["permutations and combinations", "permutations & combinations", "p&c"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Binomial Theorem",
            "puc": "1st PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 3),
            "avg_weight": 5.5,
            "aliases": ["binomial theorem", "binomial expansions"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Probability & Statistics",
            "puc": "1st PUC",
            "weight_pct_range": (4, 6),
            "expected_q": (2, 4),
            "avg_weight": 5.0,
            "aliases": ["statistics", "probability"],
            "primary_subtype": "direct_formula",
        },
        # ── 2nd PUC ──
        {
            "name": "Integrals & Application of Integrals",
            "puc": "2nd PUC",
            "weight_pct_range": (9, 10),
            "expected_q": (5, 6),
            "avg_weight": 9.5,
            "aliases": ["integrals", "application of integrals", "definite integrals", "indefinite integrals"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Continuity & Differentiability",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["continuity and differentiability", "continuity", "differentiability"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Application of Derivatives",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["application of derivatives", "maxima minima", "tangents and normals"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Matrices & Determinants",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 9),
            "expected_q": (4, 5),
            "avg_weight": 8.0,
            "aliases": ["matrices", "determinants", "inverse of matrix"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Vectors & 3D Geometry",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.0,
            "aliases": ["vector algebra", "three dimensional geometry", "vectors", "3d geometry"],
            "primary_subtype": "direct_formula",
        },
        {
            "name": "Probability (Advanced)",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 7),
            "expected_q": (4, 4),
            "avg_weight": 6.5,
            "aliases": ["probability (advanced)", "bayes theorem", "conditional probability"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Differential Equations",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["differential equations", "integrating factor"],
            "primary_subtype": "multi_step",
        },
        {
            "name": "Linear Programming",
            "puc": "2nd PUC",
            "weight_pct_range": (3, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.0,
            "aliases": ["linear programming", "lpp", "feasible region"],
            "primary_subtype": "direct_formula",
        },
    ],

    "Biology": [
        # ── 1st PUC ──
        {
            "name": "Neural Control and Coordination",
            "puc": "1st PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["neural control and coordination", "nervous system", "brain", "reflex arc"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Photosynthesis in Higher Plants",
            "puc": "1st PUC",
            "weight_pct_range": (5, 5),
            "expected_q": (3, 3),
            "avg_weight": 5.0,
            "aliases": ["photosynthesis in higher plants", "photosynthesis", "calvin cycle", "c4 pathway"],
            "primary_subtype": "concept_application",
        },
        {
            "name": "Respiration in Plants",
            "puc": "1st PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["respiration in plants", "glycolysis", "krebs cycle", "ets"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Plant Growth and Development",
            "puc": "1st PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["plant growth and development", "auxin", "gibberellin", "photoperiodism"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Biomolecules",
            "puc": "1st PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["biomolecules", "enzymes", "amino acids", "nucleotides"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Plant Kingdom",
            "puc": "1st PUC",
            "weight_pct_range": (4, 4),
            "expected_q": (2, 3),
            "avg_weight": 4.0,
            "aliases": ["plant kingdom", "algae", "bryophytes", "pteridophytes", "gymnosperms", "angiosperms"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Cell: The Unit of Life",
            "puc": "1st PUC",
            "weight_pct_range": (4, 4),
            "expected_q": (2, 3),
            "avg_weight": 4.0,
            "aliases": ["cell: the unit of life", "cell the unit of life", "cell cycle and cell division", "mitosis", "meiosis"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Morphology of Flowering Plants",
            "puc": "1st PUC",
            "weight_pct_range": (3, 4),
            "expected_q": (2, 2),
            "avg_weight": 3.5,
            "aliases": ["morphology of flowering plants", "inflorescence", "flower", "fruit", "root stem leaf"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Digestion and Absorption",
            "puc": "1st PUC",
            "weight_pct_range": (3, 4),
            "expected_q": (2, 2),
            "avg_weight": 3.5,
            "aliases": ["digestion and absorption", "digestive system", "enzymes digestion"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Breathing and Exchange of Gases",
            "puc": "1st PUC",
            "weight_pct_range": (3, 3),
            "expected_q": (1, 2),
            "avg_weight": 3.0,
            "aliases": ["breathing and exchange of gases", "respiratory system", "gas exchange"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Excretory Products and their Elimination",
            "puc": "1st PUC",
            "weight_pct_range": (2, 3),
            "expected_q": (1, 2),
            "avg_weight": 2.5,
            "aliases": ["excretory products and their elimination", "nephron", "kidney", "urine formation"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Body Fluids and Circulation",
            "puc": "1st PUC",
            "weight_pct_range": (2, 3),
            "expected_q": (1, 2),
            "avg_weight": 2.5,
            "aliases": ["body fluids and circulation", "blood", "heart", "ecg"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Living World / Biological Classification",
            "puc": "1st PUC",
            "weight_pct_range": (2, 3),
            "expected_q": (1, 2),
            "avg_weight": 2.5,
            "aliases": ["the living world", "living world", "biological classification", "monera", "protista", "fungi"],
            "primary_subtype": "fact_reaction",
        },
        # ── 2nd PUC ──
        {
            "name": "Human Reproduction / Reproduction in Organisms",
            "puc": "2nd PUC",
            "weight_pct_range": (6, 7),
            "expected_q": (4, 4),
            "avg_weight": 6.5,
            "aliases": ["human reproduction", "reproduction in organisms", "reproductive health", "spermatogenesis", "menstrual cycle"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Genetics and Evolution",
            "puc": "2nd PUC",
            "weight_pct_range": (7, 8),
            "expected_q": (4, 5),
            "avg_weight": 7.5,
            "aliases": ["principles of inheritance and variation", "genetics and evolution", "evolution", "mendelian genetics"],
            "primary_subtype": "concept_application",
        },
        {
            "name": "Biotechnology: Principles & Processes + Applications",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["biotechnology : principles and processes", "biotechnology - principles and processes", "biotechnology and its applications", "pcr", "recombinant dna"],
            "primary_subtype": "theory_definition",
        },
        {
            "name": "Ecology and Environment / Ecosystem / Biodiversity & Conservation",
            "puc": "2nd PUC",
            "weight_pct_range": (5, 6),
            "expected_q": (3, 4),
            "avg_weight": 5.5,
            "aliases": ["organisms and populations", "ecosystem", "biodiversity and conservation", "environmental issues", "ecology"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Chemical Coordination and Integration",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["chemical coordination and integration", "endocrine glands", "hormones", "pituitary"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Animal Kingdom / Structural Organisation in Animals",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 5),
            "expected_q": (2, 3),
            "avg_weight": 4.5,
            "aliases": ["animal kingdom", "structural organisation in animals", "chordata", "arthropoda"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Microbes in Human Welfare",
            "puc": "2nd PUC",
            "weight_pct_range": (3, 4),
            "expected_q": (2, 2),
            "avg_weight": 3.5,
            "aliases": ["microbes in human welfare", "antibiotics", "biogas", "fermentation"],
            "primary_subtype": "fact_reaction",
        },
        {
            "name": "Molecular Basis of Inheritance",
            "puc": "2nd PUC",
            "weight_pct_range": (4, 4),
            "expected_q": (2, 3),
            "avg_weight": 4.0,
            "aliases": ["molecular basis of inheritance", "dna replication", "transcription", "translation", "genetic code"],
            "primary_subtype": "concept_application",
        },
        {
            "name": "Strategies for Enhancement in Food Production",
            "puc": "2nd PUC",
            "weight_pct_range": (3, 3),
            "expected_q": (1, 2),
            "avg_weight": 3.0,
            "aliases": ["strategies for enhancement in food production", "plant breeding", "animal husbandry", "tissue culture"],
            "primary_subtype": "fact_reaction",
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. Subject Question Subtype Distribution Targets (Percentages out of 100)
# ─────────────────────────────────────────────────────────────────────────────

SUBJECT_SUBTYPE_TARGETS: Dict[str, Dict[str, float]] = {
    # Physics: 50% to 60% calculations total
    # Direct formula: ~35% (30-40%), Multi-step: ~18% (15-20%), Theory/definition: ~47% (40-50%)
    "Physics": {
        "direct_formula": 35.0,      # ~21 out of 60 Qs (35%)
        "multi_step": 18.33,         # ~11 out of 60 Qs (18.33%) -> Total calc: 53.33% (~32 Qs)
        "theory_definition": 46.67,  # ~28 out of 60 Qs (46.67%)
    },
    # Chemistry: 10% to 15% calculations total
    # Physical numericals: ~10% (5-8 Qs / 8-12%), Reactions & facts: ~60%, Theory/definitions: ~30%
    "Chemistry": {
        "physical_numerical": 10.0,  # ~6 out of 60 Qs (10%)
        "fact_reaction": 60.0,       # ~36 out of 60 Qs (60%)
        "theory_definition": 30.0,   # ~18 out of 60 Qs (30%)
    },
    # Mathematics: Problem solving & formula execution
    "Mathematics": {
        "direct_formula": 40.0,      # ~24 out of 60 Qs (40%)
        "multi_step": 36.67,         # ~22 out of 60 Qs (36.67%)
        "concept_application": 23.33,# ~14 out of 60 Qs (23.33%)
    },
    # Biology: Fact-heavy, memory, and conceptual physiology
    "Biology": {
        "fact_reaction": 60.0,       # ~36 out of 60 Qs (60%)
        "theory_definition": 25.0,   # ~15 out of 60 Qs (25%)
        "concept_application": 15.0, # ~9 out of 60 Qs (15%)
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. Largest Remainder Allocation Helper (Hare-Niemeyer Method)
# ─────────────────────────────────────────────────────────────────────────────

def _largest_remainder_allocation(weights: Dict[str, float], total_items: int) -> Dict[str, int]:
    """Apportion an exact integer number of items (e.g. 60 questions) across categories
    in strict proportion to their weights, ensuring the sum equals total_items without drift.
    """
    total_weight = sum(weights.values())
    if total_weight <= 0:
        count = len(weights)
        if count == 0:
            return {}
        base = total_items // count
        rem = total_items % count
        res = {k: base for k in weights}
        for i, k in enumerate(weights.keys()):
            if i < rem:
                res[k] += 1
        return res

    quotas: Dict[str, float] = {}
    floors: Dict[str, int] = {}
    remainders: List[Tuple[float, str]] = []

    for key, w in weights.items():
        q = (w / total_weight) * total_items
        quotas[key] = q
        fl = int(math.floor(q))
        floors[key] = fl
        remainders.append((q - fl, key))

    allocated = sum(floors.values())
    deficit = total_items - allocated

    # Sort descending by remainder
    remainders.sort(key=lambda x: x[0], reverse=True)
    for i in range(min(deficit, len(remainders))):
        floors[remainders[i][1]] += 1

    return floors


# ─────────────────────────────────────────────────────────────────────────────
# 4. Quota Calculation API
# ─────────────────────────────────────────────────────────────────────────────

def get_blueprint_chapter_info(subject: str, topic_name: str) -> Optional[Dict[str, Any]]:
    """Match a topic or chapter string to its official KCET blueprint definition."""
    chapters = KCET_BLUEPRINT_2026.get(subject, [])
    if not chapters or not topic_name:
        return None

    top_clean = topic_name.strip().lower()

    # Exact name match
    for ch in chapters:
        if ch["name"].lower() == top_clean:
            return ch

    # Alias matching
    for ch in chapters:
        for alias in ch.get("aliases", []):
            if alias in top_clean or top_clean in alias:
                return ch

    # Word overlap fallback
    words = set(top_clean.replace("-", " ").replace("_", " ").split())
    best_match = None
    best_score = 0
    for ch in chapters:
        ch_words = set(ch["name"].lower().replace("-", " ").replace("_", " ").split())
        score = len(words.intersection(ch_words))
        if score > best_score:
            best_score = score
            best_match = ch

    return best_match if best_score >= 1 else None


def calculate_chapter_quotas(
    subject: str,
    uploaded_topics: Optional[List[str]] = None,
    total_questions: int = 60
) -> Dict[str, int]:
    """Calculate the exact number of questions each chapter should contribute to a mock exam.
    
    If uploaded_topics is specified:
        Apportions the 60 questions strictly among ONLY the uploaded topics, scaling their
        official relative blueprint importance.
    If uploaded_topics is empty / None:
        Allocates across the full official syllabus matching the 2026 expected question distributions.
    """
    chapters = KCET_BLUEPRINT_2026.get(subject, [])
    if not chapters:
        return {}

    if uploaded_topics and len(uploaded_topics) > 0:
        # User uploaded specific chapters -> filter strictly to these topics
        weights_map: Dict[str, float] = {}
        for top in uploaded_topics:
            info = get_blueprint_chapter_info(subject, top)
            w = info["avg_weight"] if info else 5.0
            weights_map[top] = w
        return _largest_remainder_allocation(weights_map, total_questions)

    # Full syllabus mode
    weights_map = {ch["name"]: ch["avg_weight"] for ch in chapters}
    return _largest_remainder_allocation(weights_map, total_questions)


def calculate_subtype_quotas(subject: str, total_questions: int = 60) -> Dict[str, int]:
    """Calculate the target count for each question subtype (e.g. calculation vs. theory)."""
    targets = SUBJECT_SUBTYPE_TARGETS.get(subject, {
        "direct_formula": 40.0,
        "multi_step": 30.0,
        "theory_definition": 30.0,
    })
    return _largest_remainder_allocation(targets, total_questions)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Blueprint Question Sampling Algorithm
# ─────────────────────────────────────────────────────────────────────────────

def allocate_blueprint_questions(
    available_questions: List[Any],
    subject: str,
    uploaded_topics: Optional[List[str]] = None,
    total_questions: int = 60
) -> List[Any]:
    """Sample exactly total_questions from available_questions to satisfy both:
    1. Chapter weightage quotas (proportional to official KCET importance).
    2. Calculation vs. Theory subtype quotas (e.g. 50-60% calculation for Physics, 10-15% for Chemistry).
    """
    if len(available_questions) <= total_questions:
        return list(available_questions)

    from .topic_matcher import is_topic_matching
    from .mcq_extractor import infer_question_subtype

    # Step 1: Compute target chapter quotas
    chapter_quotas = calculate_chapter_quotas(subject, uploaded_topics, total_questions)
    subtype_quotas = calculate_subtype_quotas(subject, total_questions)

    logger.info(
        "Allocating %d questions for %s. Chapter quotas: %s, Subtype quotas: %s",
        total_questions,
        subject,
        chapter_quotas,
        subtype_quotas,
    )

    # Step 2: Bucket available questions by (topic, subtype)
    # Map each question to its closest chapter quota key
    questions_by_topic: Dict[str, List[Any]] = {}
    for q in available_questions:
        q_topic = getattr(q, "topic", "") or ""
        assigned_topic = None
        for ch_key in chapter_quotas.keys():
            if is_topic_matching(q_topic, [ch_key]):
                assigned_topic = ch_key
                break
        if not assigned_topic:
            # Check blueprint aliases
            for ch_key in chapter_quotas.keys():
                info = get_blueprint_chapter_info(subject, ch_key)
                if info and any(a in q_topic.lower() for a in info.get("aliases", [])):
                    assigned_topic = ch_key
                    break
        if not assigned_topic:
            assigned_topic = list(chapter_quotas.keys())[0] if chapter_quotas else "General"

        questions_by_topic.setdefault(assigned_topic, []).append(q)

    # Shuffle each bucket
    for top_list in questions_by_topic.values():
        random.shuffle(top_list)

    # Step 3: Draw questions per chapter matching the subtype targets
    selected_questions: List[Any] = []
    selected_ids = set()
    subtype_counts: Dict[str, int] = {st: 0 for st in subtype_quotas.keys()}

    for topic_key, target_count in chapter_quotas.items():
        pool = questions_by_topic.get(topic_key, [])
        picked_for_topic = []

        # Try to pick questions prioritizing subtypes that still have quota deficits
        for q in list(pool):
            if len(picked_for_topic) >= target_count:
                break
            q_id = getattr(q, "id", None) or id(q)
            if q_id in selected_ids:
                continue

            q_text = getattr(q, "question_text", "") or getattr(q, "q", "")
            q_opts = getattr(q, "options", []) or getattr(q, "opts", [])
            q_subtype = getattr(q, "subtype", None) or infer_question_subtype(q_text, q_opts, subject)

            # Check if this subtype still needs quota
            if subtype_counts.get(q_subtype, 0) < subtype_quotas.get(q_subtype, 0):
                picked_for_topic.append(q)
                selected_ids.add(q_id)
                subtype_counts[q_subtype] = subtype_counts.get(q_subtype, 0) + 1
                pool.remove(q)

        # If chapter target not yet satisfied, fill from remaining pool respecting subtype ceilings
        for q in list(pool):
            if len(picked_for_topic) >= target_count:
                break
            q_id = getattr(q, "id", None) or id(q)
            if q_id in selected_ids:
                continue

            q_text = getattr(q, "question_text", "") or getattr(q, "q", "")
            q_opts = getattr(q, "options", []) or getattr(q, "opts", [])
            q_subtype = getattr(q, "subtype", None) or infer_question_subtype(q_text, q_opts, subject)

            # Chemistry guard: numericals must strictly remain within 5 to 8 questions (8% to 12%)
            if "chem" in subject.lower() and q_subtype == "physical_numerical" and subtype_counts.get("physical_numerical", 0) >= 7:
                continue

            # Physics guard: calculations must strictly remain <= 34 (~53-56%)
            if "physic" in subject.lower() and q_subtype in ("direct_formula", "multi_step"):
                curr_calc = subtype_counts.get("direct_formula", 0) + subtype_counts.get("multi_step", 0)
                if curr_calc >= 34:
                    continue

            picked_for_topic.append(q)
            selected_ids.add(q_id)
            subtype_counts[q_subtype] = subtype_counts.get(q_subtype, 0) + 1
            pool.remove(q)

        # Fallback if pool items were skipped due to ceiling but count still needed
        for q in list(pool):
            if len(picked_for_topic) >= target_count:
                break
            q_id = getattr(q, "id", None) or id(q)
            if q_id in selected_ids:
                continue
            q_text = getattr(q, "question_text", "") or getattr(q, "q", "")
            q_opts = getattr(q, "options", []) or getattr(q, "opts", [])
            q_subtype = getattr(q, "subtype", None) or infer_question_subtype(q_text, q_opts, subject)

            if "chem" in subject.lower() and q_subtype == "physical_numerical" and subtype_counts.get("physical_numerical", 0) >= 8:
                continue
            if "physic" in subject.lower() and q_subtype in ("direct_formula", "multi_step"):
                curr_calc = subtype_counts.get("direct_formula", 0) + subtype_counts.get("multi_step", 0)
                if curr_calc >= 36:
                    continue

            picked_for_topic.append(q)
            selected_ids.add(q_id)
            subtype_counts[q_subtype] = subtype_counts.get(q_subtype, 0) + 1
            pool.remove(q)

        selected_questions.extend(picked_for_topic)

    # Step 4: Backfill any shortfall to guarantee exactly total_questions
    if len(selected_questions) < total_questions:
        remaining_pool = [q for q in available_questions if (getattr(q, "id", None) or id(q)) not in selected_ids]
        random.shuffle(remaining_pool)
        
        # Sort remaining pool to prioritize subtypes that are still below their target
        def _backfill_priority(item):
            t_text = getattr(item, "question_text", "") or getattr(item, "q", "")
            t_opts = getattr(item, "options", []) or getattr(item, "opts", [])
            st = getattr(item, "subtype", None) or infer_question_subtype(t_text, t_opts, subject)
            target_st = subtype_quotas.get(st, 0)
            curr_st = subtype_counts.get(st, 0)
            return target_st - curr_st

        remaining_pool.sort(key=_backfill_priority, reverse=True)

        for q in list(remaining_pool):
            if len(selected_questions) >= total_questions:
                break
            q_text = getattr(q, "question_text", "") or getattr(q, "q", "")
            q_opts = getattr(q, "options", []) or getattr(q, "opts", [])
            q_subtype = getattr(q, "subtype", None) or infer_question_subtype(q_text, q_opts, subject)

            if "chem" in subject.lower() and q_subtype == "physical_numerical" and subtype_counts.get("physical_numerical", 0) >= 7:
                continue
            if "physic" in subject.lower() and q_subtype in ("direct_formula", "multi_step"):
                curr_calc = subtype_counts.get("direct_formula", 0) + subtype_counts.get("multi_step", 0)
                if curr_calc >= 34:
                    continue

            selected_questions.append(q)
            selected_ids.add(getattr(q, "id", None) or id(q))
            subtype_counts[q_subtype] = subtype_counts.get(q_subtype, 0) + 1
            remaining_pool.remove(q)

        for q in remaining_pool:
            if len(selected_questions) >= total_questions:
                break
            selected_questions.append(q)
            selected_ids.add(getattr(q, "id", None) or id(q))

    # In case of slight overflow, truncate
    selected_questions = selected_questions[:total_questions]

    # Step 5: Final Subtype Target Reconciliation
    # Enforces strict user-defined bounds across all subjects
    if "chem" in subject.lower():
        # Ensure strictly 5 to 8 physical numericals (~8% to 12% of 60)
        curr_num = sum(1 for q in selected_questions if (getattr(q, "subtype", None) or infer_question_subtype(getattr(q, "question_text", "") or getattr(q, "q", ""), getattr(q, "options", []) or getattr(q, "opts", []), subject)) == "physical_numerical")
        if curr_num < 5:
            candidate_numericals = [
                q for q in available_questions
                if (getattr(q, "id", None) or id(q)) not in selected_ids
                and (getattr(q, "subtype", None) or infer_question_subtype(getattr(q, "question_text", "") or getattr(q, "q", ""), getattr(q, "options", []) or getattr(q, "opts", []), subject)) == "physical_numerical"
            ]
            for cand in candidate_numericals:
                if curr_num >= 6:
                    break
                for i, sq in enumerate(selected_questions):
                    sq_sub = getattr(sq, "subtype", None) or infer_question_subtype(getattr(sq, "question_text", "") or getattr(sq, "q", ""), getattr(sq, "options", []) or getattr(sq, "opts", []), subject)
                    if sq_sub in ("theory_definition", "fact_reaction"):
                        selected_ids.discard(getattr(sq, "id", None) or id(sq))
                        selected_questions[i] = cand
                        selected_ids.add(getattr(cand, "id", None) or id(cand))
                        setattr(cand, "subtype", "physical_numerical")
                        curr_num += 1
                        break
        elif curr_num > 8:
            candidate_theory = [
                q for q in available_questions
                if (getattr(q, "id", None) or id(q)) not in selected_ids
                and (getattr(q, "subtype", None) or infer_question_subtype(getattr(q, "question_text", "") or getattr(q, "q", ""), getattr(q, "options", []) or getattr(q, "opts", []), subject)) in ("theory_definition", "fact_reaction")
            ]
            for cand in candidate_theory:
                if curr_num <= 7:
                    break
                for i, sq in enumerate(selected_questions):
                    sq_sub = getattr(sq, "subtype", None) or infer_question_subtype(getattr(sq, "question_text", "") or getattr(sq, "q", ""), getattr(sq, "options", []) or getattr(sq, "opts", []), subject)
                    if sq_sub == "physical_numerical":
                        selected_ids.discard(getattr(sq, "id", None) or id(sq))
                        selected_questions[i] = cand
                        selected_ids.add(getattr(cand, "id", None) or id(cand))
                        curr_num -= 1
                        break

    elif "physic" in subject.lower():
        # Ensure strictly 50% to 60% calculations (30 to 36 questions out of 60)
        def is_calc(q):
            st = getattr(q, "subtype", None) or infer_question_subtype(getattr(q, "question_text", "") or getattr(q, "q", ""), getattr(q, "options", []) or getattr(q, "opts", []), subject)
            return st in ("direct_formula", "multi_step")
        
        curr_calc = sum(1 for q in selected_questions if is_calc(q))
        if curr_calc < 30:
            candidate_calcs = [
                q for q in available_questions
                if (getattr(q, "id", None) or id(q)) not in selected_ids and is_calc(q)
            ]
            for cand in candidate_calcs:
                if curr_calc >= 32:
                    break
                for i, sq in enumerate(selected_questions):
                    if not is_calc(sq):
                        selected_ids.discard(getattr(sq, "id", None) or id(sq))
                        selected_questions[i] = cand
                        selected_ids.add(getattr(cand, "id", None) or id(cand))
                        curr_calc += 1
                        break
        elif curr_calc > 36:
            candidate_theories = [
                q for q in available_questions
                if (getattr(q, "id", None) or id(q)) not in selected_ids and not is_calc(q)
            ]
            for cand in candidate_theories:
                if curr_calc <= 34:
                    break
                for i, sq in enumerate(selected_questions):
                    if is_calc(sq):
                        selected_ids.discard(getattr(sq, "id", None) or id(sq))
                        selected_questions[i] = cand
                        selected_ids.add(getattr(cand, "id", None) or id(cand))
                        curr_calc -= 1
                        break

    # Natural interleave shuffle
    random.shuffle(selected_questions)

    logger.info(
        "Successfully selected %d questions following KCET 2026 blueprint (Subtypes achieved: %s)",
        len(selected_questions),
        subtype_counts,
    )
    return selected_questions
