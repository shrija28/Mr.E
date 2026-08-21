import json
import sqlite3
import uuid
from pathlib import Path
import faiss
import numpy as np

# 1. Connect to SQLite database
db_path = Path("backend/smartkcet.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Cleaning up corrupted/junk Physics questions from database...")

# Delete all current Physics questions in DB
c.execute("DELETE FROM questions WHERE subject='Physics'")
conn.commit()
print("Deleted existing Physics rows.")

# High quality KCET Physics Question Bank (Numericals & Core Concepts)
PHYSICS_QUESTIONS = [
    {
        "q": "A car starting from rest accelerates uniformly at a rate of 2 m/s² for 10 s. What is the total distance traveled by the car?",
        "opts": ["50 m", "100 m", "150 m", "200 m"],
        "ans": "1",
        "topic": "Motion in a Straight Line",
        "exp": "Using s = ut + (1/2)at², with u = 0, a = 2 m/s², t = 10 s: s = 0 + 0.5 * 2 * 100 = 100 m."
    },
    {
        "q": "A body of mass 5 kg is dropped from a height of 20 m. Taking g = 10 m/s², the velocity of the body just before striking the ground is:",
        "opts": ["10 m/s", "20 m/s", "30 m/s", "40 m/s"],
        "ans": "1",
        "topic": "Motion in a Straight Line",
        "exp": "Using v² = u² + 2gh, v² = 0 + 2(10)(20) = 400 => v = 20 m/s."
    },
    {
        "q": "A projectile is thrown with an initial velocity of 20 m/s at an angle of 30° with the horizontal. The maximum height attained by it is (g = 10 m/s²):",
        "opts": ["2.5 m", "5.0 m", "7.5 m", "10.0 m"],
        "ans": "1",
        "topic": "Motion in a Plane",
        "exp": "H_max = (u sin θ)² / (2g) = (20 * 0.5)² / (2 * 10) = 100 / 20 = 5.0 m."
    },
    {
        "q": "A force of 20 N acts on a body of mass 4 kg initially at rest. The work done by the force in 3 seconds is:",
        "opts": ["150 J", "225 J", "450 J", "900 J"],
        "ans": "2",
        "topic": "Laws of Motion & Work Energy",
        "exp": "a = F/m = 20/4 = 5 m/s². Displacement in 3 s: s = 0.5 * 5 * 9 = 22.5 m. Work = F * s = 20 * 22.5 = 450 J."
    },
    {
        "q": "If the momentum of a body is increased by 50%, its kinetic energy increases by:",
        "opts": ["50%", "100%", "125%", "150%"],
        "ans": "2",
        "topic": "Work, Energy and Power",
        "exp": "K = p²/(2m). If p becomes 1.5p, K becomes (1.5)² K = 2.25 K, an increase of 125%."
    },
    {
        "q": "The acceleration due to gravity at a height equal to the radius of Earth (R) above the Earth's surface is:",
        "opts": ["g/2", "g/3", "g/4", "g/9"],
        "ans": "2",
        "topic": "Gravitation",
        "exp": "g' = g (R / (R + h))² = g (R / 2R)² = g/4."
    },
    {
        "q": "The escape velocity from the surface of Earth is 11.2 km/s. If a planet has 4 times the mass and double the radius of Earth, its escape velocity is:",
        "opts": ["11.2 km/s", "15.8 km/s", "22.4 km/s", "31.6 km/s"],
        "ans": "1",
        "topic": "Gravitation",
        "exp": "v_e = √(2GM/R). For M'=4M and R'=2R: v_e' = √(4/2) v_e = √2 * 11.2 ≈ 15.8 km/s."
    },
    {
        "q": "Two point charges +4 µC and +16 µC are separated by a distance of 12 cm. The distance from the +4 µC charge where the net electric field is zero is:",
        "opts": ["3 cm", "4 cm", "6 cm", "8 cm"],
        "ans": "1",
        "topic": "Electric Charges and Fields",
        "exp": "q1/x² = q2/(d-x)². √(q2/q1) = (d-x)/x => √(16/4) = 2 = (12-x)/x => 2x = 12-x => 3x = 12 => x = 4 cm."
    },
    {
        "q": "Three capacitors of capacitance 6 µF each are connected in series across a 12 V battery. The charge on each capacitor is:",
        "opts": ["12 µC", "24 µC", "36 µC", "72 µC"],
        "ans": "1",
        "topic": "Electrostatic Potential and Capacitance",
        "exp": "C_eq = 6/3 = 2 µF in series. Charge Q = C_eq * V = 2 µF * 12 V = 24 µC."
    },
    {
        "q": "A wire of resistance 16 Ω is cut into 4 equal pieces and connected in parallel. The equivalent resistance of the combination is:",
        "opts": ["1 Ω", "2 Ω", "4 Ω", "8 Ω"],
        "ans": "0",
        "topic": "Current Electricity",
        "exp": "Each piece has resistance 16/4 = 4 Ω. Connected in parallel: R_eq = 4/4 = 1 Ω."
    },
    {
        "q": "A cell of emf 1.5 V and internal resistance 0.5 Ω is connected across an external resistance of 2.5 Ω. The potential difference across the cell terminals is:",
        "opts": ["1.0 V", "1.25 V", "1.35 V", "1.5 V"],
        "ans": "1",
        "topic": "Current Electricity",
        "exp": "I = E / (R + r) = 1.5 / (2.5 + 0.5) = 0.5 A. Terminal V = E - I*r = 1.5 - (0.5 * 0.5) = 1.25 V."
    },
    {
        "q": "A circular coil of 100 turns and radius 5 cm carries a current of 1 A. The magnetic field at the center of the coil is (µ₀ = 4π × 10⁻⁷ T·m/A):",
        "opts": ["4π × 10⁻⁴ T", "2π × 10⁻⁴ T", "4π × 10⁻⁵ T", "2π × 10⁻⁵ T"],
        "ans": "0",
        "topic": "Moving Charges and Magnetism",
        "exp": "B = (µ₀ N I) / (2 R) = (4π×10⁻⁷ * 100 * 1) / (2 * 0.05) = 4π × 10⁻⁴ T."
    },
    {
        "q": "An AC voltage V = 200 sin(100π t) is applied across a 50 Ω resistor. The RMS value of current flowing through the resistor is:",
        "opts": ["2 A", "2.83 A", "4 A", "5.66 A"],
        "ans": "1",
        "topic": "Alternating Current",
        "exp": "V_peak = 200 V => V_rms = 200 / √2 ≈ 141.4 V. I_rms = V_rms / R = 141.4 / 50 ≈ 2.83 A."
    },
    {
        "q": "In a pure inductive circuit of L = 0.1 H connected to 220 V, 50 Hz AC supply, the inductive reactance X_L is approximately:",
        "opts": ["15.7 Ω", "31.4 Ω", "62.8 Ω", "100 Ω"],
        "ans": "1",
        "topic": "Alternating Current",
        "exp": "X_L = 2π f L = 2 * 3.1416 * 50 * 0.1 = 31.4 Ω."
    },
    {
        "q": "A convex lens of focal length 20 cm is placed in contact with a concave lens of focal length 40 cm. The focal length of the combination is:",
        "opts": ["+20 cm", "+40 cm", "-20 cm", "-40 cm"],
        "ans": "1",
        "topic": "Ray Optics",
        "exp": "1/F = 1/f1 + 1/f2 = 1/20 - 1/40 = 1/40 => F = +40 cm."
    },
    {
        "q": "The speed of light in a medium is 2 × 10⁸ m/s. The refractive index of the medium relative to vacuum is (c = 3 × 10⁸ m/s):",
        "opts": ["1.25", "1.33", "1.50", "1.75"],
        "ans": "2",
        "topic": "Ray Optics",
        "exp": "n = c / v = (3 × 10⁸) / (2 × 10⁸) = 1.50."
    },
    {
        "q": "In Young's double slit experiment, if the distance between the slits is reduced to half and the screen distance is doubled, the fringe width becomes:",
        "opts": ["Unchanged", "Doubled", "Halved", "4 times"],
        "ans": "3",
        "topic": "Wave Optics",
        "exp": "Fringe width β = λD/d. If D' = 2D and d' = d/2, β' = λ(2D)/(d/2) = 4 (λD/d) = 4β."
    },
    {
        "q": "The work function of a photosensitive metal is 2.5 eV. The threshold frequency for photoelectric emission is (h = 6.63 × 10⁻³⁴ J·s, 1 eV = 1.6 × 10⁻¹⁹ J):",
        "opts": ["3.0 × 10¹⁴ Hz", "6.0 × 10¹⁴ Hz", "7.5 × 10¹⁴ Hz", "9.0 × 10¹⁴ Hz"],
        "ans": "1",
        "topic": "Dual Nature of Radiation and Matter",
        "exp": "Work function Φ = 2.5 * 1.6×10⁻¹⁹ J = 4.0×10⁻¹⁹ J. ν₀ = Φ / h = (4.0×10⁻¹⁹) / (6.63×10⁻³⁴) ≈ 6.0 × 10¹⁴ Hz."
    },
    {
        "q": "The de Broglie wavelength of an electron accelerated through a potential difference of 100 V is approximately:",
        "opts": ["0.123 nm", "0.246 nm", "1.23 nm", "12.3 nm"],
        "ans": "0",
        "topic": "Dual Nature of Radiation and Matter",
        "exp": "λ = 1.227 / √V nm = 1.227 / √100 = 1.227 / 10 = 0.1227 nm ≈ 0.123 nm."
    },
    {
        "q": "The radius of the first Bohr orbit of a hydrogen atom is 0.53 Å. The radius of the second orbit (n = 2) is:",
        "opts": ["1.06 Å", "1.59 Å", "2.12 Å", "4.24 Å"],
        "ans": "2",
        "topic": "Atoms",
        "exp": "r_n = r₁ * n² = 0.53 Å * (2)² = 0.53 * 4 = 2.12 Å."
    },
    {
        "q": "The half-life of a radioactive isotope is 5 days. The fraction of the initial mass that remains undecayed after 20 days is:",
        "opts": ["1/4", "1/8", "1/16", "1/32"],
        "ans": "2",
        "topic": "Nuclei",
        "exp": "Number of half-lives n = 20 / 5 = 4. Remaining fraction = (1/2)⁴ = 1/16."
    },
    {
        "q": "In a p-n junction diode, the barrier potential for Silicon at room temperature is approximately:",
        "opts": ["0.1 V", "0.3 V", "0.7 V", "1.1 V"],
        "ans": "2",
        "topic": "Semiconductor Electronics",
        "exp": "The barrier potential for Silicon p-n junction is ~0.7 V (for Germanium it is ~0.3 V)."
    },
    {
        "q": "An ideal transformer has 500 primary turns and 50 secondary turns. If the input primary voltage is 220 V, the output secondary voltage is:",
        "opts": ["11 V", "22 V", "44 V", "110 V"],
        "ans": "1",
        "topic": "Alternating Current",
        "exp": "V_s / V_p = N_s / N_p => V_s = 220 * (50 / 500) = 22 V."
    },
    {
        "q": "A spring of force constant 400 N/m is stretched by 5 cm from its equilibrium position. The potential energy stored in the spring is:",
        "opts": ["0.5 J", "1.0 J", "2.0 J", "5.0 J"],
        "ans": "0",
        "topic": "Work, Energy and Power",
        "exp": "U = (1/2) k x² = 0.5 * 400 * (0.05)² = 200 * 0.0025 = 0.5 J."
    },
    {
        "q": "A particle executes Simple Harmonic Motion (SHM) with an amplitude of 10 cm and period of 2 s. The maximum velocity of the particle is:",
        "opts": ["5π cm/s", "10π cm/s", "20π cm/s", "40π cm/s"],
        "ans": "1",
        "topic": "Oscillations",
        "exp": "v_max = ω A = (2π / T) * A = (2π / 2) * 10 = 10π cm/s."
    },
    {
        "q": "A flywheel rotates at 300 rpm. Its angular speed in rad/s is:",
        "opts": ["5π rad/s", "10π rad/s", "20π rad/s", "30π rad/s"],
        "ans": "1",
        "topic": "System of Particles and Rotational Motion",
        "exp": "ω = 2π N / 60 = 2π * 300 / 60 = 10π rad/s."
    },
    {
        "q": "A uniform meter rule of mass 100 g is balanced on a fulcrum at the 40 cm mark by hanging a mass m at the 10 cm mark. The value of m is:",
        "opts": ["20 g", "33.3 g", "50 g", "100 g"],
        "ans": "1",
        "topic": "System of Particles and Rotational Motion",
        "exp": "Centre of gravity of meter rule is at 50 cm. Distance from fulcrum (40 cm) to CG (50 cm) = 10 cm. Distance from 10 cm mark to fulcrum (40 cm) = 30 cm. By principle of moments: m * 30 = 100 * 10 => m = 1000/30 = 33.3 g."
    },
    {
        "q": "The fundamental frequency of an open organ pipe of length 34 cm in air (speed of sound = 340 m/s) is:",
        "opts": ["250 Hz", "500 Hz", "750 Hz", "1000 Hz"],
        "ans": "1",
        "topic": "Waves",
        "exp": "Fundamental frequency f = v / (2 L) = 340 / (2 * 0.34) = 340 / 0.68 = 500 Hz."
    },
    {
        "q": "A sound wave of frequency 500 Hz travels with a speed of 350 m/s in air. The phase difference between two points separated by 17.5 cm along the wave path is:",
        "opts": ["π/4 rad", "π/2 rad", "π rad", "2π rad"],
        "ans": "1",
        "topic": "Waves",
        "exp": "Wavelength λ = v / f = 350 / 500 = 0.7 m = 70 cm. Phase diff Δφ = (2π / λ) * Δx = (2π / 70) * 17.5 = 2π / 4 = π/2 rad."
    },
    {
        "q": "The work done in blowing a soap bubble of radius 5 cm (surface tension of soap solution T = 0.03 N/m) is approximately:",
        "opts": ["1.88 × 10⁻³ J", "3.77 × 10⁻³ J", "7.54 × 10⁻³ J", "1.51 × 10⁻² J"],
        "ans": "1",
        "topic": "Mechanical Properties of Fluids",
        "exp": "A soap bubble has 2 free surfaces. Total area A = 2 * (4π r²) = 8π (0.05)² = 0.02π m². Work W = T * A = 0.03 * 0.02 * 3.1416 ≈ 1.88 × 10⁻³ J."
    },
    {
        "q": "An ideal gas undergoes an isothermal expansion from volume V to 3V at constant temperature T. The work done by the gas is:",
        "opts": ["nRT ln(3)", "3 nRT", "nRT (3 - 1)", "Zero"],
        "ans": "0",
        "topic": "Thermodynamics",
        "exp": "For isothermal process: W = nRT ln(V_final / V_initial) = nRT ln(3V/V) = nRT ln(3)."
    },
    {
        "q": "The Root Mean Square (RMS) speed of gas molecules at absolute temperature T is proportional to:",
        "opts": ["T", "T²", "√T", "1/√T"],
        "ans": "2",
        "topic": "Kinetic Theory of Gases",
        "exp": "v_rms = √(3RT/M) => v_rms is directly proportional to √T."
    },
    {
        "q": "The dimension of Planck's constant (h) is the same as that of:",
        "opts": ["Linear momentum", "Angular momentum", "Work", "Power"],
        "ans": "1",
        "topic": "Units and Measurements",
        "exp": "Dimension of h = [E/ν] = [M L² T⁻² / T⁻¹] = [M L² T⁻¹], which is identical to the dimension of angular momentum L = [r p] = [L * M L T⁻¹] = [M L² T⁻¹]."
    },
    {
        "q": "A copper wire is stretched to make it 0.1% longer. The percentage change in its resistance is approximately:",
        "opts": ["0.1%", "0.2%", "0.4%", "0.8%"],
        "ans": "1",
        "topic": "Current Electricity",
        "exp": "R = ρ L / A = ρ L² / Vol. For small changes: ΔR/R ≈ 2 (ΔL/L) = 2 * 0.1% = 0.2%."
    },
    {
        "q": "In a galvanometer of resistance 50 Ω, a shunt of 5 Ω is connected to convert it into an ammeter. The fraction of main current passing through the galvanometer is:",
        "opts": ["1/10", "1/11", "1/5", "10/11"],
        "ans": "1",
        "topic": "Moving Charges and Magnetism",
        "exp": "I_g / I = S / (G + S) = 5 / (50 + 5) = 5 / 55 = 1/11."
    },
    {
        "q": "The self-inductance of a coil in which a change of current of 2 A/s induces an emf of 10 V is:",
        "opts": ["2 H", "5 H", "10 H", "20 H"],
        "ans": "1",
        "topic": "Electromagnetic Induction",
        "exp": "e = L (dI/dt) => 10 = L * 2 => L = 5 H."
    },
    {
        "q": "An electromagnetic wave has an electric field vector E_0 = 30 V/m. The amplitude of the magnetic field vector B_0 is (c = 3 × 10⁸ m/s):",
        "opts": ["10⁻⁷ T", "3 × 10⁻⁷ T", "10⁻⁸ T", "9 × 10⁻⁸ T"],
        "ans": "0",
        "topic": "Electromagnetic Waves",
        "exp": "B_0 = E_0 / c = 30 / (3 × 10⁸) = 10⁻⁷ T."
    },
    {
        "q": "A astronomical telescope has an objective of focal length 100 cm and an eyepiece of focal length 5 cm. The magnifying power for normal adjustment is:",
        "opts": ["15", "20", "25", "105"],
        "ans": "1",
        "topic": "Ray Optics and Optical Instruments",
        "exp": "Magnifying power M = f_o / f_e = 100 / 5 = 20."
    },
    {
        "q": "In a Zener diode used as a voltage regulator, the Zener breakdown occurs due to:",
        "opts": ["Thermal excitation", "High electric field across thin depletion layer", "Low doping level", "Recombination of carriers"],
        "ans": "1",
        "topic": "Semiconductor Electronics",
        "exp": "Zener breakdown occurs in heavily doped p-n junctions with very thin depletion layers under strong electric field (~10⁶ V/m)."
    },
    {
        "q": "The boolean expression for an AND gate followed by a NOT gate is:",
        "opts": ["A + B", "A · B", "NOT(A · B)", "NOT(A + B)"],
        "ans": "2",
        "topic": "Semiconductor Electronics",
        "exp": "An AND gate followed by a NOT gate forms a NAND gate, whose output is Y = NOT(A · B)."
    }
]

batch_id = str(uuid.uuid4())
print(f"Seeding {len(PHYSICS_QUESTIONS)} authentic KCET Physics questions into DB...")

for item in PHYSICS_QUESTIONS:
    c.execute(
        """
        INSERT INTO questions (id, subject, question_text, options, correct_option, topic, explanation, generation_batch_id, source_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            "Physics",
            item["q"],
            json.dumps(item["opts"]),
            item["ans"],
            item["topic"],
            item["exp"],
            batch_id,
            "kcet_bank"
        )
    )

conn.commit()
print("Database seeding completed.")

# 2. Update FAISS Physics chunks and index
faiss_dir = Path("backend/data/faiss")
chunks_path = faiss_dir / "Physics.chunks.json"
index_path = faiss_dir / "Physics.index"

print("Updating Physics.chunks.json with real Physics textbook content...")

physics_chunks = [
    "Units and Measurements: SI base units are meter (m), kilogram (kg), second (s), ampere (A), kelvin (K), mole (mol), and candela (cd). Dimensional analysis uses [M], [L], [T], [I], [K]. Significant figures determine precision.",
    "Motion in a Straight Line: Kinematic equations for constant acceleration a: v = u + at, s = ut + 0.5 a t^2, v^2 = u^2 + 2as. Velocity is the rate of change of displacement v = ds/dt.",
    "Motion in a Plane: Vector addition uses triangle or parallelogram law. Projectile motion: Time of flight T = (2 u sin theta) / g, Maximum height H = (u^2 sin^2 theta) / (2g), Horizontal Range R = (u^2 sin 2theta) / g.",
    "Laws of Motion: Newton's first law defines inertia. Second law F = ma = dp/dt. Third law action and reaction are equal and opposite. Impulse I = F delta_t = delta_p. Friction f_s <= mu_s N.",
    "Work, Energy and Power: Work W = F . s = F s cos theta. Kinetic energy K = 0.5 m v^2. Potential energy U = mgh. Work-Energy Theorem: W_net = delta K. Power P = dW/dt = F . v.",
    "System of Particles and Rotational Motion: Center of mass r_cm = (sum m_i r_i) / M. Torque tau = r x F = I alpha. Angular momentum L = r x p = I omega. Moment of inertia I = sum m_i r_i^2.",
    "Gravitation: Newton's Law of Universal Gravitation F = G m1 m2 / r^2. Acceleration due to gravity g = G M / R^2. Altitude variation g' = g (1 - 2h/R). Escape velocity v_e = sqrt(2 G M / R).",
    "Mechanical Properties of Solids and Fluids: Young's modulus Y = stress / strain = (F/A) / (delta_L / L). Pascal's law: pressure applied to an enclosed fluid is transmitted undiminished. Bernoulli's principle P + 0.5 rho v^2 + rho g h = constant.",
    "Thermal Properties of Matter and Thermodynamics: Heat Q = m c delta_T. First law of thermodynamics dQ = dU + dW. Isothermal process T = constant, W = nRT ln(V2/V1). Adiabatic process Q = 0, P V^gamma = constant.",
    "Kinetic Theory of Gases and Oscillations: Pressure P = (1/3) n m v_rms^2. RMS speed v_rms = sqrt(3 R T / M). SHM displacement x = A sin(omega t + phi), acceleration a = -omega^2 x, period T = 2pi sqrt(m/k).",
    "Electric Charges and Fields: Coulomb's Law F = (1 / 4pi epsilon_0) (q1 q2 / r^2). Electric field E = F / q = (1 / 4pi epsilon_0) (q / r^2). Gauss's Law: electric flux phi = q_enclosed / epsilon_0.",
    "Electrostatic Potential and Capacitance: Potential V = W / q = (1 / 4pi epsilon_0) (q / r). Capacitance C = Q / V. Parallel plate capacitor C = epsilon_0 A / d. Energy stored U = 0.5 C V^2.",
    "Current Electricity: Ohm's Law V = I R. Resistivity R = rho L / A. Drift velocity v_d = e E tau / m. Kirchhoff's Current Law sum I = 0. Kirchhoff's Voltage Law sum V = 0.",
    "Moving Charges and Magnetism: Biot-Savart Law dB = (mu_0 / 4pi) (I dl sin theta / r^2). Force on moving charge F = q (v x B). Force on current wire F = I (L x B). Magnetic field at center of circular coil B = mu_0 N I / (2 R).",
    "Electromagnetic Induction and Alternating Current: Faraday's Law induced emf e = -N (d phi_B / dt). Lenz's Law gives direction of induced current. AC voltage V = V_0 sin(omega t), V_rms = V_0 / sqrt(2). Inductive reactance X_L = omega L, Capacitive reactance X_C = 1 / (omega C). Impedance Z = sqrt(R^2 + (X_L - X_C)^2).",
    "Ray Optics and Wave Optics: Snells Law n1 sin i = n2 sin r. Lens formula 1/f = 1/v - 1/u. Power P = 1/f. Youngs double slit fringe width beta = lambda D / d. Diffraction minima d sin theta = m lambda.",
    "Dual Nature of Radiation and Matter: Photoelectric equation K_max = h nu - phi_0. Threshold frequency nu_0 = phi_0 / h. de Broglie wavelength lambda = h / p = h / (m v) = 1.227 / sqrt(V) nm for electron.",
    "Atoms and Nuclei: Bohr radii r_n = n^2 h^2 epsilon_0 / (pi m e^2). Energy levels E_n = -13.6 / n^2 eV. Radioactivity decay law N(t) = N_0 e^(-lambda t). Half life T_half = ln(2) / lambda.",
    "Semiconductor Electronics: Intrinsic semiconductor n_i^2 = n_e n_h. P-N junction forward bias reduces depletion width, reverse bias increases depletion width. Transistor currents I_E = I_B + I_C. Logic gates AND, OR, NOT, NAND, NOR."
]

with open(chunks_path, "w", encoding="utf-8") as f:
    json.dump(physics_chunks, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(physics_chunks)} physics text chunks to {chunks_path}.")

# Re-create FAISS index for Physics
try:
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vecs = embedder.encode(physics_chunks, show_progress_bar=False).astype("float32")
    dim = vecs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vecs)
    faiss.write_index(index, str(index_path))
    print(f"Successfully re-indexed {len(physics_chunks)} chunks into {index_path}.")
except Exception as e:
    print(f"SentenceTransformer not available for FAISS index rebuild: {e}")

print("Physics data fix complete!")
