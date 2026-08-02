"""Official KCET Syllabus Seed Data.

Source: Karnataka Examinations Authority (KEA) & Department of Pre-University
Education (DPUE), Karnataka. Aligned with NCERT Class 11 (1st PUC) and
Class 12 (2nd PUC) textbooks as prescribed for KCET 2026.

Cross-referenced via:
- Deeksha Learning (deekshalearning.com/blog/kcet-physics-syllabus-overview/)
- Aakash Educational Services (aakash.ac.in/kcet-syllabus)
- Karnataka PUC board chapter structure (kseeb.kar.nic.in / pue.kar.nic.in)

Total topics seeded:
  Physics   : 10 (1st PUC) + 9 (2nd PUC) = 19
  Chemistry : 14 (1st PUC) + 12 (2nd PUC) = 26
  Mathematics: 12 (1st PUC) + 10 (2nd PUC) = 22
  Biology   : 22 (1st PUC) + 16 (2nd PUC) = 38
  TOTAL     : 105 chapters
"""

# Each entry: (subject, puc_year, chapter_number, chapter_name, display_order, description)
SYLLABUS_DATA = [

    # ──────────────────────────────────────────────────────────────────────
    # PHYSICS — 1st PUC (Class 11)
    # ──────────────────────────────────────────────────────────────────────
    ("Physics", "1st PUC",  1, "Physical World",
        10, "Nature of physical laws; physics in relation to science, society, and technology"),
    ("Physics", "1st PUC",  2, "Units and Measurements",
        20, "Need for measurement; units of measurement; SI units; dimensional analysis; significant figures"),
    ("Physics", "1st PUC",  3, "Motion in a Straight Line",
        30, "Position-time graph; speed and velocity; uniform and non-uniform motion; kinematic equations"),
    ("Physics", "1st PUC",  4, "Motion in a Plane",
        40, "Scalars and vectors; projectile motion; uniform circular motion; relative velocity"),
    ("Physics", "1st PUC",  5, "Laws of Motion",
        50, "Aristotle's fallacy; Newton's three laws; impulse; friction; circular motion dynamics"),
    ("Physics", "1st PUC",  6, "Work, Energy and Power",
        60, "Work-energy theorem; kinetic and potential energy; conservation of energy; power; collisions"),
    ("Physics", "1st PUC",  7, "System of Particles and Rotational Motion",
        70, "Centre of mass; moment of inertia; torque; angular momentum; rolling motion"),
    ("Physics", "1st PUC",  8, "Gravitation",
        80, "Universal law of gravitation; acceleration due to gravity; orbital velocity; escape velocity; satellites"),
    ("Physics", "1st PUC",  9, "Mechanical Properties of Solids and Fluids",
        90, "Elasticity; stress-strain curve; viscosity; surface tension; Bernoulli's principle; Stokes' law"),
    ("Physics", "1st PUC", 10, "Thermal Properties of Matter",
        100, "Heat; temperature; thermal expansion; specific heat capacity; calorimetry; heat transfer"),
    ("Physics", "1st PUC", 11, "Thermodynamics",
        110, "Thermal equilibrium; zeroth law; first law; second law; isothermal/adiabatic processes; heat engines"),
    ("Physics", "1st PUC", 12, "Kinetic Theory of Gases",
        120, "Equation of state; kinetic theory; RMS speed; degrees of freedom; mean free path"),
    ("Physics", "1st PUC", 13, "Oscillations",
        130, "Periodic motion; SHM; simple pendulum; damped oscillations; resonance"),
    ("Physics", "1st PUC", 14, "Waves",
        140, "Transverse and longitudinal waves; wave equation; speed of sound; beats; Doppler effect"),

    # ──────────────────────────────────────────────────────────────────────
    # PHYSICS — 2nd PUC (Class 12)
    # ──────────────────────────────────────────────────────────────────────
    ("Physics", "2nd PUC",  1, "Electric Charges and Fields",
        10, "Charge; Coulomb's law; electric field; Gauss's law; dipole"),
    ("Physics", "2nd PUC",  2, "Electrostatic Potential and Capacitance",
        20, "Potential; equipotential surfaces; capacitors; dielectrics; energy stored"),
    ("Physics", "2nd PUC",  3, "Current Electricity",
        30, "Drift velocity; Ohm's law; resistivity; Kirchhoff's laws; Wheatstone bridge; potentiometer"),
    ("Physics", "2nd PUC",  4, "Moving Charges and Magnetism",
        40, "Biot-Savart law; Ampere's law; force on conductor; cyclotron; galvanometer"),
    ("Physics", "2nd PUC",  5, "Magnetism and Matter",
        50, "Bar magnet; magnetic field lines; Earth's magnetism; para/dia/ferromagnetism"),
    ("Physics", "2nd PUC",  6, "Electromagnetic Induction",
        60, "Faraday's laws; Lenz's law; motional EMF; self-induction; mutual induction"),
    ("Physics", "2nd PUC",  7, "Alternating Current",
        70, "AC generator; RMS values; LCR circuit; resonance; power factor; transformers"),
    ("Physics", "2nd PUC",  8, "Electromagnetic Waves",
        80, "Displacement current; Maxwell's equations; electromagnetic spectrum"),
    ("Physics", "2nd PUC",  9, "Ray Optics and Optical Instruments",
        90, "Reflection; refraction; TIR; prism; lenses; human eye; microscope; telescope"),
    ("Physics", "2nd PUC", 10, "Wave Optics",
        100, "Huygens' principle; interference; Young's YDSE; diffraction; polarisation"),
    ("Physics", "2nd PUC", 11, "Dual Nature of Radiation and Matter",
        110, "Photoelectric effect; Einstein's equation; de Broglie wavelength; Davisson-Germer"),
    ("Physics", "2nd PUC", 12, "Atoms",
        120, "Bohr model; hydrogen spectrum; atomic spectra; energy levels"),
    ("Physics", "2nd PUC", 13, "Nuclei",
        130, "Nuclear composition; binding energy; radioactivity; alpha/beta/gamma decay; fission; fusion"),
    ("Physics", "2nd PUC", 14, "Semiconductor Electronics",
        140, "Energy bands; p-n junction; diode; LED; solar cell; Zener diode; transistor"),

    # ──────────────────────────────────────────────────────────────────────
    # CHEMISTRY — 1st PUC (Class 11)
    # ──────────────────────────────────────────────────────────────────────
    ("Chemistry", "1st PUC",  1, "Some Basic Concepts of Chemistry",
        10, "Importance of chemistry; laws of chemical combination; mole concept; stoichiometry"),
    ("Chemistry", "1st PUC",  2, "Structure of Atom",
        20, "Atomic models; quantum numbers; orbitals; electronic configuration; Aufbau principle"),
    ("Chemistry", "1st PUC",  3, "Classification of Elements and Periodicity in Properties",
        30, "Periodic law; periodic table; periodic trends in properties"),
    ("Chemistry", "1st PUC",  4, "Chemical Bonding and Molecular Structure",
        40, "Ionic and covalent bonds; VSEPR theory; hybridisation; molecular orbital theory"),
    ("Chemistry", "1st PUC",  5, "States of Matter",
        50, "Gas laws; kinetic molecular theory; real gases; liquids; intermolecular forces"),
    ("Chemistry", "1st PUC",  6, "Thermodynamics",
        60, "System/surroundings; internal energy; enthalpy; Hess's law; entropy; Gibbs energy"),
    ("Chemistry", "1st PUC",  7, "Equilibrium",
        70, "Law of mass action; Kp and Kc; Le Chatelier's principle; ionic equilibrium; pH; buffers"),
    ("Chemistry", "1st PUC",  8, "Redox Reactions",
        80, "Oxidation state; oxidation/reduction; balancing redox equations"),
    ("Chemistry", "1st PUC",  9, "Hydrogen",
        90, "Position in periodic table; preparation and properties of H2O; hydrogen peroxide"),
    ("Chemistry", "1st PUC", 10, "The s-Block Elements",
        100, "Group 1 and 2 elements; properties; compounds: NaOH, Na2CO3, CaCO3, CaO"),
    ("Chemistry", "1st PUC", 11, "The p-Block Elements (Group 13 and 14)",
        110, "Boron family; carbon family; allotropes of carbon; silicon"),
    ("Chemistry", "1st PUC", 12, "Organic Chemistry — Some Basic Principles and Techniques",
        120, "Classification; IUPAC nomenclature; isomerism; reaction intermediates; purification"),
    ("Chemistry", "1st PUC", 13, "Hydrocarbons",
        130, "Alkanes; alkenes; alkynes; aromatic hydrocarbons; carcinogenicity; toxicity"),
    ("Chemistry", "1st PUC", 14, "Environmental Chemistry",
        140, "Atmospheric pollution; water pollution; soil pollution; industrial waste management"),

    # ──────────────────────────────────────────────────────────────────────
    # CHEMISTRY — 2nd PUC (Class 12)
    # ──────────────────────────────────────────────────────────────────────
    ("Chemistry", "2nd PUC",  1, "The Solid State",
        10, "Classification of solids; crystal systems; packing; defects; electrical/magnetic properties"),
    ("Chemistry", "2nd PUC",  2, "Solutions",
        20, "Types of solutions; colligative properties; Raoult's law; osmosis; van't Hoff factor"),
    ("Chemistry", "2nd PUC",  3, "Electrochemistry",
        30, "Electrochemical cells; EMF; Nernst equation; electrolysis; Kohlrausch's law; batteries/fuel cells"),
    ("Chemistry", "2nd PUC",  4, "Chemical Kinetics",
        40, "Rate of reaction; order; molecularity; Arrhenius equation; activation energy; catalysis"),
    ("Chemistry", "2nd PUC",  5, "Surface Chemistry",
        50, "Adsorption; catalysis; colloids; emulsions; Tyndall effect"),
    ("Chemistry", "2nd PUC",  6, "General Principles and Processes of Isolation of Elements",
        60, "Occurrence; concentration; extraction; refining; uses of Al, Cu, Zn, Fe"),
    ("Chemistry", "2nd PUC",  7, "The p-Block Elements (Group 15, 16, 17, 18)",
        70, "Nitrogen; phosphorus; oxygen; sulphur; halogens; noble gases"),
    ("Chemistry", "2nd PUC",  8, "The d and f Block Elements",
        80, "Transition elements; properties; lanthanoids; actinoids"),
    ("Chemistry", "2nd PUC",  9, "Coordination Compounds",
        90, "Werner's theory; IUPAC nomenclature; isomerism; bonding; stability; importance"),
    ("Chemistry", "2nd PUC", 10, "Haloalkanes and Haloarenes",
        100, "Classification; preparation; properties; SN1/SN2; elimination reactions; uses"),
    ("Chemistry", "2nd PUC", 11, "Alcohols, Phenols and Ethers",
        110, "Preparation; physical/chemical properties; uses; important reactions"),
    ("Chemistry", "2nd PUC", 12, "Aldehydes, Ketones and Carboxylic Acids",
        120, "Preparation; nucleophilic addition; oxidation/reduction; Cannizzaro; Aldol condensation"),
    ("Chemistry", "2nd PUC", 13, "Amines",
        130, "Classification; IUPAC nomenclature; preparation; basic character; diazonium salts"),
    ("Chemistry", "2nd PUC", 14, "Biomolecules",
        140, "Carbohydrates; proteins; enzymes; vitamins; nucleic acids; hormones"),
    ("Chemistry", "2nd PUC", 15, "Polymers",
        150, "Classification; addition/condensation polymerisation; natural/synthetic/biodegradable polymers"),
    ("Chemistry", "2nd PUC", 16, "Chemistry in Everyday Life",
        160, "Medicines; food chemicals; cleansing agents; drugs; dyes"),

    # ──────────────────────────────────────────────────────────────────────
    # MATHEMATICS — 1st PUC (Class 11)
    # ──────────────────────────────────────────────────────────────────────
    ("Mathematics", "1st PUC",  1, "Sets",
        10, "Types of sets; subsets; operations: union, intersection, difference; Venn diagrams"),
    ("Mathematics", "1st PUC",  2, "Relations and Functions",
        20, "Ordered pairs; Cartesian product; relations; types of functions; graphs"),
    ("Mathematics", "1st PUC",  3, "Trigonometric Functions",
        30, "Angles; radian measure; trig ratios; identities; signs; equations; inverse functions"),
    ("Mathematics", "1st PUC",  4, "Principle of Mathematical Induction",
        40, "Process of induction; motivating applications; proving formulas"),
    ("Mathematics", "1st PUC",  5, "Complex Numbers and Quadratic Equations",
        50, "Complex numbers; algebra; Argand plane; modulus/argument; quadratic equations"),
    ("Mathematics", "1st PUC",  6, "Linear Inequalities",
        60, "Inequalities; algebraic solutions; graphical representation; system of linear inequalities"),
    ("Mathematics", "1st PUC",  7, "Permutations and Combinations",
        70, "Fundamental principle of counting; permutations; combinations; nPr; nCr"),
    ("Mathematics", "1st PUC",  8, "Binomial Theorem",
        80, "Binomial theorem for positive integral index; general and middle terms; properties"),
    ("Mathematics", "1st PUC",  9, "Sequences and Series",
        90, "AP; GP; HP; AM-GM-HM inequality; sum of n terms; special series"),
    ("Mathematics", "1st PUC", 10, "Straight Lines",
        100, "Slope; various forms of equation; angle between lines; distance formulas"),
    ("Mathematics", "1st PUC", 11, "Conic Sections",
        110, "Circle; parabola; ellipse; hyperbola; standard equations; applications"),
    ("Mathematics", "1st PUC", 12, "Introduction to Three-Dimensional Geometry",
        120, "Coordinate axes; distance formula; section formula in 3D"),
    ("Mathematics", "1st PUC", 13, "Limits and Derivatives",
        130, "Concept of limit; algebra of limits; derivatives; first principle; standard results"),
    ("Mathematics", "1st PUC", 14, "Statistics",
        140, "Measures of dispersion: range, mean deviation, variance, standard deviation"),
    ("Mathematics", "1st PUC", 15, "Probability",
        150, "Random experiments; events; axiomatic probability; addition theorem"),

    # ──────────────────────────────────────────────────────────────────────
    # MATHEMATICS — 2nd PUC (Class 12)
    # ──────────────────────────────────────────────────────────────────────
    ("Mathematics", "2nd PUC",  1, "Relations and Functions",
        10, "Types of relations; invertible functions; composition; binary operations"),
    ("Mathematics", "2nd PUC",  2, "Inverse Trigonometric Functions",
        20, "Domains; ranges; graphs; properties and formulas"),
    ("Mathematics", "2nd PUC",  3, "Matrices",
        30, "Types of matrices; operations; transpose; symmetric; elementary row/column operations"),
    ("Mathematics", "2nd PUC",  4, "Determinants",
        40, "Determinant of 2×2/3×3; properties; minors/cofactors; area of triangle; Cramer's rule"),
    ("Mathematics", "2nd PUC",  5, "Continuity and Differentiability",
        50, "Continuity; differentiability; chain rule; implicit functions; logarithmic differentiation"),
    ("Mathematics", "2nd PUC",  6, "Application of Derivatives",
        60, "Rate of change; increasing/decreasing; maxima/minima; tangents and normals; approximations"),
    ("Mathematics", "2nd PUC",  7, "Integrals",
        70, "Integration by parts; substitution; partial fractions; definite integrals; fundamental theorem"),
    ("Mathematics", "2nd PUC",  8, "Application of Integrals",
        80, "Area under curves; area between two curves"),
    ("Mathematics", "2nd PUC",  9, "Differential Equations",
        90, "Order and degree; solution methods: variable separable; homogeneous; linear"),
    ("Mathematics", "2nd PUC", 10, "Vector Algebra",
        100, "Types of vectors; algebra; dot and cross products; scalar triple product"),
    ("Mathematics", "2nd PUC", 11, "Three-Dimensional Geometry",
        110, "Direction cosines/ratios; equations of lines and planes; angle between; distance"),
    ("Mathematics", "2nd PUC", 12, "Linear Programming",
        120, "Linear constraints; feasible region; graphical method; corner-point method"),
    ("Mathematics", "2nd PUC", 13, "Probability",
        130, "Conditional probability; multiplication theorem; independent events; Bayes' theorem; probability distributions; Bernoulli trials"),

    # ──────────────────────────────────────────────────────────────────────
    # BIOLOGY — 1st PUC (Class 11)
    # ──────────────────────────────────────────────────────────────────────
    ("Biology", "1st PUC",  1, "The Living World",
        10, "Characteristics of living organisms; taxonomy; taxonomic hierarchy; nomenclature"),
    ("Biology", "1st PUC",  2, "Biological Classification",
        20, "Five kingdom classification; Monera; Protista; Fungi; Plantae; Animalia"),
    ("Biology", "1st PUC",  3, "Plant Kingdom",
        30, "Algae; Bryophytes; Pteridophytes; Gymnosperms; Angiosperms; alternation of generations"),
    ("Biology", "1st PUC",  4, "Animal Kingdom",
        40, "Classification criteria; non-chordates; chordates; salient features of phyla and classes"),
    ("Biology", "1st PUC",  5, "Morphology of Flowering Plants",
        50, "Root; stem; leaf; flower; fruit; seed; modifications; description of some families"),
    ("Biology", "1st PUC",  6, "Anatomy of Flowering Plants",
        60, "Meristematic and permanent tissues; dicot/monocot anatomy; secondary growth"),
    ("Biology", "1st PUC",  7, "Structural Organisation in Animals",
        70, "Morphology and anatomy of earthworm; cockroach; frog"),
    ("Biology", "1st PUC",  8, "Cell — The Unit of Life",
        80, "Cell theory; prokaryotic/eukaryotic cell; cell organelles and their functions"),
    ("Biology", "1st PUC",  9, "Biomolecules",
        90, "Carbohydrates; proteins; lipids; nucleic acids; enzymes"),
    ("Biology", "1st PUC", 10, "Cell Cycle and Cell Division",
        100, "Cell cycle; mitosis; meiosis; significance"),
    ("Biology", "1st PUC", 11, "Transport in Plants",
        110, "Means of transport; diffusion; osmosis; absorption; translocation; water potential"),
    ("Biology", "1st PUC", 12, "Mineral Nutrition",
        120, "Essential mineral elements; deficiency symptoms; nitrogen nutrition"),
    ("Biology", "1st PUC", 13, "Photosynthesis in Higher Plants",
        130, "Light reactions; Calvin cycle; C3 and C4 pathways; CAM; factors affecting"),
    ("Biology", "1st PUC", 14, "Respiration in Plants",
        140, "Aerobic and anaerobic respiration; glycolysis; Krebs cycle; ETC; ATP"),
    ("Biology", "1st PUC", 15, "Plant Growth and Development",
        150, "Seed germination; growth regulators: auxins, gibberellins, cytokinins, ABA, ethylene"),
    ("Biology", "1st PUC", 16, "Digestion and Absorption",
        160, "Alimentary canal; digestive glands; digestion; absorption; disorders"),
    ("Biology", "1st PUC", 17, "Breathing and Exchange of Gases",
        170, "Respiratory organs; breathing mechanism; gas exchange; transport of O2 and CO2; disorders"),
    ("Biology", "1st PUC", 18, "Body Fluids and Circulation",
        180, "Blood; lymph; circulatory pathways; cardiac cycle; ECG; disorders"),
    ("Biology", "1st PUC", 19, "Excretory Products and Their Elimination",
        190, "Ammonotelism; ureotelism; ureocotelism; nephron; urine formation; osmoregulation"),
    ("Biology", "1st PUC", 20, "Locomotion and Movement",
        200, "Types of movement; skeletal muscle; mechanism of contraction; skeletal system; joints; disorders"),
    ("Biology", "1st PUC", 21, "Neural Control and Coordination",
        210, "Neurons; CNS; PNS; sensory receptors; reflex action; sense organs"),
    ("Biology", "1st PUC", 22, "Chemical Coordination and Integration",
        220, "Endocrine glands; hormones; hormonal regulation; disorders"),

    # ──────────────────────────────────────────────────────────────────────
    # BIOLOGY — 2nd PUC (Class 12)
    # ──────────────────────────────────────────────────────────────────────
    ("Biology", "2nd PUC",  1, "Reproduction in Organisms",
        10, "Asexual and sexual reproduction; modes of asexual reproduction; life spans"),
    ("Biology", "2nd PUC",  2, "Sexual Reproduction in Flowering Plants",
        20, "Flower structure; pollination; fertilisation; post-fertilisation; fruit/seed development"),
    ("Biology", "2nd PUC",  3, "Human Reproduction",
        30, "Male/female reproductive system; gametogenesis; menstrual cycle; fertilisation; embryo development"),
    ("Biology", "2nd PUC",  4, "Reproductive Health",
        40, "Population stabilisation; birth control; MTP; STDs; infertility; ART"),
    ("Biology", "2nd PUC",  5, "Principles of Inheritance and Variation",
        50, "Mendel's laws; dihybrid cross; chromosomal theory; linkage; sex determination; mutations"),
    ("Biology", "2nd PUC",  6, "Molecular Basis of Inheritance",
        60, "DNA structure; replication; transcription; translation; genetic code; regulation of gene expression"),
    ("Biology", "2nd PUC",  7, "Evolution",
        70, "Origin of life; theories of evolution; natural selection; HWE; evidence of evolution; speciation"),
    ("Biology", "2nd PUC",  8, "Human Health and Disease",
        80, "Common diseases; immunity; AIDS; cancer; drugs; alcohol; immune system"),
    ("Biology", "2nd PUC",  9, "Strategies for Enhancement in Food Production",
        90, "Plant breeding; biofortification; SCP; tissue culture; animal husbandry"),
    ("Biology", "2nd PUC", 10, "Microbes in Human Welfare",
        100, "Fermentation; antibiotics; sewage treatment; biogas; biocontrol"),
    ("Biology", "2nd PUC", 11, "Biotechnology — Principles and Processes",
        110, "Genetic engineering; restriction enzymes; recombinant DNA; PCR; gel electrophoresis"),
    ("Biology", "2nd PUC", 12, "Biotechnology and its Applications",
        120, "GM organisms; Bt crops; insulin; gene therapy; biopiracy; ethical issues"),
    ("Biology", "2nd PUC", 13, "Organisms and Populations",
        130, "Ecological levels; populations; attributes; growth; interspecific interactions"),
    ("Biology", "2nd PUC", 14, "Ecosystem",
        140, "Components; productivity; decomposition; energy flow; nutrient cycles; ecosystem services"),
    ("Biology", "2nd PUC", 15, "Biodiversity and Conservation",
        150, "Biodiversity patterns; loss; conservation strategies: in-situ, ex-situ; hotspots; Red Data Book"),
    ("Biology", "2nd PUC", 16, "Environmental Issues",
        160, "Air/water pollution; ozone depletion; global warming; deforestation; case studies"),
]


def seed_syllabus(session) -> int:
    """Insert all KCET syllabus topics if the table is empty.

    Returns the number of rows inserted (0 if already seeded).
    """
    from .models import SyllabusTopic
    from sqlalchemy import select

    existing = session.execute(select(SyllabusTopic).limit(1)).scalar_one_or_none()
    if existing is not None:
        return 0  # Already seeded — skip

    rows = []
    for subject, puc_year, chapter_num, chapter_name, display_order, description in SYLLABUS_DATA:
        rows.append(SyllabusTopic(
            subject=subject,
            puc_year=puc_year,
            chapter_number=chapter_num,
            chapter_name=chapter_name,
            display_order=display_order,
            description=description,
            is_active=True,
        ))

    session.add_all(rows)
    session.commit()
    return len(rows)
