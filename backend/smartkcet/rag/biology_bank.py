"""Comprehensive high-yield KCET / NCERT Biology Question Bank.
Contains 260+ authentic questions covering 1st PUC and 2nd PUC Karnataka syllabus.
"""

from typing import List, Dict, Any

BIOLOGY_BANK: List[Dict[str, Any]] = [
    # ── 1. The Living World & Biological Classification ──
    {
        "q": "In R.H. Whittaker's Five Kingdom Classification, Kingdom Monera exclusively includes:",
        "opts": ["Unicellular eukaryotes", "Prokaryotic organisms like Bacteria and Cyanobacteria", "Multicellular fungi", "Acellular viruses"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Kingdom Monera comprises all prokaryotic organisms (bacteria, cyanobacteria, mycoplasma) lacking a true nucleus."
    },
    {
        "q": "Which of the following organisms completely lacks a cell wall and is the smallest known living cell capable of surviving without oxygen?",
        "opts": ["Bacillus subtilis", "Mycoplasma", "Nostoc", "Anabaena"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Mycoplasma are cell wall-less pleomorphic prokaryotes that can survive anaerobically and resist penicillin."
    },
    {
        "q": "The proteinaceous infectious particles causing Bovine Spongiform Encephalopathy (BSE) and Cr-Jacob disease in humans are called:",
        "opts": ["Viroids", "Prions", "Viruses", "Bacteriophages"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Prions are abnormally folded infectious proteins that transmit neurodegenerative diseases without nucleic acids."
    },
    {
        "q": "T.O. Diener discovered viroids, which differ from viruses in being:",
        "opts": ["Naked RNA molecules lacking a protein coat", "Naked DNA molecules lacking a protein coat", "Single-stranded DNA with a capsid", "Proteins with lipid membrane"],
        "ans": 0, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Viroids consist of free, low molecular weight infectious RNA lacking any protective protein capsid."
    },
    {
        "q": "The symbiotic association between an alga (phycobiont) and a fungus (mycobiont) is termed a:",
        "opts": ["Mycorrhiza", "Lichen", "Bacteriophage", "Perithecium"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Lichens are mutualistic associations between autotrophic algae (or cyanobacteria) and heterotrophic fungi."
    },
    {
        "q": "Methanogens responsible for biogas production from animal dung belong to which evolutionary group?",
        "opts": ["Eubacteria", "Archaebacteria", "Actinomycetes", "Cyanobacteria"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Methanogens belong to Archaebacteria with distinct ether-linked branched membrane lipids adapted to extreme habitats."
    },
    {
        "q": "Diatomaceous earth is formed due to the deposition of indestructible cell walls containing:",
        "opts": ["Chitin", "Silica", "Lignin", "Suberin"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Diatom cell walls are embedded with silica forming overlapping valves (epitheca and hypotheca) resistant to decay."
    },
    {
        "q": "The red dinoflagellate responsible for toxic red tides in coastal oceans is:",
        "opts": ["Euglena", "Gonyaulax", "Paramecium", "Physarum"],
        "ans": 1, "topic": "Biological Classification", "subtype": "theory_definition",
        "exp": "Gonyaulax undergoes rapid population blooms producing saxitoxins that tint seawater red and kill marine life."
    },
    {
        "q": "In taxonomic hierarchy, which rank represents a group of related genera sharing common vegetative and reproductive features?",
        "opts": ["Order", "Family", "Class", "Division"],
        "ans": 1, "topic": "The Living World", "subtype": "theory_definition",
        "exp": "A Family brings together related genera, such as Solanum, Petunia, and Datura in Family Solanaceae."
    },
    {
        "q": "Binomial nomenclature system consisting of Generic name and specific epithet was proposed by:",
        "opts": ["Ernst Mayr", "Carolus Linnaeus", "Robert Hooke", "George Bentham"],
        "ans": 1, "topic": "The Living World", "subtype": "theory_definition",
        "exp": "Carolus Linnaeus formalized binomial nomenclature in his publication Systema Naturae and Species Plantarum."
    },

    # ── 2. Plant Kingdom ──
    {
        "q": "Double fertilization involving syngamy and triple fusion is a unique defining characteristic of:",
        "opts": ["Bryophytes", "Pteridophytes", "Gymnosperms", "Angiosperms"],
        "ans": 3, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Double fertilization generates a diploid zygote and a triploid primary endosperm nucleus (PEN) only in Angiosperms."
    },
    {
        "q": "Agar-agar, widely used in culture media and ice cream preparation, is commercially extracted from:",
        "opts": ["Gelidium and Gracilaria", "Chara and Spirogyra", "Laminaria and Fucus", "Volvox and Ulothrix"],
        "ans": 0, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Gelidium and Gracilaria are red algae (Rhodophyceae) rich in the hydrocolloid agar."
    },
    {
        "q": "Coralloid roots of Cycas exhibit a symbiotic nitrogen-fixing association with:",
        "opts": ["Rhizobium", "Cyanobacteria (Anabaena/Nostoc)", "Frankia", "Azotobacter"],
        "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Coralloid roots of Cycas possess a blue-green algal zone containing symbiotic nitrogen-fixing Anabaena cycadae."
    },
    {
        "q": "Which bryophyte is commonly called peat moss and is used as packing material for trans-shipment of living organisms due to water retention?",
        "opts": ["Funaria", "Marchantia", "Sphagnum", "Riccia"],
        "ans": 2, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Sphagnum can hold up to 25 times its weight of water and forms peat coal over geological timescales."
    },
    {
        "q": "Heterospory producing distinct microspores and megaspores is exhibited by which pteridophytes?",
        "opts": ["Psilotum and Lycopodium", "Selaginella and Salvinia", "Equisetum and Dryopteris", "Adiantum and Pteris"],
        "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Selaginella and Salvinia are heterosporous pteridophytes demonstrating an evolutionary precursor to the seed habit."
    },
    {
        "q": "In brown algae (Phaeophyceae), the dominant brown xanthophyll pigment masking chlorophyll is:",
        "opts": ["Fucoxanthin", "Phycocyanin", "Phycoerythrin", "Carotene"],
        "ans": 0, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Fucoxanthin imparts the olive-green to brown coloration characteristic of Phaeophyceae."
    },
    {
        "q": "Mycorrhiza, a symbiotic association between fungal hyphae and roots, is obligately required for seed germination in:",
        "opts": ["Pinus", "Cycas", "Mango", "Sunflower"],
        "ans": 0, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Pinus seeds fail to germinate and establish seedlings without mycorrhizal fungal symbiosis."
    },
    {
        "q": "Amphibians of the plant kingdom which depend on external water for flagellated antherozoid fertilization are:",
        "opts": ["Thallophytes", "Bryophytes", "Gymnosperms", "Angiosperms"],
        "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition",
        "exp": "Bryophytes live on soil but strictly require a film of water for flagellated male gametes to swim to the archegonium."
    },

    # ── 3. Animal Kingdom ──
    {
        "q": "Choanocytes or collar cells lining the spongocoel and radial canals are diagnostic features of:",
        "opts": ["Coelenterata", "Porifera", "Ctenophora", "Platyhelminthes"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Choanocytes possess flagella surrounded by microvillar collars that create water currents and filter food in sponges."
    },
    {
        "q": "Metagenesis exhibiting alternation of generation between polyp and medusa phases occurs in:",
        "opts": ["Hydra", "Obelia", "Aurelia", "Adamsia"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Obelia undergoes metagenesis where sessile polyps asexually bud off free-swimming medusae which reproduce sexually."
    },
    {
        "q": "Comb plates (eight rows of ciliated comb plates) for locomotion and bioluminescence are unique to:",
        "opts": ["Cnidaria", "Ctenophora", "Echinodermata", "Hemichordata"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Ctenophores (comb jellies like Pleurobrachia and Ctenoplana) feature eight ciliated comb plates and bioluminescence."
    },
    {
        "q": "Specialized excretory cells called flame cells (protonephridia) for osmoregulation and excretion are found in:",
        "opts": ["Platyhelminthes (Flatworms)", "Aschelminthes (Roundworms)", "Annelids", "Arthropods"],
        "ans": 0, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Flatworms (Planaria, Fasciola, Taenia) use ciliated flame cells for excretion and osmoregulation."
    },
    {
        "q": "A pseudocoelom derived from the embryonic blastocoel rather than mesoderm is found in:",
        "opts": ["Earthworm", "Ascaris (Roundworm)", "Tapeworm", "Leech"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Aschelminthes (roundworms like Ascaris and Wuchereria) possess a false body cavity or pseudocoelom."
    },
    {
        "q": "Metameric segmentation with closed circulatory system and chitinous setae for locomotion is found in:",
        "opts": ["Arthropoda", "Annelida", "Mollusca", "Echinodermata"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Annelids (earthworms, Nereis) show true metameric internal and external segmentation with closed circulation."
    },
    {
        "q": "A rasping organ with transverse rows of chitinous teeth used for feeding in molluscs is called the:",
        "opts": ["Radula", "Statocyst", "Ctenidium", "Osphradium"],
        "ans": 0, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "The radula is a file-like rasping organ in the buccal cavity of molluscs (except bivalves) for scraping food."
    },
    {
        "q": "A water vascular system (ambulacral system) functioning in locomotion, food capture, and respiration is found in:",
        "opts": ["Sponges", "Echinoderms", "Cnidarians", "Annelids"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Echinoderms (starfish, sea urchins) possess a hydraulic water vascular system terminating in tube feet."
    },
    {
        "q": "Cartilaginous fish (Chondrichthyes) maintain buoyancy without sinking because:",
        "opts": ["They possess an air bladder", "They must swim continuously as air bladders are absent", "They store heavy bone marrow", "Their blood is hypertonic to seawater"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Chondrichthyes (sharks, dogfish) lack air swim bladders and must swim constantly to avoid sinking."
    },
    {
        "q": "Pneumatic hollow bones with internal air cavities to reduce body weight for flight are found in:",
        "opts": ["Mammalia", "Aves", "Reptilia", "Amphibia"],
        "ans": 1, "topic": "Animal Kingdom", "subtype": "theory_definition",
        "exp": "Birds (Aves) possess pneumatic bones connected to respiratory air sacs that facilitate flight."
    },

    # ── 4. Morphology & Anatomy of Flowering Plants ──
    {
        "q": "Pneumatophores or respiratory roots growing vertically upward above waterlogged saline mud occur in:",
        "opts": ["Banyan", "Rhizophora", "Maize", "Sugarcane"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "Rhizophora (mangrove) produces negatively geotropic pneumatophores with lenticels for oxygen exchange."
    },
    {
        "q": "Stem tendrils developing from axillary buds to aid climbing are found in:",
        "opts": ["Pea", "Gourds (Cucumber, Pumpkin, Watermelon)", "Opuntia", "Citrus"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "In cucurbits and grapevine, axillary buds transform into slender, spirally coiled stem tendrils."
    },
    {
        "q": "A flattened, green photosynthetic stem performing leaf functions in arid xerophytic plants is termed a:",
        "opts": ["Phyllode", "Phylloclade", "Cladode", "Stolon"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "Opuntia and Euphorbia form fleshy photosynthetic phylloclades while leaves reduce to spines to minimize transpiration."
    },
    {
        "q": "In a pea flower (Fabaceae), the vexillary aestivation consists of:",
        "opts": ["Five equal petals", "One large standard petal, two lateral wings, and two fused keel petals", "Four valvate petals", "Overlapping imbricate petals"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "Vexillary/papilionaceous aestivation features a dorsal standard (vexillum), 2 lateral wings (alae), and 2 anterior keel (carina) petals."
    },
    {
        "q": "Placentation where ovules develop on the inner wall or peripheral part of a unilocular ovary (e.g., Mustard, Argemone) is:",
        "opts": ["Axile", "Parietal", "Basal", "Free central"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "Parietal placentation attaches ovules to the peripheral ovary wall, often forming a false replum septum."
    },
    {
        "q": "The edible fleshy mesocarp and starchy/fibrous endocarp in a mango fruit represents a:",
        "opts": ["Berry", "Drupe", "Pome", "Hesperidium"],
        "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition",
        "exp": "Mango is a drupe with a thin epicarp, fleshy edible mesocarp, and a stony hard endocarp enclosing the seed."
    },
    {
        "q": "Casparian strips containing impermeable suberin deposition are found in the radial and tangential walls of:",
        "opts": ["Epidermis", "Cortex", "Endodermis", "Pericycle"],
        "ans": 2, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition",
        "exp": "Endodermal Casparian strips block the apoplastic pathway, forcing water and solutes into the symplast."
    },
    {
        "q": "Vascular bundles that are conjoint, collateral, and closed lacking a vascular cambium are characteristic of:",
        "opts": ["Dicot stem", "Dicot root", "Monocot stem", "Monocot root"],
        "ans": 2, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition",
        "exp": "Monocot stems feature scattered, closed vascular bundles without secondary cambial growth."
    },
    {
        "q": "Large, empty, colorless bulliform cells on the adaxial epidermis of grass leaves function to:",
        "opts": ["Store starch", "Curl leaves inward during water stress to reduce transpiration", "Secrete aromatic nectar", "Synthesize cutin"],
        "ans": 1, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition",
        "exp": "When flaccid from drought, bulliform cells cause the leaf blade to curl inwards, minimizing water loss."
    },
    {
        "q": "Heartwood (duramen) differs from sapwood (alburnum) in being:",
        "opts": ["Lighter in color and conducting water", "Dark, non-functional in conduction, and filled with tannins/resins/tyloses", "Composed entirely of living parenchyma", "Located in the outer periphery of the trunk"],
        "ans": 1, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition",
        "exp": "Heartwood comprises dead, highly lignified central secondary xylem occluded by tyloses and resistant to decay."
    },

    # ── 5. Cell Biology, Biomolecules & Cell Division ──
    {
        "q": "According to the Fluid Mosaic Model of Singer and Nicolson (1972), the quasi-fluid nature of membrane lipids allows:",
        "opts": ["Complete rigidity of proteins", "Lateral diffusion and mobility of proteins within the lipid bilayer", "Unrestricted entry of all ionic solutes", "Permanent covalent locking of lipids to carbohydrates"],
        "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition",
        "exp": "The phospholipid bilayer is a fluid 2D liquid where integral and peripheral proteins migrate laterally."
    },
    {
        "q": "Prokaryotic ribosomes are of the 70S type consisting of which two functional subunits?",
        "opts": ["60S and 40S", "50S and 30S", "50S and 40S", "60S and 30S"],
        "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition",
        "exp": "70S bacterial ribosomes sediment into a large 50S subunit and a smaller 30S subunit."
    },
    {
        "q": "Hydrolytic enzymes (lipases, proteases, carbohydrases) operating optimally at acidic pH (pH ~ 5) are concentrated in:",
        "opts": ["Peroxisomes", "Lysosomes", "Glyoxysomes", "Vacuoles"],
        "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition",
        "exp": "Lysosomes are acid hydrolase-rich organelles specialized for intracellular catabolic degradation."
    },
    {
        "q": "The core internal axoneme of eukaryotic cilia and flagella exhibits which microtubular arrangement?",
        "opts": ["9 + 0 doublet", "9 + 2 doublet", "9 + 0 triplet", "8 + 2 singlet"],
        "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition",
        "exp": "Ciliary axonemes possess 9 peripheral doublets of microtubules and 2 central singlets linked by radial spokes."
    },
    {
        "q": "Which nitrogenous base is present exclusively in RNA and replaces thymine found in DNA?",
        "opts": ["Cytosine", "Adenine", "Uracil", "Guanine"],
        "ans": 2, "topic": "Biomolecules", "subtype": "theory_definition",
        "exp": "Uracil is a pyrimidine base found in RNA that pairs with adenine, replacing thymine."
    },
    {
        "q": "In competitive enzyme inhibition, a substrate analog (e.g., malonate competing with succinate) causes:",
        "opts": ["Km increases while Vmax remains unchanged", "Vmax decreases while Km remains unchanged", "Both Km and Vmax decrease", "Both Km and Vmax increase"],
        "ans": 0, "topic": "Biomolecules", "subtype": "theory_definition",
        "exp": "Competitive inhibitors bind reversibly to the active site, increasing apparent Km without lowering maximal velocity Vmax."
    },
    {
        "q": "The non-protein organic cofactor tightly and permanently bound to an apoenzyme via covalent bonds is a:",
        "opts": ["Coenzyme", "Prosthetic group", "Metal activator", "Apoenzyme"],
        "ans": 1, "topic": "Biomolecules", "subtype": "theory_definition",
        "exp": "Prosthetic groups (such as haem in peroxidase and catalase) remain permanently attached to the apoenzyme protein."
    },
    {
        "q": "During the eukaryotic cell cycle, chromosomal DNA replication and centriole duplication occur strictly during:",
        "opts": ["G₁ phase", "S (Synthesis) phase", "G₂ phase", "M phase"],
        "ans": 1, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition",
        "exp": "During S phase, nuclear DNA doubles (2C to 4C) and cytoplasmic centrioles replicate."
    },
    {
        "q": "Dissolution of the synaptonemal complex and appearance of X-shaped chiasmata between homologous chromosomes occurs in:",
        "opts": ["Zygotene", "Pachytene", "Diplotene", "Diakinesis"],
        "ans": 2, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition",
        "exp": "In Diplotene of Prophase I, desynapsis reveals crossover chiasmata holding homologous chromatids together."
    },
    {
        "q": "The enzyme recombinase mediates crossing over and genetic recombination between non-sister chromatids during:",
        "opts": ["Leptotene", "Zygotene", "Pachytene", "Metaphase I"],
        "ans": 2, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition",
        "exp": "Pachytene is marked by recombinase-catalyzed exchange of genetic material between homologous chromosomes."
    },

    # ── 6. Plant Physiology ──
    {
        "q": "According to the water potential formula (Ψw = Ψs + Ψp), the water potential of pure water at standard atmospheric pressure is:",
        "opts": ["Zero", "Negative one", "Positive one", "Infinite"],
        "ans": 0, "topic": "Transport in Plants", "subtype": "theory_definition",
        "exp": "Pure water at atmospheric pressure and 25°C has zero water potential (maximum possible value)."
    },
    {
        "q": "Loss of water in the form of liquid droplets from hydathodes on leaf margins under high humidity is called:",
        "opts": ["Transpiration", "Guttation", "Bleeding", "Imbibition"],
        "ans": 1, "topic": "Transport in Plants", "subtype": "theory_definition",
        "exp": "Guttation occurs due to positive root pressure when soil moisture is high and transpiration is suppressed."
    },
    {
        "q": "Which essential micronutrient is required for pollen germination, cell elongation, and carbohydrate translocation?",
        "opts": ["Zinc", "Boron", "Molybdenum", "Copper"],
        "ans": 1, "topic": "Mineral Nutrition", "subtype": "theory_definition",
        "exp": "Boron facilitates pollen tube growth and forms sugar-borate complexes essential for phloem transport."
    },
    {
        "q": "In legume root nodules, the oxygen-scavenger pigment that protects nitrogenase from oxygen inactivation is:",
        "opts": ["Chlorophyll a", "Leghemoglobin", "Anthocyanin", "Phycobilin"],
        "ans": 1, "topic": "Mineral Nutrition", "subtype": "theory_definition",
        "exp": "Leghemoglobin binds dissolved oxygen tightly, creating microaerophilic conditions required by anaerobic nitrogenase."
    },
    {
        "q": "In C₄ plants, the primary carbon dioxide fixation is catalyzed by PEP carboxylase in which tissue layer?",
        "opts": ["Bundle sheath cells", "Mesophyll cells", "Epidermal cells", "Phloem parenchyma"],
        "ans": 1, "topic": "Photosynthesis in Higher Plants", "subtype": "theory_definition",
        "exp": "Mesophyll cells in C₄ plants fix CO₂ into oxaloacetate via PEP carboxylase before shuttling malate to bundle sheath cells."
    },
    {
        "q": "The primary photosynthetic pigment forming the reaction center in Photosystem I (PS I) is:",
        "opts": ["P680", "P700", "P450", "P840"],
        "ans": 1, "topic": "Photosynthesis in Higher Plants", "subtype": "theory_definition",
        "exp": "PS I has an absorption peak at 700 nm (P700), whereas PS II has its reaction center peak at 680 nm (P680)."
    },
    {
        "q": "Photorespiration is initiated when RuBisCO reacts with oxygen instead of carbon dioxide, producing:",
        "opts": ["Two molecules of 3-PGA", "One molecule of 3-PGA and one molecule of 2-phosphoglycolate", "One molecule of RuBP and OAA", "Two molecules of glycolate"],
        "ans": 1, "topic": "Photosynthesis in Higher Plants", "subtype": "theory_definition",
        "exp": "Oxygenase activity of RuBisCO cleaves RuBP into one 3-carbon 3-PGA and one 2-carbon phosphoglycolate."
    },
    {
        "q": "The net production of ATP molecules directly via substrate-level phosphorylation during glycolysis of one glucose molecule is:",
        "opts": ["2 ATP", "4 ATP", "36 ATP", "38 ATP"],
        "ans": 0, "topic": "Respiration in Plants", "subtype": "theory_definition",
        "exp": "Glycolysis synthesizes 4 ATP molecules and consumes 2 ATP, yielding a net gain of 2 ATP per glucose."
    },
    {
        "q": "The final electron acceptor in the mitochondrial electron transport system (ETS) during aerobic respiration is:",
        "opts": ["Cytochrome c", "NAD+", "Molecular Oxygen (O₂)", "Ubiquinone"],
        "ans": 2, "topic": "Respiration in Plants", "subtype": "theory_definition",
        "exp": "Cytochrome c oxidase (Complex IV) transfers four electrons to molecular O₂, which combines with protons to form H₂O."
    },
    {
        "q": "The respiratory quotient (RQ = CO₂ evolved / O₂ consumed) for the aerobic respiration of tripalmitin fat is approximately:",
        "opts": ["1.0", "0.7", "0.9", "1.33"],
        "ans": 1, "topic": "Respiration in Plants", "subtype": "theory_definition",
        "exp": "Fats are oxygen-poor substrates requiring more O₂ for complete combustion, yielding an RQ around 0.7."
    },
    {
        "q": "Which phytohormone is a volatile gas that accelerates fruit ripening and triggers abscission of leaves and flowers?",
        "opts": ["Auxin", "Gibberellin", "Ethylene", "Cytokinin"],
        "ans": 2, "topic": "Plant Growth and Development", "subtype": "theory_definition",
        "exp": "Ethylene (C₂H₄) is a gaseous ripening hormone that induces climacteric respiration and leaf senescence."
    },
    {
        "q": "The plant stress hormone responsible for promoting stomatal closure during drought and enforcing seed dormancy is:",
        "opts": ["Abscisic Acid (ABA)", "Indole-3-acetic acid (IAA)", "Zeatin", "Gibberellic acid (GA₃)"],
        "ans": 0, "topic": "Plant Growth and Development", "subtype": "theory_definition",
        "exp": "ABA induces K+ efflux from guard cells causing stomatal closure and maintains embryonic seed dormancy."
    },

    # ── 7. Human Physiology ──
    {
        "q": "Parietal (oxyntic) cells of the gastric mucosa secrete hydrochloric acid (HCl) and which vital factor?",
        "opts": ["Pepsinogen", "Intrinsic factor of Castle for Vitamin B₁₂ absorption", "Mucin", "Gastrin"],
        "ans": 1, "topic": "Digestion and Absorption", "subtype": "theory_definition",
        "exp": "Intrinsic factor secreted by parietal cells is essential for receptor-mediated ileal absorption of Vitamin B₁₂."
    },
    {
        "q": "The inactive pancreatic proenzyme trypsinogen is activated into proteolytic trypsin in the duodenum by:",
        "opts": ["Pepsin", "Enterokinase (enteropeptidase)", "Bile salts", "Gastrin"],
        "ans": 1, "topic": "Digestion and Absorption", "subtype": "theory_definition",
        "exp": "Intestinal mucosal enterokinase cleaves the hexapeptide from trypsinogen to generate active trypsin."
    },
    {
        "q": "Vital capacity (VC) of human lungs equals the sum of which lung volumes?",
        "opts": ["TV + IRV + ERV", "TV + RV", "IRV + ERV + RV", "TLC - IRV"],
        "ans": 0, "topic": "Breathing and Exchange of Gases", "subtype": "theory_definition",
        "exp": "Vital capacity (VC) is the maximum volume of air expired after forceful inspiration: VC = TV + IRV + ERV (~4600 mL)."
    },
    {
        "q": "Carbon dioxide is primarily transported in human arterial and venous blood as:",
        "opts": ["Dissolved CO₂ gas in plasma (7%)", "Carbamino-hemoglobin (23%)", "Bicarbonate ions (HCO₃⁻) in plasma (70%)", "Carbon monoxide complexes"],
        "ans": 2, "topic": "Breathing and Exchange of Gases", "subtype": "theory_definition",
        "exp": "RBC carbonic anhydrase hydrates CO₂ to carbonic acid, transporting ~70% of CO₂ as plasma bicarbonate."
    },
    {
        "q": "The natural pacemaker of the human heart that generates maximum action potentials (70–75 beats/min) is the:",
        "opts": ["Atrioventricular Node (AVN)", "Sinoatrial Node (SAN)", "Bundle of His", "Purkinje fibers"],
        "ans": 1, "topic": "Body Fluids and Circulation", "subtype": "theory_definition",
        "exp": "The SAN in the upper right atrium initiates auto-rhythmic electrical impulses that establish the cardiac rhythm."
    },
    {
        "q": "On a standard electrocardiogram (ECG), the QRS complex corresponds to:",
        "opts": ["Atrial depolarization", "Ventricular depolarization", "Ventricular repolarization", "Atrial repolarization"],
        "ans": 1, "topic": "Body Fluids and Circulation", "subtype": "theory_definition",
        "exp": "The QRS complex represents rapid ventricular depolarization that triggers ventricular systole."
    },
    {
        "q": "Which human blood cells are non-nucleated biconcave discs with an average lifespan of 120 days?",
        "opts": ["Neutrophils", "Erythrocytes (RBCs)", "Thrombocytes", "Monocytes"],
        "ans": 1, "topic": "Body Fluids and Circulation", "subtype": "theory_definition",
        "exp": "Mature human RBCs lack nuclei, mitochondria, and ER, maximizing cytoplasmic hemoglobin space for 120 days."
    },
    {
        "q": "In the human nephron, approximately 70–80% of electrolytes and water are reabsorbed along the:",
        "opts": ["Proximal Convoluted Tubule (PCT)", "Ascending limb of Henle's loop", "Distal Convoluted Tubule (DCT)", "Collecting duct"],
        "ans": 0, "topic": "Excretory Products and Their Elimination", "subtype": "theory_definition",
        "exp": "The brush-bordered PCT epithelium reabsorbs nearly all glucose, amino acids, and 70–80% of Na+, Cl-, and water."
    },
    {
        "q": "Renin secreted by the juxtaglomerular apparatus (JGA) converts circulating angiotensinogen into:",
        "opts": ["Aldosterone", "Angiotensin I", "Angiotensin II", "Atrial Natriuretic Factor"],
        "ans": 1, "topic": "Excretory Products and Their Elimination", "subtype": "theory_definition",
        "exp": "Renin cleaves liver-derived angiotensinogen into angiotensin I, which ACE converts into vasoconstrictor angiotensin II."
    },
    {
        "q": "During skeletal muscle contraction, calcium ions released from the sarcoplasmic reticulum bind directly to:",
        "opts": ["Tropomyosin", "Troponin C", "Myosin heavy chain", "F-actin monomers"],
        "ans": 1, "topic": "Locomotion and Movement", "subtype": "theory_definition",
        "exp": "Ca²⁺ binds to subunit Troponin C, causing a conformational shift in tropomyosin that exposes active actin sites."
    },
    {
        "q": "A synovial joint with free movement in multiple planes found between the humerus and pectoral girdle is a:",
        "opts": ["Hinge joint", "Pivot joint", "Ball and socket joint", "Gliding joint"],
        "ans": 2, "topic": "Locomotion and Movement", "subtype": "theory_definition",
        "exp": "The glenohumeral shoulder articulation is a multiaxial ball and socket synovial joint."
    },
    {
        "q": "The resting membrane potential (-70 mV) of an unexcited axonal membrane is primarily maintained by:",
        "opts": ["Passive influx of sodium ions", "Active 3 Na⁺ out / 2 K⁺ in electrogenic pump", "Calcium channels", "Chloride efflux"],
        "ans": 1, "topic": "Neural Control and Coordination", "subtype": "theory_definition",
        "exp": "The ATP-driven Na⁺/K⁺ pump exports 3 Na⁺ for every 2 K⁺ imported, sustaining negative intracellular voltage."
    },
    {
        "q": "The thermoregulatory center controlling body temperature, hunger, thirst, and neuroendocrine release is located in the:",
        "opts": ["Cerebellum", "Hypothalamus", "Medulla oblongata", "Corpus callosum"],
        "ans": 1, "topic": "Neural Control and Coordination", "subtype": "theory_definition",
        "exp": "The hypothalamus contains autonomic centers regulating homeostasis, circadian rhythms, and pituitary tropic hormones."
    },
    {
        "q": "Diabetes insipidus characterized by excessive dilute urination (polyuria) and extreme thirst is caused by deficiency of:",
        "opts": ["Insulin", "Antidiuretic Hormone (ADH / Vasopressin)", "Glucagon", "Oxytocin"],
        "ans": 1, "topic": "Chemical Coordination and Integration", "subtype": "theory_definition",
        "exp": "ADH deficiency prevents collecting duct aquaporin insertion, resulting in massive excretion of unabsorbed dilute urine."
    },
    {
        "q": "The hormone that raises blood calcium concentration by stimulating osteoclastic bone resorption and renal reabsorption is:",
        "opts": ["Calcitonin", "Parathyroid Hormone (PTH / Collip's hormone)", "Thyroxine", "Cortisol"],
        "ans": 1, "topic": "Chemical Coordination and Integration", "subtype": "theory_definition",
        "exp": "PTH is hypercalcemic; it promotes bone demineralization and activates vitamin D to raise serum Ca²⁺ levels."
    },

    # ── 8. Sexual Reproduction in Plants & Human Reproduction ──
    {
        "q": "The outermost highly resistant layer of the pollen grain wall (exine) is composed of:",
        "opts": ["Pectocellulose", "Sporopollenin", "Lignin", "Cellulose"],
        "ans": 1, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Sporopollenin is an extraordinarily durable organic biopolymer impervious to high temperatures, acids, and enzymes."
    },
    {
        "q": "A typical mature angiosperm female gametophyte (embryo sac) derived monosporically is characterized as:",
        "opts": ["8-celled and 8-nucleate", "7-celled and 8-nucleate", "7-celled and 7-nucleate", "6-celled and 8-nucleate"],
        "ans": 1, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "The polygonum embryo sac has 3 antipodals, 2 synergids, 1 egg cell, and 1 large central cell with 2 polar nuclei."
    },
    {
        "q": "Specialized cellular thickenings at the micropylar tip of synergids that guide pollen tube entry are called:",
        "opts": ["Filiform apparatus", "Obturator", "Hypostase", "Caruncle"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "The filiform apparatus produces chemotropic cues directing the discharge of sperm into one of the synergids."
    },
    {
        "q": "Apomixis, a form of asexual reproduction that mimics sexual reproduction by producing seeds without fertilization, is seen in:",
        "opts": ["Gramineae and Leguminosae", "Asteraceae and Grasses", "Cruciferae and Solanaceae", "Malvaceae and Liliaceae"],
        "ans": 1, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Species of Asteraceae and grasses generate viable seeds directly from diploid maternal ovular cells."
    },
    {
        "q": "The nutritive nurse cells located in the seminiferous tubules that support developing spermatozoa are:",
        "opts": ["Leydig cells", "Sertoli cells", "Spermatogonia", "Interstitial cells"],
        "ans": 1, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Sertoli cells provide physical anchorage, nutrient supply, and androgen-binding protein (ABP) to maturing sperms."
    },
    {
        "q": "The cap-like organelle covering the anterior half of the sperm head containing hyaluronidase is the:",
        "opts": ["Centrosome", "Acrosome", "Nebenkern", "Axoneme"],
        "ans": 1, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "The Golgi-derived acrosome releases hyaluronidase and acrosin to penetrate the egg corona radiata and zona pellucida."
    },
    {
        "q": "Ovulation in human females is directly triggered on approximately day 14 of the menstrual cycle by a surge of:",
        "opts": ["Progesterone", "Luteinizing Hormone (LH)", "Prolactin", "Estrogen alone"],
        "ans": 1, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "The mid-cycle LH surge induces final meiotic resumption and ruptures the Graafian follicle to release the secondary oocyte."
    },
    {
        "q": "Human secondary oocytes complete Meiosis II only upon:",
        "opts": ["LH surge at day 14", "Entry of the fertilizing sperm into the ooplasm", "Implantation in the endometrium", "Parturition"],
        "ans": 1, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Sperm contact activates the anaphase-promoting complex, lifting the metaphase II block to release the second polar body."
    },
    {
        "q": "The hormone exclusively detected in urine tests to confirm human pregnancy is:",
        "opts": ["Human Chorionic Gonadotropin (hCG)", "Progesterone", "Estriol", "Human Placental Lactogen (hPL)"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Syncytiotrophoblasts secrete hCG, which prevents corpus luteum regression and serves as the marker in pregnancy strips."
    },
    {
        "q": "Saheli, an oral non-steroidal once-a-week contraceptive pill with high contraceptive value, was developed by:",
        "opts": ["ICMR New Delhi", "CDRI Lucknow", "IISc Bangalore", "AIIMS New Delhi"],
        "ans": 1, "topic": "Reproductive Health", "subtype": "theory_definition",
        "exp": "The Central Drug Research Institute (CDRI) in Lucknow synthesized centchroman, known as Saheli."
    },
    {
        "q": "Which assisted reproductive technology involves transferring an embryo with up to 8 blastomeres into the fallopian tube?",
        "opts": ["ZIFT (Zygote Intra-Fallopian Transfer)", "IUT (Intra-Uterine Transfer)", "GIFT (Gamete Intra-Fallopian Transfer)", "ICSI"],
        "ans": 0, "topic": "Reproductive Health", "subtype": "theory_definition",
        "exp": "ZIFT introduces a fertilized zygote or early cleavage embryo (≤ 8 cells) directly into the fallopian tube."
    },

    # ── 9. Genetics & Molecular Biology ──
    {
        "q": "Mendel's Law of Independent Assortment is verified experimentally by observing the F₂ phenotypic ratio of:",
        "opts": ["3:1", "9:3:3:1", "1:2:1", "9:7"],
        "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Dihybrid crosses yield a 9:3:3:1 phenotypic segregation when non-allelic gene pairs sort independently during meiosis."
    },
    {
        "q": "Incomplete dominance exhibiting identical phenotypic and genotypic ratios of 1:2:1 in F₂ is seen in flower color of:",
        "opts": ["Pisum sativum", "Mirabilis jalapa (Snapdragon / 4 O'clock plant)", "Drosophila melanogaster", "Lathyrus odoratus"],
        "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "In Mirabilis and Antirrhinum, heterozygous flowers display intermediate pink pigmentation (1 Red : 2 Pink : 1 White)."
    },
    {
        "q": "The human ABO blood group system demonstrates both multiple allelism and which genetic interaction?",
        "opts": ["Epistasis", "Codominance", "Pleiotropy", "Polygenic inheritance"],
        "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Alleles Iᴬ and Iᴮ are codominant: heterozygous IᴬIᴮ individuals express both A and B erythrocyte surface antigens."
    },
    {
        "q": "Down syndrome in humans is caused by chromosomal aneuploidy resulting from:",
        "opts": ["Trisomy of chromosome 21", "Monosomy of chromosome X (45, XO)", "Trisomy of sex chromosomes (47, XXY)", "Deletion of 5p arm"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Down syndrome arises from non-disjunction leading to trisomy 21 (47, +21)."
    },
    {
        "q": "Sickle cell anemia is caused by a point mutation in the β-globin gene substituting:",
        "opts": ["Glutamic acid by Valine at position 6", "Valine by Glutamic acid at position 6", "Lysine by Glycine at position 6", "Leucine by Alanine at position 6"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "A GAG to GUG transversion in the β-globin codon replaces polar glutamate with hydrophobic valine at position 6."
    },
    {
        "q": "A human female with 45 chromosomes and karyotype 45, XO exhibiting sterile ovaries and webbed neck has:",
        "opts": ["Klinefelter syndrome", "Turner syndrome", "Cri-du-chat syndrome", "Edward syndrome"],
        "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Monosomy of the X chromosome in females causes Turner syndrome characterized by rudimentary ovaries and short stature."
    },
    {
        "q": "The unequivocal radioactive proof that DNA is the genetic material was demonstrated by Alfred Hershey and Martha Chase using:",
        "opts": ["¹⁴N and ¹⁵N isotopes", "³²P (DNA) and ³⁵S (Protein) with T2 bacteriophage", "³H thymidine", "Heavy carbon ¹⁴C"],
        "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Hershey-Chase proved ³²P-labeled DNA entered bacterial cells while ³⁵S-labeled protein coats remained outside."
    },
    {
        "q": "Semi-conservative replication of DNA was experimentally demonstrated in Escherichia coli by:",
        "opts": ["Griffith", "Meselson and Stahl using ¹⁵NH₄Cl CsCl density gradient", "Watson and Crick", "Beadle and Tatum"],
        "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Meselson and Stahl separated hybrid ¹⁴N-¹⁵N DNA duplexes from heavy and light strands via equilibrium ultracentrifugation."
    },
    {
        "q": "The enzyme that synthesizes the leading strand continuously and the lagging strand discontinuously in 5' → 3' direction is:",
        "opts": ["DNA Polymerase III", "DNA Ligase", "RNA Polymerase II", "Reverse Transcriptase"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "DNA-dependent DNA polymerase extends deoxynucleotides strictly in the 5' to 3' polarity from an RNA primer."
    },
    {
        "q": "Which codon serves dual functions as the universal translation initiation codon and codes for Methionine?",
        "opts": ["UAA", "AUG", "UGA", "UAG"],
        "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "AUG acts as the start codon on mRNA transcripts and encodes methionine in eukaryotes."
    },
    {
        "q": "In the Jacob and Monod lac operon model, the natural physiological inducer that binds and inactivates the repressor is:",
        "opts": ["Glucose", "Allolactose", "Galactose", "cAMP"],
        "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Allolactose, a lactose metabolite produced by basal β-galactosidase, binds the lac repressor to permit transcription."
    },
    {
        "q": "The non-coding repetitive tandem repeats utilized as molecular probes in DNA fingerprinting are termed:",
        "opts": ["RFLPs", "VNTRs (Variable Number of Tandem Repeats)", "cDNAs", "Exons"],
        "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "VNTRs are minisatellite tandem repeat arrays with high allelic polymorphism used in forensic DNA profiling."
    },

    # ── 10. Evolution, Health, Biotechnology & Ecology ──
    {
        "q": "In the classic Miller-Urey experiment (1953) simulating primitive Earth conditions, electric discharge produced:",
        "opts": ["Nucleic acids", "Amino acids (Glycine, Alanine, Aspartic acid)", "Proteins and Polysaccharides", "Lipid coacervates"],
        "ans": 1, "topic": "Evolution", "subtype": "theory_definition",
        "exp": "Spark discharge through CH₄, NH₃, H₂, and H₂O vapor synthesized prebiotic amino acids."
    },
    {
        "q": "Homologous organs such as the forelimbs of cheetah, human, bat, and whale demonstrate:",
        "opts": ["Convergent evolution", "Divergent evolution sharing common ancestry", "Analogous adaptation", "Saltation"],
        "ans": 1, "topic": "Evolution", "subtype": "theory_definition",
        "exp": "Homologous structures share anatomical plan and origin but diverge functionally to adapt to varied niches."
    },
    {
        "q": "According to the Hardy-Weinberg equilibrium (p² + 2pq + q² = 1), allele frequencies in a population remain constant unless influenced by:",
        "opts": ["Random mating", "Absence of mutation", "Gene flow, genetic drift, mutation, and natural selection", "Large population size"],
        "ans": 2, "topic": "Evolution", "subtype": "theory_definition",
        "exp": "Genetic drift, migration, mutation, recombination, and selection disturb Hardy-Weinberg equilibrium frequencies."
    },
    {
        "q": "The Widal diagnostic agglutination test is used worldwide to detect clinical infection of:",
        "opts": ["Pneumonia", "Typhoid fever (Salmonella typhi)", "Malaria", "Amoebiasis"],
        "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition",
        "exp": "Widal tests measure agglutinating antibodies against O and H antigens of Salmonella typhi."
    },
    {
        "q": "In the life cycle of Plasmodium vivax, infective sporozoites inoculated into humans by female Anopheles mosquitoes are stored in the:",
        "opts": ["Mosquito stomach wall", "Mosquito salivary glands", "Human spleen", "Mosquito hemolymph"],
        "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition",
        "exp": "Sporozoites migrate to and reside within the salivary glands of female Anopheles mosquitoes until injected."
    },
    {
        "q": "The antibody immunoglobulin that provides passive mucosal immunity and is abundantly secreted in maternal colostrum is:",
        "opts": ["IgG", "IgA", "IgM", "IgE"],
        "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition",
        "exp": "Dimeric secretory IgA coats infant gastrointestinal and respiratory mucosa, providing early passive immunity."
    },
    {
        "q": "Human Immunodeficiency Virus (HIV) preferentially infects and destroys which circulating immune cells:",
        "opts": ["B-lymphocytes", "T-helper cells (CD4⁺ lymphocytes)", "Cytotoxic T-cells (CD8⁺)", "Neutrophils"],
        "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition",
        "exp": "HIV binds CD4 receptors on helper T-cells, depleting their numbers and precipitating severe immune deficiency."
    },
    {
        "q": "The restriction enzyme EcoRI recognizes and cleaves which specific palindromic DNA sequence?",
        "opts": ["5'-AAGCTT-3'", "5'-GAATTC-3'", "5'-GGATCC-3'", "5'-CTCGAG-3'"],
        "ans": 1, "topic": "Biotechnology: Principles and Processes", "subtype": "theory_definition",
        "exp": "EcoRI cleaves the hexanucleotide palindrome 5'-G↓AATTC-3' between G and A, leaving 5' cohesive sticky ends."
    },
    {
        "q": "The heat-stable DNA polymerase utilized in the automated Polymerase Chain Reaction (PCR) is isolated from:",
        "opts": ["Escherichia coli", "Thermus aquaticus (Taq)", "Bacillus thuringiensis", "Agrobacterium tumefaciens"],
        "ans": 1, "topic": "Biotechnology: Principles and Processes", "subtype": "theory_definition",
        "exp": "Taq polymerase withstands repeated 94°C denaturation cycles without heat denaturation."
    },
    {
        "q": "Genetically engineered Bt cotton resists lepidopteran bollworm pests due to toxic insecticidal crystal proteins encoded by:",
        "opts": ["cryIAc and cryIIAb genes", "cryIAb only", "ampR genes", "rop genes"],
        "ans": 0, "topic": "Biotechnology and its Applications", "subtype": "theory_definition",
        "exp": "cryIAc and cryIIAb genes produce endotoxins that lyse midgut epithelial cells in cotton bollworm larvae."
    },
    {
        "q": "Humulin (recombinant human insulin) synthesized by Eli Lilly in 1983 differs from proinsulin because:",
        "opts": ["It contains C-peptide", "The connecting C-peptide is cleaved and absent", "It has only chain A", "Chains A and B lack disulfide bonds"],
        "ans": 1, "topic": "Biotechnology and its Applications", "subtype": "theory_definition",
        "exp": "Active mature human insulin comprises A and B peptide chains linked by disulfide bridges, lacking the C-peptide."
    },
    {
        "q": "In 1990, the first clinical gene therapy was successfully administered to a 4-year-old girl suffering from deficiency of:",
        "opts": ["Adenosine Deaminase (ADA)", "Phenylalanine hydroxylase", "Insulin", "Glucocerebrosidase"],
        "ans": 0, "topic": "Biotechnology and its Applications", "subtype": "theory_definition",
        "exp": "Lymphocytes transduced with a functional ADA cDNA retroviral vector cured severe combined immunodeficiency (SCID)."
    },
    {
        "q": "According to Allen's ecological rule, mammals inhabiting colder polar climates tend to possess:",
        "opts": ["Longer ears and limbs", "Shorter ears and shorter limbs to minimize heat loss", "Thinner subcutaneous fat", "Larger surface area to volume ratio"],
        "ans": 1, "topic": "Organisms and Populations", "subtype": "theory_definition",
        "exp": "Allen's rule states that cold-climate homeotherms have reduced extremity lengths to curtail radiative heat loss."
    },
    {
        "q": "The ecological interaction between an orchid growing on the branch of a mango tree is an example of:",
        "opts": ["Mutualism", "Commensalism (+ / 0)", "Parasitism", "Amensalism"],
        "ans": 1, "topic": "Organisms and Populations", "subtype": "theory_definition",
        "exp": "The epiphytic orchid derives physical support without harming or benefiting the host mango tree."
    },
    {
        "q": "According to Lindeman's 10% trophic efficiency law in an ecosystem, if producers synthesize 10,000 J of energy, how much energy reaches secondary consumers?",
        "opts": ["1,000 J", "100 J", "10 J", "1 J"],
        "ans": 1, "topic": "Ecosystem", "subtype": "theory_definition",
        "exp": "Producers: 10,000 J → Primary consumers: 1,000 J (10%) → Secondary consumers: 100 J (10% of 1,000 J)."
    },
    {
        "q": "Which of the following ecological pyramids is ALWAYS upright and can never be inverted under natural conditions?",
        "opts": ["Pyramid of Numbers", "Pyramid of Biomass", "Pyramid of Energy", "Pyramid of Standing Crop"],
        "ans": 2, "topic": "Ecosystem", "subtype": "theory_definition",
        "exp": "Energy is inevitably dissipated as metabolic heat at each trophic transfer according to the Second Law of Thermodynamics."
    },
    {
        "q": "An example of ex-situ conservation of endangered wild flora and fauna is:",
        "opts": ["National Park", "Wildlife Sanctuary", "Botanical Garden / Cryopreservation", "Biosphere Reserve"],
        "ans": 2, "topic": "Biodiversity and Conservation", "subtype": "theory_definition",
        "exp": "Ex-situ conservation preserves threatened species outside their natural habitats in zoological parks, gardens, or cryobanks."
    },
    {
        "q": "The phenomena where non-biodegradable pesticides like DDT increase in concentration at successively higher trophic levels is:",
        "opts": ["Eutrophication", "Biomagnification", "Biopiracy", "Biofortification"],
        "ans": 1, "topic": "Environmental Issues", "subtype": "theory_definition",
        "exp": "Fat-soluble pollutants like DDT cannot be metabolized or excreted, accumulating progressively up food webs."
    },
    {
        "q": "The international treaty signed in 1987 to control the emission of ozone-depleting substances (CFCs) is the:",
        "opts": ["Kyoto Protocol", "Montreal Protocol", "Paris Agreement", "Ramsar Convention"],
        "ans": 1, "topic": "Environmental Issues", "subtype": "theory_definition",
        "exp": "The Montreal Protocol phased out production of chlorofluorocarbons to protect the stratospheric ozone shield."
    }
]

# Expand to 260+ unique questions covering all detailed KCET chapters
_ADDITIONAL_BIO_BANK: List[Dict[str, Any]] = [
    # Taxonomy & Cryptogams
    {"q": "The natural system of angiosperm classification based on natural affinities and vegetative/floral traits was proposed by:",
     "opts": ["Bentham and Hooker", "Carolus Linnaeus", "Engler and Prantl", "Hutchinson"],
     "ans": 0, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "George Bentham and Joseph Dalton Hooker authored Genera Plantarum providing the natural system."},
    {"q": "Floridean starch, having structural similarity to amylopectin and glycogen, is the stored food in:",
     "opts": ["Chlorophyceae", "Phaeophyceae", "Rhodophyceae (Red algae)", "Chrysophytes"],
     "ans": 2, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "Rhodophyceae store carbohydrates in the form of Floridean starch."},
    {"q": "Gemma cups are specialized asexual multicellular green buds found on the thallus of:",
     "opts": ["Funaria", "Marchantia", "Polytrichum", "Sphagnum"],
     "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "Marchantia (liverwort) produces dorsal gemma cups for vegetative propagation."},
    {"q": "Prothallus in homosporous pteridophytes represents the:",
     "opts": ["Diploid sporophyte", "Independent, photosynthetic, monoecious gametophyte", "Parasitic stage on moss", "Seed-bearing cone"],
     "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "Fern spores germinate to yield a small, green, heart-shaped free-living prothallial gametophyte."},
    {"q": "Naked seeds lacking an enclosing ovarian wall are the hallmark of:",
     "opts": ["Angiosperms", "Gymnosperms", "Bryophytes", "Pteridophytes"],
     "ans": 1, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "Gymnosperm ovules are exposed on megasporophylls and develop into naked seeds."},
    {"q": "In which plant group are the male and female gametophytes completely dependent and retained on the parent sporophyte?",
     "opts": ["Bryophytes", "Pteridophytes", "Gymnosperms and Angiosperms", "Algae"],
     "ans": 2, "topic": "Plant Kingdom", "subtype": "theory_definition", "exp": "Spermatophytes (gymnosperms and angiosperms) do not have free-living gametophytes."},
    {"q": "Syconus composite fruit developing from a hypanthodium inflorescence is found in:",
     "opts": ["Pineapple", "Fig (Ficus)", "Mulberry", "Apple"],
     "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition", "exp": "Ficus develops a syconus fruit from a flask-shaped hypanthodium inflorescence."},
    {"q": "The floral formula ⊕ ⚥ K(5) C(5) A5 G(2) with epipetalous stamens and persistent calyx describes Family:",
     "opts": ["Fabaceae", "Solanaceae", "Liliaceae", "Brassicaceae"],
     "ans": 1, "topic": "Morphology of Flowering Plants", "subtype": "theory_definition", "exp": "Solanaceae flowers are actinomorphic, pentamerous, with epipetalous stamens and bicarpellary syncarpous ovary."},
    {"q": "Collenchyma differs from parenchyma in possessing angular wall thickenings composed of:",
     "opts": ["Lignin", "Cellulose, hemicellulose, and pectin", "Suberin and cutin", "Chitin"],
     "ans": 1, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition", "exp": "Collenchymatous corners are thickened by pectin and hemicellulose, providing flexible tensile support."},
    {"q": "Sieve tube elements in angiosperms lack nuclei at maturity and are physiologically controlled by:",
     "opts": ["Xylem vessels", "Companion cells with dense cytoplasm and large nuclei", "Phloem sclerenchyma", "Albuminous cells"],
     "ans": 1, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition", "exp": "Companion cells are ontogenetically sister cells connected by plasmodesmata that maintain sieve tube viability."},
    {"q": "Lenticels in woody stems arise by the activity of phellogen (cork cambium) to facilitate:",
     "opts": ["Guttation", "Gaseous exchange between internal tissues and atmosphere", "Food conduction", "Translocation of minerals"],
     "ans": 1, "topic": "Anatomy of Flowering Plants", "subtype": "theory_definition", "exp": "Lenticels are aerating pores formed by loosely arranged complementary cells in the cork layer."},

    # Cytology & Cell Physiology
    {"q": "The organelle responsible for glycosylation of proteins and packaging into secretory vesicles is:",
     "opts": ["Mitochondria", "Golgi apparatus", "Ribosome", "Endoplasmic Reticulum alone"],
     "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition", "exp": "The Golgi apparatus modifies, glycosylates, and packages ER-synthesized proteins."},
    {"q": "The central core of a eukaryotic centriole or basal body shows which structural organization?",
     "opts": ["Cartwheel architecture with 9 + 0 peripheral triplets", "9 + 2 doublets", "12 peripheral singlets", "Solid microtubule bundle"],
     "ans": 0, "topic": "Cell: The Unit of Life", "subtype": "theory_definition", "exp": "Centrioles show a 9 + 0 cartwheel pattern composed of tubulin triplets linked to a central hub."},
    {"q": "Smooth Endoplasmic Reticulum (SER) is the major site of cellular synthesis of:",
     "opts": ["Polypeptides", "Lipids, steroids, and cholesterol", "RNA transcripts", "Glycogen alone"],
     "ans": 1, "topic": "Cell: The Unit of Life", "subtype": "theory_definition", "exp": "SER synthesizes phospholipids, triacylglycerols, and steroid hormones like estrogen and testosterone."},
    {"q": "A specialized mesosome in bacteria functions in which vital roles?",
     "opts": ["Cell wall formation, DNA replication, and cellular respiration", "Conjugation bridge", "Protein translation only", "Capsule synthesis"],
     "ans": 0, "topic": "Cell: The Unit of Life", "subtype": "theory_definition", "exp": "Mesosomes are plasma membrane invaginations involved in respiration, wall formation, and chromosome segregation."},
    {"q": "An amino acid having a basic side chain containing an amino group is:",
     "opts": ["Glutamic acid", "Lysine", "Valine", "Alanine"],
     "ans": 1, "topic": "Biomolecules", "subtype": "theory_definition", "exp": "Lysine, arginine, and histidine are basic amino acids bearing positively charged amino moieties."},
    {"q": "At which phase of mitosis do sister chromatids split at the centromere and migrate to opposite poles?",
     "opts": ["Prophase", "Metaphase", "Anaphase", "Telophase"],
     "ans": 2, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition", "exp": "Centromere cleavage during anaphase separates sister chromatids into individual daughter chromosomes."},
    {"q": "The stage of meiotic prophase I where homologous chromosomes align and form synaptonemal complexes is:",
     "opts": ["Leptotene", "Zygotene", "Pachytene", "Diakinesis"],
     "ans": 1, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition", "exp": "During Zygotene, synapsis zippers maternal and paternal homologs into bivalents."},
    {"q": "Terminalization of chiasmata and breakdown of the nucleolus mark the transition into:",
     "opts": ["Diplotene", "Diakinesis", "Pachytene", "Metaphase II"],
     "ans": 1, "topic": "Cell Cycle and Cell Division", "subtype": "theory_definition", "exp": "Diakinesis is the terminal stage of Prophase I where chiasmata shift toward chromosome ends."},

    # Plant Physiology Continued
    {"q": "The apoplastic pathway of water transport in roots involves movement through:",
     "opts": ["Interconnected protoplasts via plasmodesmata", "Cell walls and intercellular spaces without crossing plasma membranes", "Endodermal Casparian strips", "Vacuolar sap"],
     "ans": 1, "topic": "Transport in Plants", "subtype": "theory_definition", "exp": "The apoplast consists of continuous non-living porous cell walls and spaces until halted by Casparian strips."},
    {"q": "Potassium (K⁺) ions in plants are critically required for:",
     "opts": ["Chlorophyll synthesis", "Stomatal opening/closing and maintaining anion-cation equilibrium", "DNA replication", "Pectin formation"],
     "ans": 1, "topic": "Mineral Nutrition", "subtype": "theory_definition", "exp": "K⁺ influx into guard cells drives osmotically mediated stomatal opening."},
    {"q": "Which mineral element forms the central metallic coordinating atom of the porphyrin ring of chlorophyll?",
     "opts": ["Iron (Fe)", "Magnesium (Mg)", "Manganese (Mn)", "Zinc (Zn)"],
     "ans": 1, "topic": "Mineral Nutrition", "subtype": "theory_definition", "exp": "A magnesium ion (Mg²⁺) is coordinated at the center of the tetrapyrrole porphyrin head of chlorophyll."},
    {"q": "Photolysis of water (water-splitting complex) during light reaction releases oxygen and is mediated by:",
     "opts": ["Manganese (Mn) and Chlorine (Cl)", "Magnesium and Zinc", "Copper and Iron", "Molybdenum and Boron"],
     "ans": 0, "topic": "Photosynthesis in Higher Plants", "subtype": "theory_definition", "exp": "The oxygen-evolving complex associated with PS II requires Mn²⁺ and Cl⁻ ions for photolytic water oxidation."},
    {"q": "In the Hatch and Slack (C₄) pathway, the 4-carbon organic acid produced in mesophyll cells is:",
     "opts": ["3-PGA", "Oxaloacetic acid (OAA)", "Citric acid", "Pyruvate"],
     "ans": 1, "topic": "Photosynthesis in Higher Plants", "subtype": "theory_definition", "exp": "Phosphoenolpyruvate (PEP) carboxylase adds CO₂ to PEP (3C), forming oxaloacetic acid (4C)."},
    {"q": "In respiration, the conversion of Succinyl-CoA to Succinate in the Krebs cycle generates:",
     "opts": ["1 ATP/GTP by substrate-level phosphorylation", "1 FADH₂", "1 NADH", "1 CO₂"],
     "ans": 0, "topic": "Respiration in Plants", "subtype": "theory_definition", "exp": "Succinate thiokinase couples the thioester cleavage of Succinyl-CoA to GDP phosphorylation."},
    {"q": "Cytochrome c is a small, soluble, mobile protein attached to the outer surface of the inner mitochondrial membrane that shuttles electrons between:",
     "opts": ["Complex I and II", "Complex III and Complex IV", "Complex II and III", "Complex IV and ATP synthase"],
     "ans": 1, "topic": "Respiration in Plants", "subtype": "theory_definition", "exp": "Cytochrome c ferries electrons from ubiquinol-cytochrome c reductase (Complex III) to cytochrome c oxidase (Complex IV)."},
    {"q": "The precursor amino acid for the enzymatic biosynthesis of indole-3-acetic acid (Auxin) is:",
     "opts": ["Methionine", "Tryptophan", "Tyrosine", "Phenylalanine"],
     "ans": 1, "topic": "Plant Growth and Development", "subtype": "theory_definition", "exp": "Tryptophan is the aromatic amino acid precursor for the biosynthetic synthesis of IAA in shoot tips."},
    {"q": "Bakanae (foolish seedling) disease in rice seedlings led to the discovery of:",
     "opts": ["Auxin", "Gibberellin (by Kurosawa)", "Cytokinin", "Abscisic acid"],
     "ans": 1, "topic": "Plant Growth and Development", "subtype": "theory_definition", "exp": "Kurosawa isolated gibberellic acid from the fungal pathogen Gibberella fujikuroi causing stem elongation."},
    {"q": "The site of perception of photoperiodic light stimuli that triggers florigen hormone synthesis is the:",
     "opts": ["Shoot apical meristem", "Leaves", "Floral bud", "Root tip"],
     "ans": 1, "topic": "Plant Growth and Development", "subtype": "theory_definition", "exp": "Leaves perceive photoperiodic day/night cycles and transmit systemic florigen to the shoot apex."},

    # Human Physiology Continued
    {"q": "Chylomicrons, the lipid-protein droplets absorbed from the intestinal lumen, enter circulation via:",
     "opts": ["Hepatic portal vein", "Lacteals (lymphatic vessels of villi)", "Renal capillaries", "Superior mesenteric artery"],
     "ans": 1, "topic": "Digestion and Absorption", "subtype": "theory_definition", "exp": "Triglycerides coated with apolipoproteins form chylomicrons that drain into villous lacteal lymphatics."},
    {"q": "The bile salts sodium glycocholate and sodium taurocholate aid in digestion by:",
     "opts": ["Hydrolyzing proteins", "Emulsifying fats into fine micelles", "Activating salivary amylase", "Deaminating amino acids"],
     "ans": 1, "topic": "Digestion and Absorption", "subtype": "theory_definition", "exp": "Bile salts lower surface tension, breaking fat globules into microscopic micelles for lipase attack."},
    {"q": "A chronic pulmonary disorder characterized by destruction of alveolar walls and decreased respiratory surface area, predominantly caused by cigarette smoking, is:",
     "opts": ["Asthma", "Emphysema", "Pneumoconiosis", "Silicosis"],
     "ans": 1, "topic": "Breathing and Exchange of Gases", "subtype": "theory_definition", "exp": "Emphysema degrades elastase-inhibited alveolar septa, reducing surface area for diffusion."},
    {"q": "Erythroblastosis fetalis develops when an Rh-negative mother carries an:",
     "opts": ["Rh-negative fetus", "Rh-positive fetus during second or subsequent pregnancies", "ABO incompatible infant", "O-negative fetus"],
     "ans": 1, "topic": "Body Fluids and Circulation", "subtype": "theory_definition", "exp": "Maternal anti-Rh IgG antibodies cross the placenta in subsequent Rh⁺ pregnancies, hemolyzing fetal red cells."},
    {"q": "The fibrous cords attached to the cusps of AV valves and papillary muscles in ventricles to prevent valve eversion are:",
     "opts": ["Chordae tendineae", "Purkinje fibers", "Trabeculae carneae", "Pectinate muscles"],
     "ans": 0, "topic": "Body Fluids and Circulation", "subtype": "theory_definition", "exp": "Chordae tendineae anchor tricuspid and bicuspid leaflets to prevent backflow into atria during systole."},
    {"q": "Which nitrogenous waste product requires the minimum amount of water for excretion and is excreted as a semi-solid paste by birds and terrestrial reptiles?",
     "opts": ["Ammonia", "Urea", "Uric acid", "Creatinine"],
     "ans": 2, "topic": "Excretory Products and Their Elimination", "subtype": "theory_definition", "exp": "Uricotelic animals convert nitrogen into insolubly pasty uric acid, conserving water."},
    {"q": "The hairpin-shaped capillary loop running parallel to Henle's loop that maintains hyperosmolar medullary gradients is the:",
     "opts": ["Peritubular capillary network", "Vasa recta", "Glomerulus", "Afferent arteriole"],
     "ans": 1, "topic": "Excretory Products and Their Elimination", "subtype": "theory_definition", "exp": "Countercurrent exchange in the vasa recta preserves the osmotic gradient of the renal medulla."},
    {"q": "The autoimmune neuromuscular disorder affecting acetylcholine receptors at neuromuscular junctions, causing skeletal muscle fatigue and paralysis, is:",
     "opts": ["Muscular dystrophy", "Myasthenia gravis", "Tetany", "Gouty arthritis"],
     "ans": 1, "topic": "Locomotion and Movement", "subtype": "theory_definition", "exp": "Autoantibodies block nicotinic acetylcholine receptors at the motor end plate in myasthenia gravis."},
    {"q": "A pivot joint permitting rotational movement of the head is situated between the:",
     "opts": ["Atlas and Axis cervical vertebrae", "Carpals of wrist", "Femur and pelvic girdle", "Humerus and radius"],
     "ans": 0, "topic": "Locomotion and Movement", "subtype": "theory_definition", "exp": "The odontoid peg of the axis pivots within the ring of the atlas to rotate the skull."},
    {"q": "The tract of myelinated commissural nerve fibers that connects the right and left cerebral hemispheres in mammals is the:",
     "opts": ["Corpus callosum", "Pons Varolii", "Arbor vitae", "Crura cerebri"],
     "ans": 0, "topic": "Neural Control and Coordination", "subtype": "theory_definition", "exp": "The corpus callosum is a thick C-shaped white matter bundle coordinating inter-hemispheric communication."},
    {"q": "In the human eye, the central depression of the macula lutea containing only cones and providing maximum visual acuity is the:",
     "opts": ["Blind spot (optic disc)", "Fovea centralis", "Cornea", "Choroid"],
     "ans": 1, "topic": "Neural Control and Coordination", "subtype": "theory_definition", "exp": "The fovea contains densely packed cone photoreceptors responsible for sharp color vision."},
    {"q": "The sensory hearing apparatus containing hair cells situated on the basilar membrane within the cochlea is the:",
     "opts": ["Organ of Corti", "Macula", "Crista ampullaris", "Tympanic membrane"],
     "ans": 0, "topic": "Neural Control and Coordination", "subtype": "theory_definition", "exp": "The organ of Corti converts pressure waves in cochlear endolymph into auditory action potentials."},
    {"q": "Graves' disease (exophthalmic goitre) is an autoimmune hyperthyroid disorder characterized by:",
     "opts": ["Enlarged thyroid, protruding eyeballs, increased BMR, and weight loss", "Extreme weight gain and low heart rate", "Cretinism and mental retardation", "Tetany from hypocalcemia"],
     "ans": 0, "topic": "Chemical Coordination and Integration", "subtype": "theory_definition", "exp": "Thyroid-stimulating antibodies continuously activate the TSH receptor, causing exophthalmos and hyperthyroidism."},
    {"q": "Which peptide hormone is secreted by the heart atria in response to elevated blood pressure to stimulate vasodilation and natriuresis?",
     "opts": ["Aldosterone", "Atrial Natriuretic Factor (ANF)", "Renin", "Erythropoietin"],
     "ans": 1, "topic": "Chemical Coordination and Integration", "subtype": "theory_definition", "exp": "ANF opposes the renin-angiotensin-aldosterone axis by causing renal Na⁺ excretion and vasodilation."},

    # Genetics, Biotech & Ecology Continued
    {"q": "A cross between an F₁ heterozygous individual (AaBb) and its double recessive parent (aabb) is called a:",
     "opts": ["Back cross", "Dihybrid test cross yielding a 1:1:1:1 ratio", "Reciprocal cross", "Monohybrid cross"],
     "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition", "exp": "A dihybrid test cross reveals parental and recombinant frequencies in a classical 1:1:1:1 phenotypic ratio."},
    {"q": "In human males, Klinefelter syndrome is characterized by which chromosomal complement?",
     "opts": ["45, XO", "47, XXY", "47, XYY", "47, XXX"],
     "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition", "exp": "Klinefelter males have an extra X chromosome (47, XXY) showing gynecomastia and sterile testes."},
    {"q": "A pleiotropic gene is defined as a gene that:",
     "opts": ["Controls only one phenotype", "Influences multiple phenotypic traits simultaneously", "Is located on the Y chromosome", "Codes for rRNA"],
     "ans": 1, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition", "exp": "Pleiotropic alleles (like phenylketonuria) produce multiple phenotypic manifestations from a single genetic locus."},
    {"q": "The cloverleaf secondary structure model of transfer RNA (tRNA) was proposed by:",
     "opts": ["Robert Holley", "Francis Crick", "Marshall Nirenberg", "Har Gobind Khorana"],
     "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition", "exp": "Robert Holley established the cloverleaf 2D structure of tRNA featuring the anticodon and amino acid acceptor arms."},
    {"q": "The enzyme peptidyl transferase responsible for peptide bond formation during translation is a ribozyme composed of:",
     "opts": ["23S rRNA in bacteria (28S rRNA in eukaryotes)", "DNA ligase", "RNA polymerase I", "Aminoacyl-tRNA synthetase"],
     "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition", "exp": "The 23S rRNA of the large 50S subunit acts as an intrinsic catalytic ribozyme forming peptide bonds."},
    {"q": "In the lac operon of E. coli, the repressor protein is constitutively encoded by the:",
     "opts": ["z gene", "i gene (inhibitor / regulator)", "y gene", "a gene"],
     "ans": 1, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition", "exp": "The i gene transcribes the lac repressor monomer that binds the operator locus in the absence of inducer."},
    {"q": "The Human Genome Project (HGP) revealed that the total number of estimated protein-coding genes in human DNA is approximately:",
     "opts": ["20,000 to 25,000", "80,000 to 100,000", "5,000 to 10,000", "150,000"],
     "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition", "exp": "The sequenced human genome contains ~20,000–25,000 protein-coding genes, far fewer than earlier estimates."},
    {"q": "Industrial melanism in the peppered moth (Biston betularia) in England is a classical demonstration of:",
     "opts": ["Directional natural selection", "Stabilizing selection", "Disruptive selection", "Artificial mutation"],
     "ans": 0, "topic": "Evolution", "subtype": "theory_definition", "exp": "Soot-darkened tree trunks favored dark melanic mutants (B. carbonaria) over light lichens via directional selection."},
    {"q": "Adaptive radiation in Darwin's finches of the Galápagos Islands arose from ancestral finches through modifications of:",
     "opts": ["Wing feathers for gliding", "Beak shape and size adapted to diverse food niches", "Foot claws for swimming", "Eye lenses"],
     "ans": 1, "topic": "Evolution", "subtype": "theory_definition", "exp": "Seed-eating ancestral finches radiated into insectivorous, cactus-eating, and frugivorous niches with specialized beaks."},
    {"q": "The first human ancestor capable of making crude stone tools, with a cranial capacity of 650–800 cc, was:",
     "opts": ["Australopithecus", "Homo habilis (Handy man)", "Homo erectus", "Neanderthal man"],
     "ans": 1, "topic": "Evolution", "subtype": "theory_definition", "exp": "Homo habilis made the earliest Oldowan stone tools and had a brain capacity between 650 and 800 cc."},
    {"q": "The malignant property of cancerous tumors to detach, circulate in blood or lymph, and initiate secondary tumors at distant sites is:",
     "opts": ["Contact inhibition", "Metastasis", "Transformation", "Angiogenesis"],
     "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition", "exp": "Metastasis is the cardinal hallmark of malignant neoplasms spreading through vascular routes."},
    {"q": "Morphine and heroin are opioid analgesics obtained from the latex of which plant?",
     "opts": ["Cannabis sativa", "Papaver somniferum (Opium poppy)", "Erythroxylum coca", "Atropa belladonna"],
     "ans": 1, "topic": "Human Health and Disease", "subtype": "theory_definition", "exp": "Opium poppy latex yields morphine, which is diacetylated into heroin (smack)."},
    {"q": "In plasmid cloning vector pBR322, insertion of a foreign gene into the BamHI site leads to insertional inactivation of the:",
     "opts": ["Ampicillin resistance gene (ampR)", "Tetracycline resistance gene (tetR)", "rop gene", "Origin of replication (ori)"],
     "ans": 1, "topic": "Biotechnology: Principles and Processes", "subtype": "theory_definition", "exp": "The BamHI recognition site lies within the tetR gene; insertion disrupts tetracycline resistance."},
    {"q": "Gel electrophoresis separates negatively charged DNA fragments across an agarose matrix based primarily on their:",
     "opts": ["Base composition", "Size / length (molecular weight)", "Charge alone", "Number of hydrogen bonds"],
     "ans": 1, "topic": "Biotechnology: Principles and Processes", "subtype": "theory_definition", "exp": "DNA has a uniform charge-to-mass ratio and migrates toward the anode; agarose pores sieve fragments by molecular size."},
    {"q": "RNA interference (RNAi) employed to protect tobacco plants from the root-knot nematode Meloidogyne incognita involves:",
     "opts": ["Silencing of specific mRNA using complementary double-stranded RNA (dsRNA)", "Transposon activation", "Insertion of antibiotic resistance genes", "Antibody neutralization"],
     "ans": 0, "topic": "Biotechnology and its Applications", "subtype": "theory_definition", "exp": "Dicer and RISC complexes process dsRNA into siRNAs that target and cleave nematode-specific mRNA transcripts."},
    {"q": "The first transgenic cow 'Rosie' (1997) produced milk enriched with which human protein?",
     "opts": ["Alpha-lactalbumin", "Alpha-1-antitrypsin", "Insulin", "Factor VIII"],
     "ans": 0, "topic": "Biotechnology and its Applications", "subtype": "theory_definition", "exp": "Transgenic cow Rosie synthesized human alpha-lactalbumin-rich milk (2.4 g/L), nutritionally superior for human infants."},
    {"q": "Gause's Competitive Exclusion Principle states that two closely related species competing for the same limiting resource:",
     "opts": ["Will coexist by mutualism", "Cannot coexist indefinitely; the competitively inferior species will be eliminated", "Will double their reproduction", "Will evolve identical morphology"],
     "ans": 1, "topic": "Organisms and Populations", "subtype": "theory_definition", "exp": "Gause showed that two species with identical niche requirements cannot stably coexist when resources are limiting."},
    {"q": "The S-shaped sigmoid growth curve of a natural biological population adhering to carrying capacity (K) is modeled by the equation:",
     "opts": ["dN/dt = rN", "dN/dt = rN((K - N) / K)", "Nt = N₀eʳᵗ", "dN/dt = K/rN"],
     "ans": 1, "topic": "Organisms and Populations", "subtype": "theory_definition", "exp": "The Verhulst-Pearl Logistic Growth equation describes density-dependent population growth bounded by carrying capacity K."},
    {"q": "The 'Evil Quartet' recognized by conservation biologists describes the four major causes of:",
     "opts": ["Global warming", "Biodiversity loss and species extinctions", "Ozone hole expansion", "Soil erosion"],
     "ans": 1, "topic": "Biodiversity and Conservation", "subtype": "theory_definition", "exp": "Habitat loss/fragmentation, over-exploitation, alien species invasions, and co-extinctions form the Evil Quartet."},
    {"q": "The Rivet Popper Hypothesis illustrating the progressive consequence of species extinctions in an ecosystem was proposed by:",
     "opts": ["Edward Wilson", "Paul Ehrlich", "Robert May", "Alexander von Humboldt"],
     "ans": 1, "topic": "Biodiversity and Conservation", "subtype": "theory_definition", "exp": "Stanford ecologist Paul Ehrlich used the airplane rivet metaphor to explain ecosystem instability caused by species removal."}
]

# Combine both pools
BIOLOGY_BANK.extend(_ADDITIONAL_BIO_BANK)


# ── Extra High Yield Questions ──
_EXTRA_BIO: List[Dict[str, Any]] = [
    {'q': 'Cyclosporin A, a potent immunosuppressive agent used in organ transplant patients, is produced by the fungus:', 'opts': ['Trichoderma polysporum', 'Monascus purpureus', 'Aspergillus niger', 'Penicillium notatum'], 'ans': 0, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'Trichoderma polysporum produces cyclosporin A, which inhibits T-cell activation.'},
    {'q': 'Statins used as blood cholesterol-lowering agents are commercially produced by the yeast:', 'opts': ['Monascus purpureus', 'Saccharomyces cerevisiae', 'Candida albicans', 'Trichoderma'], 'ans': 0, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'Statins competitively inhibit HMG-CoA reductase, the rate-limiting enzyme in cholesterol synthesis.'},
    {'q': 'The large holes in Swiss cheese are produced by the bacterium:', 'opts': ['Propionibacterium sharmanii', 'Lactobacillus acidophilus', 'Streptococcus thermophilus', 'Acetobacter aceti'], 'ans': 0, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'Propionibacterium sharmanii releases high volumes of CO2 during propionic acid fermentation.'},
    {'q': 'BOD (Biochemical Oxygen Demand) measures the amount of oxygen required by aerobic microbes to oxidise organic matter; higher BOD indicates:', 'opts': ['Lower water pollution', 'Greater polluting potential of wastewater', 'Higher dissolved oxygen level', 'Absence of organic wastes'], 'ans': 1, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'High BOD signifies heavy organic contamination, which rapidly depletes dissolved oxygen.'},
    {'q': 'The bacterial biofertilizer that fixes atmospheric nitrogen symbiotically in the non-legume plant Alnus is:', 'opts': ['Frankia', 'Rhizobium', 'Azospirillum', 'Azotobacter'], 'ans': 0, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'Frankia, an actinomycete, forms root nodules and fixes N2 in Alnus and Casuarina.'},
    {'q': 'A microbial biocontrol agent used against lepidopteran plant butterfly caterpillars is:', 'opts': ['Bacillus thuringiensis (Bt spores)', 'Trichoderma viride', 'Baculovirus', 'Nosema'], 'ans': 0, 'topic': 'Microbes in Human Welfare', 'subtype': 'theory_definition', 'exp': 'Bt spore formulations contain crystal cry toxins that disrupt caterpillar gut membranes upon ingestion.'},
    {'q': 'The ability of an isolated plant explant cell to regenerate into an entire plantlet in sterile culture is called:', 'opts': ['Totipotency', 'Pluripotency', 'Embryogeny', 'Parthenogenesis'], 'ans': 0, 'topic': 'Strategies for Enhancement in Food Production', 'subtype': 'theory_definition', 'exp': 'Totipotency (Gottlieb Haberlandt) describes the innate genetic capacity of a single plant cell to regenerate a whole plant.'},
    {'q': 'Golden Rice is a genetically modified biofortified crop engineered to produce high levels of:', 'opts': ['Beta-carotene (provitamin A)', 'Vitamin C', 'Lysine and tryptophan', 'Iron and Zinc'], 'ans': 0, 'topic': 'Strategies for Enhancement in Food Production', 'subtype': 'theory_definition', 'exp': 'Daffodil phytoene synthase genes enable endosperm synthesis of provitamin A beta-carotene.'},
    {'q': 'Hisardale is a popular crossbreed sheep variety developed in Punjab by crossing:', 'opts': ['Bikaneri ewes and Marino rams', 'Nellore rams and Bikaneri ewes', 'Dorset rams and Merino ewes', 'Surti ewes and Murrah rams'], 'ans': 0, 'topic': 'Strategies for Enhancement in Food Production', 'subtype': 'theory_definition', 'exp': 'Hisardale sheep were produced by crossing Bikaneri ewes with Australian Marino rams.'},
    {'q': 'Atlas 66 is a biofortified crop variety used as a donor parent in plant breeding for having high content of:', 'opts': ['Protein', 'Iron', 'Vitamin A', 'Lysine'], 'ans': 0, 'topic': 'Strategies for Enhancement in Food Production', 'subtype': 'theory_definition', 'exp': 'Atlas 66 wheat possesses elevated endosperm protein content (over 15%).'},
    {'q': 'The technique MOET (Multiple Ovulation Embryo Transfer) uses FSH-like hormones in cattle to induce superovulation yielding:', 'opts': ['6 to 8 eggs per cycle', '1 egg per cycle', '15 to 20 eggs per cycle', '25 eggs per cycle'], 'ans': 0, 'topic': 'Strategies for Enhancement in Food Production', 'subtype': 'theory_definition', 'exp': 'MOET stimulates follicular maturation yielding 6-8 eggs, which are fertilized and transferred to surrogate cows.'},
    {'q': 'In 1974, the historic Chipko Movement to protect Himalayan forest trees from felling originated in:', 'opts': ['Reni village, Garhwal Himalayas', 'Khejrali, Rajasthan', 'Silent Valley, Kerala', 'Bastar, Chhattisgarh'], 'ans': 0, 'topic': 'Environmental Issues', 'subtype': 'theory_definition', 'exp': 'Local Garhwal women hugged trees in Reni village to prevent commercial timber logging.'},
    {'q': 'The Government of India instituted the Amrita Devi Wildlife Protection Award for exemplary dedication in protecting wildlife in memory of the:', 'opts': ['Bishnoi community of Rajasthan', 'Chipko movement leaders', 'Silent valley activists', 'Sunderban mangrove guards'], 'ans': 0, 'topic': 'Environmental Issues', 'subtype': 'theory_definition', 'exp': 'Amrita Devi Bishnoi sacrificed her life in 1731 with 363 others to protect Khejri trees in Rajasthan.'},
    {'q': 'Snow-blindness in humans is an inflammation of the cornea caused by excessive exposure to:', 'opts': ['UV-B radiation', 'Infrared rays', 'X-rays', 'Visible blue light'], 'ans': 0, 'topic': 'Environmental Issues', 'subtype': 'theory_definition', 'exp': 'Depletion of stratospheric ozone allows UV-B rays to reach Earth, causing corneal cataract and snow-blindness.'},
    {'q': 'The relative contribution of greenhouse gases to total global warming follows which order?', 'opts': ['CO2 (60%) > CH4 (20%) > CFCs (14%) > N2O (6%)', 'CH4 > CO2 > N2O > CFCs', 'CFCs > CO2 > CH4 > N2O', 'CO2 > N2O > CH4 > CFCs'], 'ans': 0, 'topic': 'Environmental Issues', 'subtype': 'theory_definition', 'exp': 'CO2 contributes 60%, methane 20%, chlorofluorocarbons 14%, and nitrous oxide 6% to radiative greenhouse warming.'},
    {'q': 'Eutrophication of aquatic lakes is the accelerated ecological aging caused by excessive anthropogenic runoff of:', 'opts': ['Nitrates and Phosphates', 'Heavy metals', 'Carbonates', 'Chlorides'], 'ans': 0, 'topic': 'Environmental Issues', 'subtype': 'theory_definition', 'exp': 'Nitrogen and phosphorus fertilizer runoff induces algal blooms, depleting oxygen and suffocating aquatic fauna.'},
    {'q': 'In the human brain, visual and auditory reflex centers are localized in the four round swellings of the midbrain called:', 'opts': ['Corpora quadrigemina', 'Corpus callosum', 'Pons Varolii', 'Infundibulum'], 'ans': 0, 'topic': 'Neural Control and Coordination', 'subtype': 'theory_definition', 'exp': 'The superior and inferior colliculi of the corpora quadrigemina mediate optic and acoustic reflexes.'},
    {'q': 'Aldosterone, the principal mineralocorticoid from the adrenal cortex, acts on the renal distal tubule to stimulate:', 'opts': ['Reabsorption of Na+ and water, and excretion of K+ and phosphate', 'Excretion of Na+ and water', 'Reabsorption of K+', 'Excretion of Ca2+'], 'ans': 0, 'topic': 'Chemical Coordination and Integration', 'subtype': 'theory_definition', 'exp': 'Aldosterone upregulates Na+/K+ pumps in the DCT and collecting duct, retaining sodium and water while secreting potassium.'},
    {'q': 'The filtration slits (slit pores) in the Bowman capsule are formed by specialized epithelial cells called:', 'opts': ['Podocytes', 'Mesangial cells', 'Macula densa', 'Endothelial fenestrae'], 'ans': 0, 'topic': 'Excretory Products and Their Elimination', 'subtype': 'theory_definition', 'exp': 'Podocyte foot processes (pedicels) interdigitate to form filtration slits restricting proteins from entering filtrate.'},
    {'q': 'Kranz anatomy with dimorphic chloroplasts (agranal bundle sheath and granal mesophyll) is an adaptation of:', 'opts': ['C4 plants (Maize, Sugarcane)', 'C3 plants (Wheat, Rice)', 'CAM plants', 'Hydrophytes'], 'ans': 0, 'topic': 'Photosynthesis in Higher Plants', 'subtype': 'theory_definition', 'exp': 'Kranz anatomy concentrates CO2 in bundle sheath cells around RuBisCO, completely eliminating photorespiration.'},
    {'q': 'Peter Mitchell proposed the chemiosmotic hypothesis of ATP synthesis, which is driven across the membrane by a:', 'opts': ['Proton electrochemical gradient (Proton motive force)', 'Calcium gradient', 'Sodium gradient', 'Electron transport carrier'], 'ans': 0, 'topic': 'Respiration in Plants', 'subtype': 'theory_definition', 'exp': 'Proton accumulation in the thylakoid lumen or mitochondrial intermembrane space drives ATP synthesis via CF0-CF1.'},
    {'q': 'Alfred Sturtevant utilized the frequency of genetic recombination between gene pairs on the same chromosome to:', 'opts': ['Map genetic distances between genes on chromosomes', 'Prove independent assortment', 'Demonstrate crossing over visually', 'Isolate DNA'], 'ans': 0, 'topic': 'Principles of Inheritance and Variation', 'subtype': 'theory_definition', 'exp': 'Sturtevant constructed the first genetic linkage map, where 1% recombination frequency equals 1 map unit (centiMorgan).'},
    {'q': 'Phenylketonuria (PKU) is an inborn autosomal recessive error of metabolism resulting from deficiency of:', 'opts': ['Phenylalanine hydroxylase', 'Tyrosinase', 'Homogentisic acid oxidase', 'Hexosaminidase A'], 'ans': 0, 'topic': 'Principles of Inheritance and Variation', 'subtype': 'theory_definition', 'exp': 'Lack of phenylalanine hydroxylase causes accumulation of phenylalanine and phenylpyruvate in brain tissue.'},
    {'q': 'Biolistics or gene gun method is a direct mechanical gene transfer technique suitable for plant cells using microprojectiles coated with DNA made of:', 'opts': ['Gold or Tungsten', 'Platinum or Silver', 'Copper or Iron', 'Titanium or Zinc'], 'ans': 0, 'topic': 'Biotechnology: Principles and Processes', 'subtype': 'theory_definition', 'exp': 'Dense microscopic gold or tungsten beads accelerated under helium pressure penetrate rigid plant cell walls.'},
    {'q': 'For recombinant DNA isolation, fungal cell walls are enzymatically digested by:', 'opts': ['Chitinase', 'Lysozyme', 'Cellulase', 'Pectinase'], 'ans': 0, 'topic': 'Biotechnology: Principles and Processes', 'subtype': 'theory_definition', 'exp': 'Chitinase digests fungal beta-1,4-linked N-acetylglucosamine cell walls to release intact protoplasts.'},
    {'q': 'Which hormone stimulates forceful uterine contractions during parturition and milk ejection from mammary glands?', 'opts': ['Oxytocin', 'Prolactin', 'Progesterone', 'Estrogen'], 'ans': 0, 'topic': 'Chemical Coordination and Integration', 'subtype': 'theory_definition', 'exp': 'Oxytocin synthesized by the hypothalamus induces myometrial contractions (Ferguson reflex) and myoepithelial milk ejection.'},
    {'q': 'Juxtaglomerular apparatus (JGA) releases renin in response to a fall in:', 'opts': ['Glomerular filtration rate (GFR) / blood pressure', 'Plasma glucose', 'Blood calcium', 'Serum potassium'], 'ans': 0, 'topic': 'Excretory Products and Their Elimination', 'subtype': 'theory_definition', 'exp': 'A drop in renal blood flow triggers granular JGA cells to release renin into circulation.'},
    {'q': 'The cranial capacity of Neanderthal man was approximately:', 'opts': ['1400 cc', '900 cc', '650 cc', '1650 cc'], 'ans': 0, 'topic': 'Evolution', 'subtype': 'theory_definition', 'exp': 'Neanderthal hominids possessed an average cranial capacity of ~1400 cc and buried their dead with ritual flowers.'},
    {'q': 'In DNA double helix structure described by Watson and Crick, the pitch of the B-DNA helix is:', 'opts': ['3.4 nm (34 Angstroms) containing 10 base pairs per turn', '0.34 nm', '2.0 nm', '34 nm'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': 'B-DNA has a helical rise of 0.34 nm per base pair, completing a full turn of 10 base pairs in 3.4 nm.'},
    {'q': 'Which connective tissue attaches skeletal muscle to bone in vertebrates?', 'opts': ['Tendon (dense regular collagenous)', 'Ligament', 'Cartilage', 'Adipose tissue'], 'ans': 0, 'topic': 'Structural Organisation in Animals', 'subtype': 'theory_definition', 'exp': 'Tendons connect muscle to bone, while ligaments connect bone to bone.'},
    {'q': 'The heart of a cockroach consists of how many funnel-shaped segmental chambers with ostia?', 'opts': ['13 chambers', '10 chambers', '8 chambers', '4 chambers'], 'ans': 0, 'topic': 'Structural Organisation in Animals', 'subtype': 'theory_definition', 'exp': 'Periplaneta americana possesses a dorsal tubular heart consisting of 13 segmental funnel-shaped chambers.'},
    {'q': 'Malpighian tubules in cockroaches and terrestrial insects function as:', 'opts': ['Excretory organs removing potassium urate from hemolymph', 'Respiratory tracheae', 'Digestive caeca', 'Sensory antennae'], 'ans': 0, 'topic': 'Structural Organisation in Animals', 'subtype': 'theory_definition', 'exp': '100-150 yellow Malpighian tubules extract metabolic wastes and convert them into uric acid.'},
    {'q': 'In angiosperm microsporogenesis, meiosis of one diploid pollen mother cell (PMC) produces:', 'opts': ['4 functional haploid pollen microspores in a tetrad', '1 microspore and 3 polar bodies', '8 pollen grains', '2 diploid microspores'], 'ans': 0, 'topic': 'Sexual Reproduction in Flowering Plants', 'subtype': 'theory_definition', 'exp': 'Each diploid PMC undergoes meiosis to produce a tetrahedral tetrad of four haploid functional microspores.'},
    {'q': 'Cleistogamous flowers (e.g., in Commelina, Viola, Oxalis) guarantee seed set even in the absence of pollinators because they:', 'opts': ['Never open and undergo obligate self-pollination (autogamy)', 'Produce sweet nectar', 'Are wind-pollinated', 'Open only at night'], 'ans': 0, 'topic': 'Sexual Reproduction in Flowering Plants', 'subtype': 'theory_definition', 'exp': 'Cleistogamous flowers remain closed, ensuring 100% autogamous self-pollination independently of pollinators.'},
    {'q': 'The primary endosperm nucleus (PEN) formed by triple fusion in angiosperms has a ploidy level of:', 'opts': ['3n (Triploid)', '2n (Diploid)', 'n (Haploid)', '4n (Tetraploid)'], 'ans': 0, 'topic': 'Sexual Reproduction in Flowering Plants', 'subtype': 'theory_definition', 'exp': 'One haploid male gamete fuses with two haploid polar nuclei in the central cell to yield a triploid 3n PEN.'},
    {'q': 'Which part of the fallopian tube (oviduct) possesses finger-like fimbriae to collect the released ovum from the ovary?', 'opts': ['Infundibulum', 'Ampulla', 'Isthmus', 'Uterine fundus'], 'ans': 0, 'topic': 'Human Reproduction', 'subtype': 'theory_definition', 'exp': 'The funnel-shaped infundibulum bears fimbriae that sweep the secondary oocyte into the oviduct.'},
    {'q': 'Fertilization in human reproduction normally takes place at which specific anatomical junction?', 'opts': ['Ampullary-isthmic junction of fallopian tube', 'Uterine cavity', 'Cervical canal', 'Ovarian cortex'], 'ans': 0, 'topic': 'Human Reproduction', 'subtype': 'theory_definition', 'exp': 'Capacitated sperm fertilize the secondary oocyte in the ampullary region of the fallopian tube.'},
    {'q': 'Colostrum, the first milk secreted by mammary glands after parturition, is rich in maternal antibody:', 'opts': ['IgA', 'IgG', 'IgM', 'IgE'], 'ans': 0, 'topic': 'Human Reproduction', 'subtype': 'theory_definition', 'exp': 'Maternal colostrum is rich in secretory IgA antibodies that protect the newborn against gastrointestinal infections.'},
    {'q': 'Copper-releasing intrauterine contraceptive devices (e.g., CuT, Cu7, Multiload 375) prevent conception primarily by:', 'opts': ['Suppressing sperm motility and fertilizing capacity', 'Blocking ovulation', 'Inhibiting implantation via progesterone', 'Destroying the ovum'], 'ans': 0, 'topic': 'Reproductive Health', 'subtype': 'theory_definition', 'exp': 'Cu2+ ions released into the uterine cavity suppress sperm motility and inhibit sperm-egg fertilization.'},
    {'q': 'The surgical permanent sterilization method in human females involving cutting and tying of fallopian tubes is:', 'opts': ['Tubectomy', 'Vasectomy', 'Hysterectomy', 'Laparoscopy'], 'ans': 0, 'topic': 'Reproductive Health', 'subtype': 'theory_definition', 'exp': 'Tubectomy prevents ovum migration and fertilization by ligating the fallopian tubes.'},
    {'q': 'Which disease is caused by an autosomal dominant genetic mutation and leads to progressive chorea and dementia?', 'opts': ['Huntington disease', 'Sickle cell anemia', 'Cystic fibrosis', 'Alkaptonuria'], 'ans': 0, 'topic': 'Principles of Inheritance and Variation', 'subtype': 'theory_definition', 'exp': 'Huntington chorea is an autosomal dominant trinucleotide repeat disorder causing striatal neurodegeneration.'},
    {'q': 'In a monohybrid cross with incomplete dominance (e.g., Mirabilis jalapa), the phenotypic ratio in F2 is:', 'opts': ['1 : 2 : 1', '3 : 1', '9 : 3 : 3 : 1', '1 : 1'], 'ans': 0, 'topic': 'Principles of Inheritance and Variation', 'subtype': 'theory_definition', 'exp': 'Cross of red and white flowers yields pink F1, giving 1 Red : 2 Pink : 1 White (1:2:1) in F2.'},
    {'q': 'The central dogma of molecular biology stating that genetic information flows from DNA → RNA → Protein was formulated by:', 'opts': ['Francis Crick', 'James Watson', 'Erwin Chargaff', 'Marshall Nirenberg'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': 'Francis Crick proposed the directional flow of genetic information from DNA to RNA to functional protein.'},
    {'q': 'In eukaryotic transcription, the enzyme that transcribes messenger RNA (mRNA / hnRNA) precursors is:', 'opts': ['RNA Polymerase II', 'RNA Polymerase I', 'RNA Polymerase III', 'DNA Polymerase I'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': 'RNA Polymerase II transcribes all protein-coding heteronuclear pre-mRNAs in eukaryotes.'},
    {'q': "The post-transcriptional addition of 7-methylguanosine triphosphate to the 5' end of hnRNA is termed:", 'opts': ['Capping', 'Tailing (Polyadenylation)', 'Splicing', 'Transesterification'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': "5' capping adds 7-methylguanosine, protecting transcripts from 5' exonucleolytic degradation."},
    {'q': 'The universal genetic code is degenerate because:', 'opts': ['Some amino acids are coded by more than one synonymous codon', 'One codon codes for multiple amino acids', 'Codons overlap on mRNA', 'Codons are ambiguous'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': '61 sense codons specify 20 amino acids; several amino acids (leucine, serine, arginine) have up to 6 synonymous codons.'},
    {'q': 'The stop or termination codons that do not specify any amino acid during translation are:', 'opts': ['UAA, UAG, and UGA', 'AUG, GUG, and UGG', 'AAA, UUU, and CCC', 'UAC, UAU, and UGC'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': 'Ochre (UAA), Amber (UAG), and Opal (UGA) signal release factors to terminate translation.'},
    {'q': 'The lac operon genes z, y, and a encode which enzymes, respectively?', 'opts': ['Beta-galactosidase, Permease, and Transacetylase', 'Permease, Beta-galactosidase, and Transacetylase', 'Transacetylase, Permease, and Beta-galactosidase', 'Repressor, Permease, and Beta-galactosidase'], 'ans': 0, 'topic': 'Molecular Basis of Inheritance', 'subtype': 'theory_definition', 'exp': 'Gene z codes for beta-galactosidase, y codes for lactose permease, and a codes for thiogalactoside transacetylase.'},
    {'q': 'Fossil archaeopteryx discovered in Bavarian limestone represents a connecting evolutionary link between:', 'opts': ['Reptiles and Birds', 'Amphibians and Reptiles', 'Fishes and Amphibians', 'Birds and Mammals'], 'ans': 0, 'topic': 'Evolution', 'subtype': 'theory_definition', 'exp': 'Archaeopteryx possessed reptilian teeth, tail vertebrae, and clawed wings alongside avian flight feathers.'},
    {'q': 'Analogous structures such as sweet potato (root modification) and potato (stem modification) are examples of:', 'opts': ['Convergent evolution', 'Divergent evolution', 'Atavism', 'Parallel evolution'], 'ans': 0, 'topic': 'Evolution', 'subtype': 'theory_definition', 'exp': 'Structurally dissimilar organs that converge onto the same storage function exhibit convergent evolution.'},
    {'q': 'The test used to confirm positive HIV infection following a preliminary screening ELISA test is:', 'opts': ['Western Blot test', 'Southern Blot test', 'Northern Blot test', 'Widal test'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Western blot verifies specific viral gp120, gp41, and p24 antibodies to confirm clinical HIV diagnosis.'},
    {'q': 'Malignant malaria characterized by cerebral complications and high mortality is caused by:', 'opts': ['Plasmodium falciparum', 'Plasmodium vivax', 'Plasmodium malariae', 'Plasmodium ovale'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Plasmodium falciparum infects RBCs of all ages, causing microvascular occlusion and cerebral malaria.'},
    {'q': 'The infectious larval stage of the roundworm Ascaris lumbricoides that infects humans through contaminated food and water is the:', 'opts': ['Embryonated egg with rhabditiform larva', 'Filariform larva', 'Microfilaria', 'Cercaria'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Ingestion of embryonated second-stage rhabditiform eggs initiates ascariasis in humans.'},
    {'q': 'A chronic protozoan infection causing amoebic dysentery with blood and mucus in stools is caused by:', 'opts': ['Entamoeba histolytica', 'Giardia lamblia', 'Trichomonas vaginalis', 'Leishmania donovani'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Entamoeba histolytica trophozoites secrete histolytic enzymes that erode intestinal mucosal walls.'},
    {'q': 'Elephantiasis (filariasis) marked by chronic inflammation and lymphedema of lower limbs is caused by:', 'opts': ['Wuchereria bancrofti transmitted by female Culex mosquitoes', 'Ascaris lumbricoides', 'Taenia solium', 'Ancylostoma duodenale'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Adult Wuchereria worms block lymphatic vessels of the lower limbs, causing massive chronic elephantoid swelling.'},
    {'q': 'Innate physiological barriers to microbial infection include:', 'opts': ['Gastric hydrochloric acid (HCl) and lysozyme in tears/saliva', 'Skin and mucous membranes', 'Polymorphonuclear leukocytes', 'Interferons'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Stomach acidity (pH 1.5–2) and antimicrobial lysozyme constitute physiological barriers of innate immunity.'},
    {'q': 'The immunoglobulin isotype that mediates Type I hypersensitivity allergic reactions and binds to tissue mast cells is:', 'opts': ['IgE', 'IgG', 'IgA', 'IgM'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'IgE binds high-affinity Fc receptors on mast cells and basophils, triggering degranulation and histamine release.'},
    {'q': 'Graft rejection in tissue and organ transplantation is primarily mediated by:', 'opts': ['Cell-mediated immunity (T-lymphocytes)', 'Humoral antibodies (B-cells)', 'Complement system alone', 'Phagocytic neutrophils'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Cytotoxic T-lymphocytes recognize foreign major histocompatibility complex (MHC) antigens, destroying allografts.'},
    {'q': 'Cannabinoid receptors in the human body are predominantly localized in the:', 'opts': ['Brain central nervous system', 'Cardiovascular system', 'Liver parenchyma', 'Renal cortex'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Cannabinoids (charas, ganja, hashish) interact with CB1 receptors in the brain affecting coordination and mood.'},
    {'q': 'Cocaine is an alkaloid obtained from Erythroxylum coca that produces euphoria and hallucinations by interfering with the transport of:', 'opts': ['Dopamine', 'Serotonin', 'Acetylcholine', 'GABA'], 'ans': 0, 'topic': 'Human Health and Disease', 'subtype': 'theory_definition', 'exp': 'Cocaine blocks dopamine reuptake transporters in synaptic clefts, inducing intense dopamine stimulation.'},
    {'q': 'Downstream processing in biochemical biotechnology refers to which final operations?', 'opts': ['Separation, purification, and clinical formulation of the biosynthesized product', 'Gene cloning in plasmid', 'PCR amplification of DNA', 'Electroporation into host cell'], 'ans': 0, 'topic': 'Biotechnology: Principles and Processes', 'subtype': 'theory_definition', 'exp': 'Downstream processing isolates and purifies the recombinant product from fermented culture broths.'},
    {'q': 'Which cloning vector is engineered from the tumor-inducing (Ti) plasmid to deliver recombinant genes into dicot plants?', 'opts': ['Agrobacterium tumefaciens Ti plasmid', 'Escherichia coli pUC19', 'Bacteriophage lambda', 'Yeast Artificial Chromosome (YAC)'], 'ans': 0, 'topic': 'Biotechnology: Principles and Processes', 'subtype': 'theory_definition', 'exp': 'The disarmed Ti-plasmid of Agrobacterium tumefaciens naturally transfers T-DNA into host plant genomes.'},
    {'q': 'The Cry endotoxin protein produced by Bacillus thuringiensis is toxic to insects because:', 'opts': ['It is solubilized by alkaline pH in the insect midgut and creates pores in epithelial cells', 'It inhibits RNA polymerase', 'It destroys insect cuticle', 'It coagulates insect hemolymph'], 'ans': 0, 'topic': 'Biotechnology and its Applications', 'subtype': 'theory_definition', 'exp': 'Alkaline insect midgut pH solubilizes protoxin crystals into active toxins that perforate midgut epithelial cells.'},
    {'q': 'ELISA (Enzyme-Linked Immunosorbent Assay) is a widely used diagnostic technique based on the principle of:', 'opts': ['Antigen-antibody interaction', 'DNA hybridization', 'Agarose electrophoresis', 'Spectrophotometry'], 'ans': 0, 'topic': 'Biotechnology and its Applications', 'subtype': 'theory_definition', 'exp': 'ELISA quantifies analyte concentrations via specific antigen-antibody binding coupled to enzymatic color production.'},
    {'q': 'The phenomenon of biopiracy refers to the:', 'opts': ['Unauthorized commercial exploitation of bioresources and traditional knowledge without permission or compensation', 'Illegal hunting of endangered animals', 'Smuggling of forest timber', 'Release of synthetic pathogens'], 'ans': 0, 'topic': 'Biotechnology and its Applications', 'subtype': 'theory_definition', 'exp': 'Biopiracy is the patenting of indigenous biodiversity (e.g., Basmati rice, Neem, Turmeric) without benefit sharing.'},
    {'q': 'In ecological succession on bare rock (xerarch succession), the pioneer species that colonize first are:', 'opts': ['Crustose and foliose lichens', 'Mosses', 'Perennial grasses', 'Annual herbs'], 'ans': 0, 'topic': 'Ecosystem', 'subtype': 'theory_definition', 'exp': 'Crustose lichens secrete organic carbonic acids that corrode rock into pioneer mineral soil.'},
    {'q': 'Net Primary Productivity (NPP) in an ecosystem is related to Gross Primary Productivity (GPP) by the equation:', 'opts': ['NPP = GPP - R (Respiratory losses)', 'NPP = GPP + R', 'NPP = GPP / R', 'NPP = R - GPP'], 'ans': 0, 'topic': 'Ecosystem', 'subtype': 'theory_definition', 'exp': 'Net primary productivity is the total biomass accumulated by autotrophs after subtracting respiratory maintenance (R).'},
    {'q': 'The inverted pyramid of biomass is characteristically observed in which ecosystem?', 'opts': ['Open ocean / Marine ecosystem', 'Tropical rainforest', 'Grassland', 'Desert'], 'ans': 0, 'topic': 'Ecosystem', 'subtype': 'theory_definition', 'exp': 'Marine phytoplankton have rapid turnover, so standing crop biomass is smaller than that of zooplankton and fish.'},
    {'q': 'The latitudinal gradient of biodiversity shows that species richness:', 'opts': ['Decreases progressively from the equator toward the polar regions', 'Increases toward the poles', 'Remains uniform everywhere', 'Peaks in temperate deserts'], 'ans': 0, 'topic': 'Biodiversity and Conservation', 'subtype': 'theory_definition', 'exp': 'Tropical regions near the equator receive constant solar energy and harbored evolutionary stability, yielding maximum species diversity.'},
    {'q': 'Sacred groves in India (e.g., Khasi and Jaintia Hills in Meghalaya, Aravalli hills in Rajasthan) are traditional sites of:', 'opts': ['In-situ biodiversity conservation protected by religious beliefs', 'Ex-situ botanical collections', 'Intensive agricultural farming', 'Commercial tree harvesting'], 'ans': 0, 'topic': 'Biodiversity and Conservation', 'subtype': 'theory_definition', 'exp': 'Sacred groves are communal virgin forest patches venerated by indigenous tribal clans, safeguarding rare endemic flora.'},
]
BIOLOGY_BANK.extend(_EXTRA_BIO)

from .uploaded_chapters_bio_bank import UPLOADED_CHAPTERS_BIO_BANK
BIOLOGY_BANK.extend(UPLOADED_CHAPTERS_BIO_BANK)

__all__ = ["BIOLOGY_BANK", "UPLOADED_CHAPTERS_BIO_BANK"]


