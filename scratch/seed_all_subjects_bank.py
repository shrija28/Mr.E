"""Seed clean, high-quality, authentic KCET Question Banks for ALL 4 Subjects:
Physics, Chemistry, Mathematics, and Biology.
Wipes out all previous corrupted, OMR, and pseudo fallback questions.
"""

import sys
import json
import sqlite3
import uuid
from pathlib import Path

sys.path.insert(0, 'backend')

db_path = Path("backend/smartkcet.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Purging ALL existing questions from database...")
c.execute("DELETE FROM questions")
conn.commit()

# --- QUESTION BANKS FOR ALL 4 SUBJECTS ---

CHEMISTRY_QUESTIONS = [
    {
        "q": "What is the mass percentage of carbon in carbon dioxide (CO₂)? (Molar mass of C = 12 g/mol, O = 16 g/mol)",
        "opts": ["12.00%", "27.27%", "72.73%", "33.33%"],
        "ans": 1,
        "topic": "Some Basic Concepts of Chemistry",
        "exp": "Molar mass of CO₂ = 12 + 2(16) = 44 g/mol. Mass % of C = (12 / 44) * 100 = 27.27%."
    },
    {
        "q": "How many moles of O₂ are required to react completely with 4 moles of CH₄ in the reaction: CH₄ + 2O₂ → CO₂ + 2H₂O?",
        "opts": ["2 moles", "4 moles", "6 moles", "8 moles"],
        "ans": 3,
        "topic": "Some Basic Concepts of Chemistry",
        "exp": "Stoichiometric ratio CH₄ : O₂ = 1 : 2. For 4 moles of CH₄, O₂ needed = 4 * 2 = 8 moles."
    },
    {
        "q": "The wavelength of a spectral line emitted when an electron in a hydrogen atom transitions from n = 3 to n = 2 belongs to:",
        "opts": ["Lyman series", "Balmer series", "Paschen series", "Brackett series"],
        "ans": 1,
        "topic": "Structure of Atom",
        "exp": "Transitions ending at n = 2 correspond to the Balmer series, which lies in the visible spectrum."
    },
    {
        "q": "The maximum number of electrons that can be accommodated in a subshell with azimuthal quantum number l = 2 (d-subshell) is:",
        "opts": ["2", "6", "10", "14"],
        "ans": 2,
        "topic": "Structure of Atom",
        "exp": "Number of electrons in a subshell = 2(2l + 1). For l = 2: 2(2*2 + 1) = 2(5) = 10 electrons."
    },
    {
        "q": "Which of the following species has a square planar geometry according to VSEPR theory?",
        "opts": ["CH₄", "SF₄", "XeF₄", "NH₄⁺"],
        "ans": 2,
        "topic": "Chemical Bonding and Molecular Structure",
        "exp": "XeF₄ has 4 bond pairs and 2 lone pairs on Xe (sp³d² hybridization), giving a square planar shape."
    },
    {
        "q": "The bond order of O₂⁺ ion (15 electrons) according to Molecular Orbital Theory is:",
        "opts": ["1.5", "2.0", "2.5", "3.0"],
        "ans": 2,
        "topic": "Chemical Bonding and Molecular Structure",
        "exp": "Bond Order = 0.5 * (N_b - N_a) = 0.5 * (10 - 5) = 2.5."
    },
    {
        "q": "For a reaction, ΔH = +40 kJ/mol and ΔS = +100 J/(K·mol). The minimum temperature above which the reaction becomes spontaneous is:",
        "opts": ["273 K", "300 K", "400 K", "500 K"],
        "ans": 2,
        "topic": "Thermodynamics",
        "exp": "For spontaneity ΔG = ΔH - T ΔS < 0 => T > ΔH / ΔS = (40,000 J/mol) / (100 J/K·mol) = 400 K."
    },
    {
        "q": "What is the pH of a 1.0 × 10⁻³ M solution of hydrochloric acid (HCl) at 25°C?",
        "opts": ["1.0", "2.0", "3.0", "11.0"],
        "ans": 2,
        "topic": "Equilibrium",
        "exp": "HCl is a strong acid: [H⁺] = 1.0 × 10⁻³ M. pH = -log₁₀[H⁺] = -log₁₀(10⁻³) = 3.0."
    },
    {
        "q": "For the gaseous reaction N₂(g) + 3H₂(g) ⇌ 2NH₃(g), the relation between K_p and K_c is:",
        "opts": ["K_p = K_c (RT)⁻²", "K_p = K_c (RT)⁰", "K_p = K_c (RT)¹", "K_p = K_c (RT)²"],
        "ans": 0,
        "topic": "Equilibrium",
        "exp": "Δn_g = moles of gaseous products - moles of gaseous reactants = 2 - (1 + 3) = -2. Thus K_p = K_c (RT)⁻²."
    },
    {
        "q": "The standard electrode potentials of Zn²⁺/Zn and Cu²⁺/Cu are -0.76 V and +0.34 V respectively. The standard EMF of the cell Zn | Zn²⁺ || Cu²⁺ | Cu is:",
        "opts": ["+0.42 V", "+1.10 V", "-1.10 V", "+0.76 V"],
        "ans": 1,
        "topic": "Electrochemistry",
        "exp": "E°_cell = E°_cathode - E°_anode = E°(Cu²⁺/Cu) - E°(Zn²⁺/Zn) = 0.34 - (-0.76) = +1.10 V."
    },
    {
        "q": "How many Coulombs of electricity are required to deposit 10.8 g of Silver (Ag, molar mass 108 g/mol) from AgNO₃ solution? (F = 96500 C/mol)",
        "opts": ["965 C", "9650 C", "48250 C", "96500 C"],
        "ans": 1,
        "topic": "Electrochemistry",
        "exp": "Moles of Ag = 10.8 / 108 = 0.1 mol. Ag⁺ + e⁻ → Ag requires 0.1 mol of e⁻ = 0.1 × 96500 = 9650 C."
    },
    {
        "q": "The rate constant of a first-order reaction is 6.93 × 10⁻³ min⁻¹. Its half-life period (t_1/2) is:",
        "opts": ["10 min", "50 min", "100 min", "200 min"],
        "ans": 2,
        "topic": "Chemical Kinetics",
        "exp": "For a first order reaction, t_1/2 = 0.693 / k = 0.693 / (6.93 × 10⁻³) = 100 min."
    },
    {
        "q": "The osmotic pressure of a solution containing 6 g of urea (molar mass = 60 g/mol) in 1 L solution at 300 K is (R = 0.0821 L·atm/(K·mol)):",
        "opts": ["1.23 atm", "2.46 atm", "4.92 atm", "9.84 atm"],
        "ans": 1,
        "topic": "Solutions",
        "exp": "Molarity C = (6/60) / 1 = 0.1 M. Osmotic pressure π = C R T = (0.1) × (0.0821) × (300) = 2.463 atm."
    },
    {
        "q": "Reimer-Tiemann reaction of phenol with chloroform in the presence of aqueous NaOH introduces which functional group into the benzene ring?",
        "opts": ["-COOH at ortho position", "-CHO at ortho position", "-NO₂ at para position", "-CH₃ at para position"],
        "ans": 1,
        "topic": "Alcohols, Phenols and Ethers",
        "exp": "Reimer-Tiemann reaction converts phenol to salicylaldehyde by introducing an aldehyde group (-CHO) at the ortho position."
    },
    {
        "q": "Which of the following organic compounds gives a positive Iodoform test (yellow precipitate of CHI₃ on warming with I₂ and NaOH)?",
        "opts": ["Methanol (CH₃OH)", "Ethanol (CH₃CH₂OH)", "Benzaldehyde (C₆H₅CHO)", "Propan-1-ol"],
        "ans": 1,
        "topic": "Aldehydes, Ketones and Carboxylic Acids",
        "exp": "Ethanol contains the CH₃CH(OH)- group which oxidizes to CH₃CHO and yields iodoform (CHI₃)."
    },
    {
        "q": "Primary aliphatic or aromatic amines when warmed with chloroform and ethanolic KOH produce foul-smelling compounds called:",
        "opts": ["Nitrites", "Isocyanides (Carbylamines)", "Cyanides", "Amides"],
        "ans": 1,
        "topic": "Amines",
        "exp": "This is the Carbylamine test: R-NH₂ + CHCl₃ + 3KOH → R-NC (Isocyanide) + 3KCl + 3H₂O."
    },
    {
        "q": "Nitration of benzene using a mixture of concentrated HNO₃ and concentrated H₂SO₄ involves which electrophile?",
        "opts": ["NO⁺", "NO₂⁺ (Nitronium ion)", "NO₃⁻", "HNO₂"],
        "ans": 1,
        "topic": "Hydrocarbons",
        "exp": "Concentrated H₂SO₄ protonates HNO₃, generating the nitronium ion (NO₂⁺) as the reactive electrophile."
    },
    {
        "q": "The oxidation number of Chromium (Cr) in potassium dichromate (K₂Cr₂O₇) is:",
        "opts": ["+3", "+4", "+5", "+6"],
        "ans": 3,
        "topic": "Redox Reactions",
        "exp": "2(+1) + 2(x) + 7(-2) = 0 => 2 + 2x - 14 = 0 => 2x = 12 => x = +6."
    },
    {
        "q": "Which of the following p-block elements shows anomalous behavior due to small size, high electronegativity, and absence of d-orbitals?",
        "opts": ["Nitrogen", "Phosphorus", "Arsenic", "Antimony"],
        "ans": 0,
        "topic": "The p-Block Elements",
        "exp": "Nitrogen differs significantly from other group 15 elements due to small size, high electronegativity, pπ-pπ multiple bonding, and lack of d-orbitals."
    },
    {
        "q": "The monomer units of Nylon-6,6 are hexamethylenediamine and:",
        "opts": ["Terephthalic acid", "Adipic acid", "Ethylene glycol", "Caprolactam"],
        "ans": 1,
        "topic": "Polymers",
        "exp": "Nylon-6,6 is a condensation polymer formed by hexamethylenediamine and adipic acid (hexanedioic acid)."
    }
]

MATHEMATICS_QUESTIONS = [
    {
        "q": "The domain of the real-valued function f(x) = sin⁻¹(2x - 1) is:",
        "opts": ["[-1, 1]", "[0, 1]", "[-1/2, 1/2]", "(0, 1)"],
        "ans": 1,
        "topic": "Inverse Trigonometric Functions",
        "exp": "-1 ≤ 2x - 1 ≤ 1 => 0 ≤ 2x ≤ 2 => 0 ≤ x ≤ 1. Domain is [0, 1]."
    },
    {
        "q": "The principal value of tan⁻¹(1) + cos⁻¹(-1/2) + sin⁻¹(-1/2) is equal to:",
        "opts": ["π/4", "π/2", "3π/4", "π"],
        "ans": 2,
        "topic": "Inverse Trigonometric Functions",
        "exp": "tan⁻¹(1) = π/4, cos⁻¹(-1/2) = 2π/3, sin⁻¹(-1/2) = -π/6. Sum = π/4 + 2π/3 - π/6 = (3π + 8π - 2π)/12 = 9π/12 = 3π/4."
    },
    {
        "q": "If matrix A = [[2, 3], [1, 4]], then the determinant of A⁻¹ (|A⁻¹|) is:",
        "opts": ["1/5", "1/8", "5", "8"],
        "ans": 0,
        "topic": "Matrices and Determinants",
        "exp": "|A| = (2*4 - 3*1) = 8 - 3 = 5. |A⁻¹| = 1 / |A| = 1/5."
    },
    {
        "q": "If A is a non-singular square matrix of order 3 with determinant |A| = 4, then the determinant of its adjoint |adj(A)| is:",
        "opts": ["4", "12", "16", "64"],
        "ans": 2,
        "topic": "Determinants",
        "exp": "For a matrix of order n, |adj(A)| = |A|^(n-1). Here n = 3, so |adj(A)| = 4^(3-1) = 4² = 16."
    },
    {
        "q": "If y = e^(sin(x²)), then the derivative dy/dx at x = 0 is:",
        "opts": ["0", "1", "e", "2"],
        "ans": 0,
        "topic": "Continuity and Differentiability",
        "exp": "dy/dx = e^(sin(x²)) * cos(x²) * (2x). At x = 0: dy/dx = e⁰ * cos(0) * 0 = 0."
    },
    {
        "q": "The derivative of tan⁻¹[sin x / (1 + cos x)] with respect to x is:",
        "opts": ["1/2", "1", "2", "-1/2"],
        "ans": 0,
        "topic": "Continuity and Differentiability",
        "exp": "sin x / (1 + cos x) = tan(x/2). So tan⁻¹[tan(x/2)] = x/2. Derivative with respect to x is 1/2."
    },
    {
        "q": "The value of the indefinite integral ∫ [1 / (x (x² + 1))] dx is:",
        "opts": ["ln|x| - 0.5 ln|x² + 1| + C", "0.5 ln|x| - ln|x² + 1| + C", "ln|x² + 1| + C", "tan⁻¹(x) + C"],
        "ans": 0,
        "topic": "Integrals",
        "exp": "Multiply numerator and denominator by x: ∫ [x / (x²(x² + 1))] dx. Let u = x², du = 2x dx => 0.5 ∫ [1 / (u(u+1))] du = 0.5 [ln|u| - ln|u+1|] = ln|x| - 0.5 ln|x² + 1| + C."
    },
    {
        "q": "The area of the region bounded by the parabola y² = 4x and the straight line y = 2x is:",
        "opts": ["1/6 sq units", "1/3 sq units", "1/2 sq units", "2/3 sq units"],
        "ans": 1,
        "topic": "Application of Integrals",
        "exp": "Intersection points: (2x)² = 4x => 4x² = 4x => x = 0, 1. Area = ∫₀¹ [2√x - 2x] dx = [ (4/3) x^(3/2) - x² ]₀¹ = 4/3 - 1 = 1/3 sq units."
    },
    {
        "q": "The degree of the differential equation (d²y/dx²)³ + (dy/dx)⁴ + y = 0 is:",
        "opts": ["1", "2", "3", "4"],
        "ans": 2,
        "topic": "Differential Equations",
        "exp": "Order of the differential equation is 2 (highest derivative d²y/dx²). Degree is the power of the highest derivative = 3."
    },
    {
        "q": "The integrating factor (I.F.) of the linear differential equation dy/dx + (2/x) y = x³ is:",
        "opts": ["x", "x²", "ln x", "e^x"],
        "ans": 1,
        "topic": "Differential Equations",
        "exp": "P(x) = 2/x. I.F. = e^(∫ P dx) = e^(∫ (2/x) dx) = e^(2 ln x) = e^(ln x²) = x²."
    },
    {
        "q": "If vector a = 2i + j + 3k and vector b = 3i + 5j - k, then the dot product a · b is equal to:",
        "opts": ["5", "8", "11", "14"],
        "ans": 1,
        "topic": "Vector Algebra",
        "exp": "a · b = (2*3) + (1*5) + (3*-1) = 6 + 5 - 3 = 8."
    },
    {
        "q": "The angle between two vectors a and b having magnitudes √3 and 2 respectively, with dot product a · b = √6, is:",
        "opts": ["π/6", "π/4", "π/3", "π/2"],
        "ans": 1,
        "topic": "Vector Algebra",
        "exp": "cos θ = (a · b) / (|a| |b|) = √6 / (√3 * 2) = √2 / 2 = 1/√2 => θ = π/4."
    },
    {
        "q": "If P(A) = 0.6, P(B) = 0.3, and P(A ∩ B) = 0.2, then the conditional probability P(A | B) is:",
        "opts": ["1/3", "1/2", "2/3", "3/4"],
        "ans": 2,
        "topic": "Probability",
        "exp": "P(A | B) = P(A ∩ B) / P(B) = 0.2 / 0.3 = 2/3."
    },
    {
        "q": "If A and B are two independent events such that P(A) = 0.4 and P(B) = 0.5, then P(A ∪ B) is equal to:",
        "opts": ["0.2", "0.7", "0.9", "0.6"],
        "ans": 1,
        "topic": "Probability",
        "exp": "For independent events P(A ∩ B) = P(A) * P(B) = 0.4 * 0.5 = 0.2. P(A ∪ B) = P(A) + P(B) - P(A ∩ B) = 0.4 + 0.5 - 0.2 = 0.7."
    },
    {
        "q": "If the binary operation * on R is defined by a * b = a + b + a b, then the identity element in R is:",
        "opts": ["-1", "0", "1", "2"],
        "ans": 1,
        "topic": "Relations and Functions",
        "exp": "a * e = a => a + e + a e = a => e(1 + a) = 0 => e = 0."
    },
    {
        "q": "If a line makes angles 90°, 60°, and 30° with x, y, and z axes respectively, its direction cosines are:",
        "opts": ["(0, 1/2, √3/2)", "(1, 0, 0)", "(0, √3/2, 1/2)", "(1/2, 1/2, 1/2)"],
        "ans": 0,
        "topic": "Three Dimensional Geometry",
        "exp": "l = cos(90°) = 0, m = cos(60°) = 1/2, n = cos(30°) = √3/2."
    },
    {
        "q": "The distance between the parallel planes 2x - y + 2z = 4 and 4x - 2y + 4z = 10 is:",
        "opts": ["1/3", "2/3", "1", "2"],
        "ans": 0,
        "topic": "Three Dimensional Geometry",
        "exp": "Rewrite second plane as 2x - y + 2z = 5. Distance d = |d₂ - d₁| / √(a² + b² + c²) = |5 - 4| / √(2² + (-1)² + 2²) = 1 / √9 = 1/3."
    },
    {
        "q": "The maximum value of Z = 3x + 4y subject to constraints x + y ≤ 4, x ≥ 0, y ≥ 0 is:",
        "opts": ["12", "16", "18", "24"],
        "ans": 1,
        "topic": "Linear Programming",
        "exp": "Corner points of feasible region: (0,0), (4,0), (0,4). Z(0,0)=0, Z(4,0)=12, Z(0,4)=16. Max value = 16."
    },
    {
        "q": "If the mean and variance of a Binomial distribution are 4 and 2 respectively, the number of trials n is:",
        "opts": ["4", "6", "8", "10"],
        "ans": 2,
        "topic": "Probability",
        "exp": "Mean = n p = 4, Variance = n p q = 2 => q = 2/4 = 0.5 => p = 0.5. n (0.5) = 4 => n = 8."
    },
    {
        "q": "The limit lim (x → 0) [sin(5x) / (3x)] is equal to:",
        "opts": ["1", "3/5", "5/3", "15"],
        "ans": 2,
        "topic": "Limits and Derivatives",
        "exp": "lim (x → 0) [sin(5x) / (5x)] * (5/3) = 1 * (5/3) = 5/3."
    }
]

BIOLOGY_QUESTIONS = [
    {
        "q": "In R.H. Whittaker's Five Kingdom Classification, Kingdom Monera exclusively includes:",
        "opts": ["Unicellular eukaryotes", "Prokaryotic organisms like Bacteria and Cyanobacteria", "Multicellular fungi", "Acellular viruses"],
        "ans": 1,
        "topic": "Biological Classification",
        "exp": "Kingdom Monera comprises all prokaryotic unicellular organisms lacking a membrane-bound nucleus, such as eubacteria and archaebacteria."
    },
    {
        "q": "Double fertilization involving syngamy and triple fusion is a unique characteristic feature of:",
        "opts": ["Algae", "Bryophytes", "Gymnosperms", "Angiosperms"],
        "ans": 3,
        "topic": "Plant Kingdom",
        "exp": "Double fertilization occurs exclusively in flowering plants (Angiosperms), forming a diploid zygote and a triploid primary endosperm nucleus (PEN)."
    },
    {
        "q": "The organelle known as the 'powerhouse of the cell' where ATP synthesis occurs via oxidative phosphorylation is:",
        "opts": ["Golgi apparatus", "Ribosome", "Mitochondrion", "Lysosome"],
        "ans": 2,
        "topic": "Cell: The Unit of Life",
        "exp": "Mitochondria generate ATP through cellular respiration on their inner cristae membrane."
    },
    {
        "q": "During meiotic cell division, crossing over between non-sister chromatids of homologous chromosomes occurs during which stage of Prophase I?",
        "opts": ["Leptotene", "Zygotene", "Pachytene", "Diplotene"],
        "ans": 2,
        "topic": "Cell Cycle and Cell Division",
        "exp": "Crossing over and recombination nodules mediated by recombinase enzyme occur specifically during the Pachytene stage."
    },
    {
        "q": "Which nitrogenous base is present in RNA but absent in DNA?",
        "opts": ["Adenine", "Guanine", "Cytosine", "Uracil"],
        "ans": 3,
        "topic": "Biomolecules",
        "exp": "RNA contains Uracil (U) instead of Thymine (T) present in DNA."
    },
    {
        "q": "In C₄ plants, the primary carbon dioxide (CO₂) acceptor in mesophyll cells is:",
        "opts": ["Ribulose-1,5-bisphosphate (RuBP)", "Phosphoenolpyruvate (PEP)", "Oxaloacetic acid (OAA)", "Phosphoglyceric acid (PGA)"],
        "ans": 1,
        "topic": "Photosynthesis in Higher Plants",
        "exp": "In C₄ plants, CO₂ is fixed by PEP carboxylase in mesophyll cells using Phosphoenolpyruvate (PEP) to form 4-carbon OAA."
    },
    {
        "q": "The gaseous plant growth regulator (phytohormone) responsible for promoting fruit ripening is:",
        "opts": ["Auxin", "Gibberellin", "Cytokinin", "Ethylene"],
        "ans": 3,
        "topic": "Plant Growth and Development",
        "exp": "Ethylene (C₂H₄) is a gaseous hormone that regulates fruit ripening, triple response, and abscission."
    },
    {
        "q": "The functional structural and filtration unit of the human kidney is called:",
        "opts": ["Neuron", "Nephron", "Alveolus", "Glomerulus"],
        "ans": 1,
        "topic": "Excretory Products and their Elimination",
        "exp": "Each human kidney contains approximately 1 million functional filtering units called nephrons."
    },
    {
        "q": "During cardiac cycle, the first heart sound 'LUBB' is produced due to the closure of:",
        "opts": ["Semilunar valves", "Atrioventricular (Tricuspid and Bicuspid) valves", "Sinoatrial node", "Aortic valve"],
        "ans": 1,
        "topic": "Body Fluids and Circulation",
        "exp": "The first heart sound (lub) is associated with the closure of the tricuspid and bicuspid (AV) valves at the onset of ventricular systole."
    },
    {
        "q": "The hormone secreted by the beta cells of Islets of Langerhans in the pancreas to decrease blood glucose levels is:",
        "opts": ["Glucagon", "Insulin", "Somatostatin", "Thyroxine"],
        "ans": 1,
        "topic": "Chemical Coordination and Integration",
        "exp": "Insulin acts on hepatocytes and adipocytes to enhance cellular glucose uptake and glycogenesis, lowering blood glucose."
    },
    {
        "q": "In Mendel's dihybrid cross between round yellow (RRYY) and wrinkled green (rryy) pea plants, the phenotypic ratio in F₂ generation is:",
        "opts": ["3 : 1", "1 : 2 : 1", "9 : 3 : 3 : 1", "9 : 7"],
        "ans": 2,
        "topic": "Principles of Inheritance and Variation",
        "exp": "Dihybrid phenotypic ratio in F₂ generation is 9 (Round Yellow) : 3 (Round Green) : 3 (Wrinkled Yellow) : 1 (Wrinkled Green)."
    },
    {
        "q": "The enzyme responsible for unwinding the DNA double helix during DNA replication is:",
        "opts": ["DNA Polymerase", "DNA Ligase", "Helicase", "RNA Primase"],
        "ans": 2,
        "topic": "Molecular Basis of Inheritance",
        "exp": "DNA Helicase breaks hydrogen bonds between base pairs to unwind the replication fork."
    },
    {
        "q": "In the Lac Operon model of E. coli, the repressor protein synthesized by the i-gene binds to which region in the absence of lactose?",
        "opts": ["Promoter region", "Operator region", "Structural gene z", "Structural gene a"],
        "ans": 1,
        "topic": "Molecular Basis of Inheritance",
        "exp": "In the absence of inducer (lactose), the repressor binds to the operator region, preventing RNA polymerase from transcribing the operon."
    },
    {
        "q": "EcoRI is a restriction endonuclease enzyme isolated from Escherichia coli. The letter 'R' in EcoRI designates:",
        "opts": ["Restriction type", "Strain RY13 of the bacterium", "Recombinant DNA", "Ribosomal locus"],
        "ans": 1,
        "topic": "Biotechnology: Principles and Processes",
        "exp": "In EcoRI: E = Escherichia, co = coli, R = strain RY13, I = first endonuclease isolated from this strain."
    },
    {
        "q": "According to Lindeman's 10% Law of energy transfer in an ecosystem, the percentage of energy transferred from one trophic level to the next higher trophic level is:",
        "opts": ["1%", "10%", "50%", "90%"],
        "ans": 1,
        "topic": "Ecosystem",
        "exp": "Only 10% of energy is transferred to each higher trophic level; 90% is lost as heat during metabolic processes."
    },
    {
        "q": "Which of the following is an example of Ex-situ conservation of biodiversity?",
        "opts": ["National Parks", "Wildlife Sanctuaries", "Botanical Gardens & Zoological Parks", "Biosphere Reserves"],
        "ans": 2,
        "topic": "Biodiversity and Conservation",
        "exp": "Ex-situ conservation involves protecting threatened species outside their natural habitat (e.g. Botanical Gardens, Seed Banks, Zoo Parks)."
    },
    {
        "q": "The functional unit of contraction in human skeletal muscle fiber between two successive Z-lines is called:",
        "opts": ["Sarcolemma", "Sarcomere", "Sarcoplasmic reticulum", "Myofibril"],
        "ans": 1,
        "topic": "Locomotion and Movement",
        "exp": "The anatomical and functional unit of contraction in a myofibril bounded by two Z-lines is the sarcomere."
    },
    {
        "q": "Which hormone triggers ovulation (release of secondary oocyte from Graafian follicle) around the 14th day of human menstrual cycle?",
        "opts": ["Follicle Stimulating Hormone (FSH)", "Luteinizing Hormone (LH surge)", "Progesterone", "Estrogen"],
        "ans": 1,
        "topic": "Human Reproduction",
        "exp": "A rapid surge in LH (LH surge) mid-cycle causes rupture of the mature Graafian follicle and induces ovulation."
    },
    {
        "q": "The primary site of gas exchange (O₂ and CO₂) in human lungs is:",
        "opts": ["Trachea", "Bronchi", "Alveoli", "Pleural cavity"],
        "ans": 2,
        "topic": "Breathing and Exchange of Gases",
        "exp": "Alveoli are thin-walled vascularized bag-like structures providing a large surface area for diffusion of gases."
    },
    {
        "q": "Bt cotton plants are resistant to insect pests like bollworms due to the expression of Cry toxins derived from:",
        "opts": ["Bacillus thuringiensis", "Agrobacterium tumefaciens", "Escherichia coli", "Rhizobium leguminosarum"],
        "ans": 0,
        "topic": "Biotechnology and its Applications",
        "exp": "Cry genes from the soil bacterium Bacillus thuringiensis encode insecticidal crystal proteins toxic to bollworms."
    }
]

from smartkcet.rag.mcq_extractor import PHYSICS_NUMERICAL_BANK

all_subjects_map = {
    "Physics": PHYSICS_NUMERICAL_BANK,
    "Chemistry": CHEMISTRY_QUESTIONS,
    "Mathematics": MATHEMATICS_QUESTIONS,
    "Biology": BIOLOGY_QUESTIONS,
}

total_inserted = 0

for subject, q_list in all_subjects_map.items():
    batch_id = str(uuid.uuid4())
    print(f"Seeding {len(q_list)} authentic KCET questions for {subject}...")
    for item in q_list:
        ans_val = str(item["ans"]) if isinstance(item["ans"], int) else str(item["ans"])
        c.execute(
            """
            INSERT INTO questions (id, subject, question_text, options, correct_option, topic, explanation, generation_batch_id, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                subject,
                item["q"],
                json.dumps(item["opts"]),
                ans_val,
                item["topic"],
                item.get("exp", ""),
                batch_id,
                "kcet_authentic_bank"
            )
        )
        total_inserted += 1

conn.commit()
print(f"Successfully seeded {total_inserted} high-quality authentic questions across all 4 subjects into DB!")
