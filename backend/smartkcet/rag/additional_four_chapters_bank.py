"""High-yield supplementary NCERT / KCET questions for the 4 core Biology chapters:
1. Principles of Inheritance and Variation (+30 questions)
2. Human Reproduction (+20 questions)
3. Molecular Basis of Inheritance (+20 questions)
4. Sexual Reproduction in Flowering Plants (+20 questions)
"""

ADDITIONAL_FOUR_CHAPTERS_QS = [
    # ── Principles of Inheritance and Variation (+30 questions) ──
    {
        "q": "Which of the following Mendelian traits in garden pea (Pisum sativum) is recessive?",
        "opts": ["Constricted pod shape", "Round seed shape", "Yellow seed color", "Axial flower position"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Inflated pod is dominant over constricted pod shape in garden pea."
    },
    {
        "q": "The phenotypic dihybrid test cross ratio for two unlinked genes assorting independently is:",
        "opts": ["1 : 1 : 1 : 1", "9 : 3 : 3 : 1", "3 : 1", "1 : 2 : 1"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Crossing a dihybrid (AaBb) with a homozygous recessive tester (aabb) yields 1 AaBb : 1 Aabb : 1 aaBb : 1 aabb."
    },
    {
        "q": "In pea plants, yellow seed color (Y) is dominant over green (y) and round seed shape (R) is dominant over wrinkled (r). What proportion of F2 progeny in a dihybrid cross will be recombinant phenotypes (round green and wrinkled yellow)?",
        "opts": ["6/16 (3/8)", "9/16", "1/16", "10/16"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "In F2: 9 round yellow (parental), 3 round green (recombinant), 3 wrinkled yellow (recombinant), 1 wrinkled green (parental). Recombinants = 6/16."
    },
    {
        "q": "A heterozygous tall pea plant (Tt) with red flowers (Rr) is self-pollinated. The proportion of dwarf plants with red flowers in progeny is:",
        "opts": ["3/16", "9/16", "1/16", "6/16"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Dwarf (tt) probability = 1/4; Red flowers (R_) probability = 3/4. Combined probability = 1/4 * 3/4 = 3/16."
    },
    {
        "q": "Morgan observed 1.3% recombination between the genes for yellow body (y) and white eyes (w) in Drosophila, but 37.2% between white eyes (w) and miniature wings (m). This indicated that:",
        "opts": ["Genes y and w are located very close together on the X chromosome compared to w and m", "Genes w and m are on different chromosomes", "Genes y and w assort independently", "Miniature wing gene is on an autosome"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Lower recombination frequency indicates tighter physical linkage between genes located close together on the same chromosome."
    },
    {
        "q": "In grasshoppers, sex determination is of the XO type where:",
        "opts": ["Males have one X chromosome (XO) and females have two X chromosomes (XX)", "Females have XO and males have XX", "Males have XY and females have XX", "Males are ZZ and females are ZW"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "In XO sex determination, all eggs have an X chromosome, but sperm either carry an X (50%) or no sex chromosome (50%)."
    },
    {
        "q": "A man with normal color vision marries a woman who is a carrier for red-green color blindness. What percentage of their sons are expected to be color blind?",
        "opts": ["50%", "25%", "100%", "0%"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Mother is X^C X^c and father is X^C Y. Sons receive Y from father and either X^C (normal, 50%) or X^c (color blind, 50%) from mother."
    },
    {
        "q": "A color blind man marries a woman with normal vision whose father was color blind. What is the probability that their first child will be a color blind girl?",
        "opts": ["25% (1/4)", "50%", "0%", "12.5%"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Father is X^c Y; mother is carrier X^C X^c. Girls receive X^c from father and either X^C (carrier) or X^c (color blind) from mother. P(girl) = 1/2, P(X^c from mother) = 1/2 -> 1/4."
    },
    {
        "q": "The gene for sickle cell anemia is a classic example of pleiotropy because in the homozygous state (HbS HbS) it leads to:",
        "opts": ["Abnormal hemoglobin, sickling of erythrocytes, anemia, spleen damage, and resistance to malaria in heterozygotes", "Only pale skin color", "Only reduced height", "Only impaired hearing"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "A single nucleotide substitution creates a pleiotropic cascade affecting RBC shape, blood flow, organ damage, and falciparum resistance."
    },
    {
        "q": "In humans, which of the following syndromes is an example of aneuploidy caused by non-disjunction of autosomes?",
        "opts": ["Down syndrome", "Turner syndrome", "Klinefelter syndrome", "Cri-du-chat syndrome"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Down syndrome results from trisomy of autosome 21, whereas Turner and Klinefelter are sex-chromosome aneuploidies."
    },
    {
        "q": "Cri-du-chat (cat's cry) syndrome in humans is caused by which structural chromosomal aberration?",
        "opts": ["Deletion of short arm of chromosome 5", "Duplication on chromosome 9", "Inversion in chromosome 11", "Translocation between chromosomes 9 and 22"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Partial deletion of the short arm (p arm) of chromosome 5 causes infant high-pitched cat-like crying and microcephaly."
    },
    {
        "q": "Philadelphia chromosome, characteristically observed in patients with Chronic Myelogenous Leukemia (CML), results from reciprocal translocation between chromosomes:",
        "opts": ["9 and 22", "14 and 21", "8 and 14", "13 and 15"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Reciprocal translocation t(9;22)(q34;q11) fuses BCR and ABL1 genes creating the Philadelphia oncogenic kinase."
    },
    {
        "q": "Which of the following disorders is an inborn autosomal recessive error of metabolism resulting in dark black urine upon standing?",
        "opts": ["Alkaptonuria", "Phenylketonuria", "Albinism", "Cystinuria"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Alkaptonuria is caused by homogentisate 1,2-dioxygenase deficiency; homogentisic acid oxidizes in air to alkapton, turning urine black."
    },
    {
        "q": "Beta-thalassemia is an autosomal recessive disorder caused by mutations in the HBB gene located on human chromosome:",
        "opts": ["11", "16", "21", "13"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Beta-globin gene cluster is situated on short arm of chromosome 11; alpha-globin cluster is on chromosome 16."
    },
    {
        "q": "Alpha-thalassemia is controlled by two closely linked genes (HBA1 and HBA2) on chromosome 16. Total loss of all 4 alpha globin alleles leads to:",
        "opts": ["Hydrops fetalis (Hb Barts)", "Thalassemia minor", "Mild anemia", "Sickle cell trait"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Deletion of all 4 alpha genes causes severe fetal hydrops fetalis with high-affinity gamma-4 tetramers (Hb Barts) resulting in stillbirth."
    },
    {
        "q": "What is the expected phenotypic ratio in the F2 generation of a cross involving two genes that exhibit complete linkage (no crossing over)?",
        "opts": ["3 : 1", "9 : 3 : 3 : 1", "1 : 2 : 1", "1 : 1 : 1 : 1"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "With complete linkage, the two genes segregate as a single unit without recombination, yielding a 3:1 monohybrid F2 phenotypic ratio."
    },
    {
        "q": "In Mirabilis jalapa (four o'clock plant), crossing a red-flowered plant with a pink-flowered plant yields progeny in the ratio:",
        "opts": ["1 Red : 1 Pink", "1 Red : 2 Pink : 1 White", "All pink", "3 Red : 1 Pink"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Cross is RR (red) x Rr (pink). Offspring genotypes are 1/2 RR (red) and 1/2 Rr (pink), giving a 1:1 phenotypic ratio."
    },
    {
        "q": "The probability of having a child with blood group O from parents who both have blood group A is:",
        "opts": ["25% if both parents are heterozygous (IA i)", "50%", "0%", "100%"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "If both parents are IA i, the Punnett square produces 1/4 IA IA, 1/2 IA i, and 1/4 ii (blood group O)."
    },
    {
        "q": "Gynandromorphs in Drosophila (individuals possessing both male and female body sectors) arise primarily due to:",
        "opts": ["Loss of one X chromosome during early embryonic cleavage mitosis in an XX zygote", "Nondisjunction of Y chromosome", "Hormonal reversal during pupation", "Translocation to autosome"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Loss of an X chromosome in a cell during first mitotic divisions produces an XO lineage (male phenotype) alongside XX (female)."
    },
    {
        "q": "In human genetics, hypertrichosis (excessive hair on pinna of the ear) is inherited as a:",
        "opts": ["Y-linked (holandric) trait", "X-linked recessive trait", "Autosomal dominant trait", "Mitochondrial trait"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Holandric genes are present on non-homologous region of the Y chromosome and transmit strictly from father to all sons."
    },
    {
        "q": "Which of the following is true regarding human female sex chromosomes during interphase somatic cells?",
        "opts": ["One of the two X chromosomes is heterochromatinized and condensed into a dark Barr body", "Both X chromosomes remain fully active euchromatin", "Neither X chromosome forms a Barr body", "The Y chromosome forms the Barr body"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Mary Lyon hypothesis explains dosage compensation: one X chromosome is randomly inactivated into a condensed Barr body."
    },
    {
        "q": "How many Barr bodies are present in the somatic cells of a male with Klinefelter syndrome (47, XXY)?",
        "opts": ["1 Barr body", "0 Barr bodies", "2 Barr bodies", "3 Barr bodies"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Number of Barr bodies = Total X chromosomes - 1. For 47, XXY: 2 - 1 = 1 Barr body."
    },
    {
        "q": "How many Barr bodies are present in a female with Turner syndrome (45, XO)?",
        "opts": ["0 Barr bodies", "1 Barr body", "2 Barr bodies", "3 Barr bodies"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Total X chromosomes = 1; 1 - 1 = 0 Barr bodies."
    },
    {
        "q": "The gene causing Huntington disease shows anticipation, which means that:",
        "opts": ["Symptoms appear at an earlier age and with greater severity in successive generations due to CAG trinucleotide expansion", "The gene mutates into a recessive allele", "The gene jumps to the X chromosome", "Symptoms disappear in grand-progeny"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Trinucleotide CAG repeats expand during gametogenesis, causing earlier and more severe neurological onset."
    },
    {
        "q": "A cross between AaBb and aabb produces 90 AaBb, 10 Aabb, 10 aaBb, and 90 aabb. What is the recombination frequency between genes A and B?",
        "opts": ["10%", "20%", "5%", "45%"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Recombinant progeny = 10 + 10 = 20. Total progeny = 90 + 10 + 10 + 90 = 200. Recombination frequency = (20 / 200) * 100 = 10%."
    },
    {
        "q": "In polygenic inheritance of wheat kernel color studied by Nilsson-Ehle, crossing dark red (AABB) with white (aabb) yields an F2 phenotypic ratio of:",
        "opts": ["1 : 4 : 6 : 4 : 1", "9 : 3 : 3 : 1", "1 : 2 : 1", "15 : 1"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Two additive gene pairs yield 5 phenotypic classes in F2: 1 dark red : 4 medium-dark red : 6 medium red : 4 light red : 1 white."
    },
    {
        "q": "The standard test organism used by Thomas Hunt Morgan that earned him the title 'Father of Experimental Genetics' was:",
        "opts": ["Drosophila melanogaster", "Neurospora crassa", "Caenorhabditis elegans", "Escherichia coli"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "T.H. Morgan established linkage, crossing over, and sex linkage using Drosophila melanogaster."
    },
    {
        "q": "In a cross between two individuals heterozygous for sickle cell trait (HbA HbS x HbA HbS), what fraction of their viable adult offspring are expected to be sickle cell carriers in a malaria-endemic region?",
        "opts": ["2/3 of viable survivors", "1/2", "1/4", "3/4"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "multi_step",
        "exp": "Progeny genotypic ratio is 1 HbA HbA : 2 HbA HbS : 1 HbS HbS. Homozygous HbS HbS suffer lethal severe anemia, leaving 2/3 of viable survivors as carriers."
    },
    {
        "q": "Mendel's Law of Segregation is universally applicable without exception because:",
        "opts": ["Homologous chromosomes and alleles segregate into separate gametes during anaphase I of meiosis", "Crossing over does not affect allele separation", "Alleles never blend in heterozygous individuals", "Gametes always receive both parental alleles"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "Alleles do not blend; during meiosis, homologous chromosome pairs disjoin into separate gametes so each gamete is pure."
    },
    {
        "q": "Who coined the terms 'genetics', 'allele', and 'heterozygote' in classical biology?",
        "opts": ["William Bateson", "Gregor Mendel", "Hugo de Vries", "Wilhelm Johannsen"],
        "ans": 0, "topic": "Principles of Inheritance and Variation", "subtype": "theory_definition",
        "exp": "William Bateson coined the term 'Genetics' in 1905 and introduced allele, homozygous, and heterozygous."
    },

    # ── Human Reproduction (+20 questions) ──
    {
        "q": "The temperature of testes in the scrotum is maintained lower than the body core by the counter-current heat exchange mechanism of the:",
        "opts": ["Pampiniform venous plexus", "Cremaster muscle alone", "Dartos muscle alone", "Tunica albuginea"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Pampiniform plexus of veins surrounds the testicular artery, absorbing heat to maintain testicular temperature 2-2.5 °C below core."
    },
    {
        "q": "During human spermiogenesis, the non-motile round spermatids are transformed into mature motile spermatozoa by:",
        "opts": ["Condensation of nucleus, acrosome formation from Golgi, and growth of axial filament flagellum", "Meiotic cell division II", "Mitotic proliferation", "Degeneration of cytoplasm only"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Spermiogenesis involves morphogenetic differentiation of spermatids into spermatozoa without any further cell division."
    },
    {
        "q": "The release of mature spermatozoa from the luminal surface of Sertoli cells into the cavity of seminiferous tubules is termed:",
        "opts": ["Spermiation", "Insemination", "Ejaculation", "Spermiogenesis"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Spermiation is the detachment and shedding of spermatozoa from Sertoli nursing cells into the tubule lumen."
    },
    {
        "q": "In a healthy human adult male ejaculate of ~3 to 4 mL, for normal fertility what percentage of sperms must show normal shape and vigorous motility?",
        "opts": ["At least 60% must have normal shape and at least 40% of them must show vigorous motility", "100% normal shape and motility", "50% normal shape and 50% motility", "80% normal shape and 20% motility"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "According to NCERT: ejaculate contains 200-300 million sperms; 60% must show normal morphology and at least 40% must show vigorous forward motility."
    },
    {
        "q": "Oogenesis is initiated during which stage of human female life?",
        "opts": ["Embryonic fetal development (prior to birth)", "At puberty (menarche)", "During childhood", "At first sexual intercourse"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "A couple of million oogonia are formed in each fetal ovary before birth; no new oogonia are ever formed or added after birth."
    },
    {
        "q": "Primary oocytes remain arrested in which meiotic stage from embryonic development until ovulation occurs after puberty?",
        "opts": ["Prophase I (Diplotene stage)", "Metaphase I", "Anaphase II", "Telophase I"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Primary oocytes enter meiotic division I and become suspended in diplotene stage of prophase I until stimulated by LH surge."
    },
    {
        "q": "The fluid-filled cavity characteristic of the mature tertiary and Graafian ovarian follicle is called the:",
        "opts": ["Antrum", "Corona radiata", "Theca interna", "Blastocoel"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Antrum is the follicular fluid (liquor folliculi) filled cavity that distinguishes tertiary follicles from secondary follicles."
    },
    {
        "q": "Ovulation in a typical 28-day human menstrual cycle is triggered by a sudden surge in which gonadotropic hormone?",
        "opts": ["Luteinizing Hormone (LH)", "Follicle Stimulating Hormone (FSH)", "Progesterone", "Human Chorionic Gonadotropin (hCG)"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Rapid secretion of LH midway through the cycle (LH surge around day 14) induces rupture of the Graafian follicle and ovum release."
    },
    {
        "q": "After ovulation, the ruptured Graafian follicle is transformed under LH influence into an endocrine structure termed:",
        "opts": ["Corpus luteum", "Corpus albicans", "Corpus callosum", "Zona glomerulosa"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Luteal granulosa and theca cells hypertrophy to form the yellow corpus luteum, which secretes massive amounts of progesterone."
    },
    {
        "q": "In the absence of pregnancy and fertilization, the corpus luteum degenerates into a fibrous white scar known as:",
        "opts": ["Corpus albicans", "Corpus luteum of pregnancy", "Atretic follicle", "Macula densa"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "In unfertilized cycles, LH drop induces corpus luteum regression into an inactive fibrous scar called corpus albicans."
    },
    {
        "q": "The proliferative or follicular phase of the human menstrual cycle is characterized by uterine endometrial repair driven by:",
        "opts": ["Estrogen secreted by growing ovarian follicles", "Progesterone from corpus luteum", "Oxytocin from posterior pituitary", "Prolactin from anterior pituitary"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Growing ovarian follicles secrete rising levels of estradiol (estrogen), regenerating the sloughed endometrial lining via mitotic proliferation."
    },
    {
        "q": "Sperm capacitation occurs inside the female reproductive tract and involves:",
        "opts": ["Removal of cholesterol and inhibitory glycoproteins from the sperm acrosomal membrane to allow fertilization", "Acrosome loss", "Mitotic division of sperm", "Flagellar shedding"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Capacitation takes ~7 hours in the female tract, washing away decapacitation factors from the acrosome surface and increasing motility."
    },
    {
        "q": "The fast block to polyspermy during human fertilization is achieved by:",
        "opts": ["Rapid depolarization of the ovum plasma membrane through sodium ion influx", "Cortical granule exocytosis", "Hardening of the zona pellucida", "Acrosome reaction"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Sperm binding triggers instantaneous membrane depolarization from -70 mV to +20 mV via Na+ influx, repelling additional sperm."
    },
    {
        "q": "The slow block to polyspermy (cortical reaction) involves:",
        "opts": ["Exocytosis of cortical granules releasing enzymes that harden the zona pellucida (zona reaction)", "Membrane hyperpolarization", "Sperm head phagocytosis", "Formation of fertilization cone"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Intracellular Ca2+ wave induces cortical granules to secrete enzymes that cleave ZP receptors, permanently blocking polyspermy."
    },
    {
        "q": "Cleavage divisions of the human zygote are described as:",
        "opts": ["Holoblastic, equal to slightly unequal, and indeterminate", "Meroblastic superficial", "Discoidal meroblastic", "Spiral determinate"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Human eggs are microlecithal; cleavage planes completely divide the egg (holoblastic) producing blastomeres."
    },
    {
        "q": "The solid mulberry-shaped ball of 8 to 16 blastomeres formed ~3 days after fertilization is called the:",
        "opts": ["Morula", "Blastocyst", "Gastrula", "Neurula"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Morula (Latin for mulberry) consists of 8-16 compact blastomeres enclosed within the intact zona pellucida."
    },
    {
        "q": "Implantation of the human embryo into the uterine endometrium occurs at which developmental stage?",
        "opts": ["Blastocyst (Blastula) stage (~day 6 to 7 post-fertilization)", "Morula stage", "Gastrula stage", "Zygote stage"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "The blastocyst hatches from the zona pellucida and its outer trophoblast layer attaches to the receptive uterine endometrium."
    },
    {
        "q": "The outer epithelial cell layer of the blastocyst that gives rise to chorionic villi and the embryonic placenta is the:",
        "opts": ["Trophoblast", "Inner cell mass (embryoblast)", "Amnion", "Allantois"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Trophoblast cells invade maternal endometrium, forming syncytiotrophoblast and chorionic villi of the placenta."
    },
    {
        "q": "Human Chorionic Gonadotropin (hCG), the hormone detected in standard clinical pregnancy test kits, is secreted by the:",
        "opts": ["Trophoblast / Syncytiotrophoblast of developing placenta", "Maternal corpus luteum", "Fetal adrenal cortex", "Anterior pituitary gland"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "Syncytiotrophoblast secretes hCG, which rescues the corpus luteum from regression so progesterone levels stay elevated."
    },
    {
        "q": "Which of the following hormones is produced in human females ONLY during pregnancy?",
        "opts": ["Human Placental Lactogen (hPL), hCG, and Relaxin", "Estrogen and Progesterone", "LH and FSH", "Prolactin and Oxytocin"],
        "ans": 0, "topic": "Human Reproduction", "subtype": "theory_definition",
        "exp": "hCG, hPL, and placental relaxin are synthesized exclusively during pregnancy by placental and gestational tissues."
    },

    # ── Molecular Basis of Inheritance (+20 questions) ──
    {
        "q": "In a nucleosome, the DNA is wrapped around the histone octamer in approximately:",
        "opts": ["1.65 turns (encompassing ~146 to 200 base pairs of DNA)", "3.5 turns", "5 full turns", "Half a turn"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "DNA wraps 1.65 left-handed superhelical turns (~147 bp in core particle, ~200 bp with linker DNA) around the octamer."
    },
    {
        "q": "Which linker histone binds the outer entry and exit site of DNA on the nucleosome core particle?",
        "opts": ["Histone H1", "Histone H2A", "Histone H3", "Histone H4"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Histone H1 seals the entering and exiting DNA strands to stabilize higher-order 30-nm chromatin solenoid fibers."
    },
    {
        "q": "Frederick Griffith (1928) discovered the phenomenon of bacterial transformation using which organism?",
        "opts": ["Streptococcus pneumoniae (Pneumococcus)", "Escherichia coli", "Salmonella typhimurium", "Bacteriophage T2"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Griffith demonstrated that heat-killed smooth (S-strain) transformed live rough (R-strain) into pathogenic virulent smooth bacteria."
    },
    {
        "q": "Oswald Avery, Colin MacLeod, and Maclyn McCarty (1944) established that the 'transforming principle' was DNA by showing that transformation was destroyed ONLY by:",
        "opts": ["Deoxyribonuclease (DNase)", "Ribonuclease (RNase)", "Proteases (Trypsin and Chymotrypsin)", "Lipases"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Digestion with proteases and RNase did not affect transformation, whereas DNase completely abolished transforming activity."
    },
    {
        "q": "Alfred Hershey and Martha Chase (1952) proved that DNA is the genetic material of bacteriophage T2 using radioactive isotopes:",
        "opts": ["32P to label DNA and 35S to label protein coats", "15N to label DNA and 14C to label protein", "3H to label DNA and 32P to label protein", "35S to label DNA and 32P to label protein"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Phosphate occurs in DNA but not protein (32P); sulfur occurs in methionine/cysteine of proteins but not DNA (35S)."
    },
    {
        "q": "Matthew Meselson and Franklin Stahl (1958) demonstrated semiconservative replication of DNA in E. coli using density gradient centrifugation in:",
        "opts": ["Cesium chloride (CsCl) gradient after growing bacteria in 15NH4Cl and transferring to 14NH4Cl", "Sucrose density gradient", "Agarose gel electrophoresis", "Polyacrylamide gel"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "CsCl equilibrium density centrifugation distinguished heavy (15N-15N), hybrid (15N-14N), and light (14N-14N) DNA duplexes."
    },
    {
        "q": "DNA replication in living cells is initiated at specific sequence sites termed:",
        "opts": ["Origin of replication (ori)", "Promoter site", "Operator site", "Terminator region"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Ori sites are AT-rich sequences recognized by initiator proteins (DnaA in E. coli) where DNA unwinding begins."
    },
    {
        "q": "During DNA replication, the leading strand is synthesized continuously, while the lagging strand is synthesized discontinuously as:",
        "opts": ["Okazaki fragments joined by DNA ligase", "Klenow fragments", "Primer fragments", "Restriction fragments"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Since DNA polymerase functions only in the 5'->3' direction, the anti-parallel lagging template is replicated in discontinuous Okazaki segments."
    },
    {
        "q": "The RNA primer required for initiating DNA synthesis in replication is synthesized by the enzyme:",
        "opts": ["RNA Primase (DNA-dependent RNA polymerase)", "DNA Polymerase I", "Topoisomerase", "Helicase"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "DNA polymerases cannot synthesize de novo without a free 3'-OH group, which is supplied by RNA primase."
    },
    {
        "q": "Which enzyme relieves the torsional strain and positive supercoiling ahead of the replicating DNA fork?",
        "opts": ["Topoisomerase (DNA Gyrase in prokaryotes)", "DNA Helicase", "Single-Stranded Binding Protein (SSB)", "DNA Ligase"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Topoisomerases cut and swivel DNA strands to relieve superhelical tension generated by helicase unwinding."
    },
    {
        "q": "In eukaryotic transcription, ribosomal RNA (28S, 18S, and 5.8S rRNA) is synthesized by:",
        "opts": ["RNA Polymerase I", "RNA Polymerase II", "RNA Polymerase III", "Reverse Transcriptase"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "RNA Polymerase I transcribes large rRNAs (28S, 18S, 5.8S); Pol II transcribes mRNA/hnRNA; Pol III transcribes tRNA and 5S rRNA."
    },
    {
        "q": "The promoter sequence recognized by RNA Polymerase II in eukaryotic transcription is the TATA box (Hogness box) centered at approximately:",
        "opts": ["-25 to -30 bp upstream of the transcription start site (+1)", "-10 bp upstream (Pribnow box)", "-70 bp upstream", "+10 bp downstream"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "The TATA box is located at -25 to -30 in eukaryotes; the bacterial counterpart is the Pribnow box at -10."
    },
    {
        "q": "Splicing of eukaryotic pre-mRNA involves the removal of non-coding intervening sequences termed:",
        "opts": ["Introns (with joining of coding exons)", "Exons (with joining of introns)", "Cistrons", "Codons"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Spliceosomes excise non-coding introns and ligate coding exons together to form mature translatable mRNA."
    },
    {
        "q": "The initiator codon AUG encodes which amino acid in all living organisms during translation?",
        "opts": ["Methionine (Formyl-methionine in prokaryotes)", "Valine", "Tryptophan", "Phenylalanine"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "AUG has dual functions: it acts as the initiation codon and codes for methionine in eukaryotes (N-formylmethionine in prokaryotes)."
    },
    {
        "q": "Which of the following amino acids is encoded by only a single codon in the universal genetic code?",
        "opts": ["Tryptophan (UGG) and Methionine (AUG)", "Leucine and Serine", "Arginine and Alanine", "Lysine and Glycine"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Only two amino acids are encoded by a single codon: Methionine (AUG) and Tryptophan (UGG)."
    },
    {
        "q": "In the cloverleaf secondary structure of tRNA, the amino acid attachment site is located at the:",
        "opts": ["3' end with CCA-OH sequence", "5' end with G residue", "Anticodon loop", "D loop"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "The 3' terminal CCA-OH sequence acts as the aminoacyl acceptor stem where amino acids are covalently charged by aminoacyl-tRNA synthetase."
    },
    {
        "q": "In the lac operon of E. coli, the lac repressor protein is synthesized constitutively by the regulatory gene:",
        "opts": ["lac i gene", "lac z gene", "lac y gene", "lac a gene"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "The i gene (inhibitor) is transcribed constitutively to produce the tetrameric lac repressor protein."
    },
    {
        "q": "In the lac operon, allolactose acts as an:",
        "opts": ["Inducer that binds to the repressor protein, causing conformational change and preventing it from binding the operator", "Co-repressor", "Apoenzyme", "Promoter activator"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "Allolactose acts as an inducer: binding the repressor releases it from the operator DNA, derepressing operon transcription."
    },
    {
        "q": "According to the Human Genome Project (HGP), what percentage of the total human genome codes for functional proteins?",
        "opts": ["Less than 2%", "Over 50%", "About 25%", "85%"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "HGP revealed that less than 2% of the 3.1 billion base pairs in the human genome encodes amino acid polypeptide sequences."
    },
    {
        "q": "Sir Alec Jeffreys developed the technique of DNA fingerprinting based on identifying polymorphic variations in:",
        "opts": ["Variable Number of Tandem Repeats (VNTRs / Minisatellites)", "Ribosomal RNA genes", "Histone coding sequences", "Mitochondrial cytochrome b"],
        "ans": 0, "topic": "Molecular Basis of Inheritance", "subtype": "theory_definition",
        "exp": "DNA profiling utilizes hypervariable minisatellite tandem repeat (VNTR) copy number variations between individuals."
    },

    # ── Sexual Reproduction in Flowering Plants (+20 questions) ──
    {
        "q": "The innermost wall layer of the microsporangium that nourishes developing pollen grains is the:",
        "opts": ["Tapetum", "Endothecium", "Middle layers", "Epidermis"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Tapetal cells are dense with cytoplasm and often multinucleate, nourishing developing microspore mother cells and pollen."
    },
    {
        "q": "The cells of which microsporangial wall layer develop fibrous alpha-cellulosic bands that facilitate anther dehiscence at maturity?",
        "opts": ["Endothecium", "Epidermis", "Middle layers", "Tapetum"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Hygroscopic radial cellulosic fibrous thickenings in endothecium cells shrink upon drying, rupturing the stomium for pollen release."
    },
    {
        "q": "The exceptionally resistant organic biopolymer constituting the hard outer exine of pollen grains is:",
        "opts": ["Sporopollenin", "Cellulose", "Pectocellulose", "Chitin"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Sporopollenin is an oxidative polymer of carotenoids that withstands strong acids, bases, and high temperatures, preserving fossil pollen."
    },
    {
        "q": "The aperture regions on the pollen grain exine where sporopollenin is absent are called:",
        "opts": ["Germ pores", "Stomium", "Micropyle", "Chalaza"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Germ pores are circular apertures where sporopollenin is absent, allowing the pollen tube to emerge during germination."
    },
    {
        "q": "In over 60% of angiosperms, pollen grains are shed at which developmental stage?",
        "opts": ["2-celled stage (Vegetative cell and Generative cell)", "3-celled stage", "4-celled stage", "1-celled microspore stage"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "In >60% of angiosperms, pollen is shed at the 2-celled stage; in the remaining ~40%, the generative cell divides into two male gametes before shedding (3-celled)."
    },
    {
        "q": "Pollen grains of cereals like wheat and rice lose their viability within approximately:",
        "opts": ["30 minutes after shedding", "Several months", "24 hours", "A full year"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Wheat and rice pollen grains lose viability within 30 minutes, whereas members of Rosaceae, Leguminosae, and Solanaceae remain viable for months."
    },
    {
        "q": "Cryopreservation of pollen grains for long-term storage in pollen banks is carried out in liquid nitrogen at:",
        "opts": ["-196 °C", "-80 °C", "-20 °C", "-30 °C"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Liquid nitrogen at -196 °C (-320 °F) arrests all metabolic activity, preserving pollen viability for crop breeding programs."
    },
    {
        "q": "The most common anatomical type of ovule in more than 82% of angiosperm families is:",
        "opts": ["Anatropous (inverted ovule with micropyle close to hilum)", "Orthotropous (straight ovule)", "Campylotropous", "Hemianatropous"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "In anatropous ovules, the body is inverted 180 degrees so the micropyle and funicle lie closely adjacent near the hilum."
    },
    {
        "q": "A typical mature angiosperm female gametophyte (embryo sac) at maturity consists of:",
        "opts": ["7 cells and 8 nuclei (Polygonum type)", "8 cells and 8 nuclei", "7 cells and 7 nuclei", "6 cells and 8 nuclei"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Monosporic Polygonum embryo sac has 3 antipodal cells, 1 binucleate central cell, 2 synergids, and 1 egg cell = 7 cells, 8 nuclei."
    },
    {
        "q": "The cellular finger-like thickenings in the synergids that guide the pollen tube into the embryo sac are termed the:",
        "opts": ["Filiform apparatus", "Obturator", "Caruncle", "Aril"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "The filiform apparatus in synergids secretes chemotropic signals guiding the pollen tube into one of the synergids."
    },
    {
        "q": "Transfer of pollen grains from the anther to the stigma of the same flower is called:",
        "opts": ["Autogamy", "Geitonogamy", "Xenogamy", "Chasmogamy"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Autogamy is strict self-pollination occurring within the same individual flower."
    },
    {
        "q": "Geitonogamy is functionally cross-pollination involving a pollinator, but genetically it is equivalent to autogamy because:",
        "opts": ["The pollen grains come from the same parent plant", "The flowers have identical petals", "No seeds are produced", "It occurs only in unisexual trees"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Transfer of pollen to another flower on the same plant is genetically identical to self-pollination since both flowers share the same genotype."
    },
    {
        "q": "Which of the following adaptations is an outbreeding device preventing autogamy by maturing anthers and stigmas at different times?",
        "opts": ["Dichogamy (Protandry or Protogyny)", "Homogamy", "Cleistogamy", "Bud pollination"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Dichogamy ensures non-synchronous pollen release and stigma receptivity, promoting outcrossing."
    },
    {
        "q": "Double fertilization, a defining hallmark of angiosperms, was first discovered in Lilium and Fritillaria by:",
        "opts": ["S.G. Nawaschin (1898)", "E. Strasburger", "P. Maheshwari", "Robert Brown"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Sergei Nawaschin discovered double fertilization involving syngamy (syngamy) and triple fusion."
    },
    {
        "q": "During double fertilization in flowering plants, the two fusion events are:",
        "opts": ["Syngamy (Egg + Sperm -> 2n Zygote) and Triple Fusion (2 Polar nuclei + Sperm -> 3n PEN)", "Two sperm fusing with one egg", "One sperm fusing with two antipodals", "Fusion of synergids with central cell"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "One male gamete (n) fertilizes egg (n) forming diploid zygote (2n); second male gamete (n) fuses with 2 polar nuclei forming triploid PEN (3n)."
    },
    {
        "q": "The coconut water from tender coconut represents:",
        "opts": ["Free-nuclear endosperm", "Cellular endosperm", "Helobial endosperm", "Liquid embryo"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Coconut water is liquid free-nuclear endosperm containing thousands of free nuclei; surrounding white kernel is cellular endosperm."
    },
    {
        "q": "In albuminous (endospermic) seeds, endosperm tissue is retained in mature seeds to nourish germinating seedlings. Examples include:",
        "opts": ["Castor, Maize, Wheat, and Barley", "Pea, Gram, and Bean", "Groundnut and Tamarind", "Mustard and Sunflower"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Cereals (maize, wheat) and castor retain nutritive endosperm (albuminous); legumes (pea, bean) consume it completely (exalbuminous)."
    },
    {
        "q": "Persistent residual nucellus observed in seeds of black pepper and beet is called:",
        "opts": ["Perisperm", "Pericarp", "Endocarp", "Caruncle"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "In some species (black pepper, beet), remnants of the diploid nucellus persist as nutritive perisperm around the embryo."
    },
    {
        "q": "Apple, strawberry, and cashew are termed 'false fruits' (pseudocarps) because:",
        "opts": ["The fleshy edible portion develops from the floral thalamus rather than the ovary alone", "They develop without fertilization", "They lack seeds", "They grow on roots"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "In false fruits, floral parts other than the ovary (such as the thalamus/receptacle) hypertrophy to form the fleshy edible fruit."
    },
    {
        "q": "The development of seeds without fertilization, mimicking sexual reproduction as observed in Asteraceae and grasses, is termed:",
        "opts": ["Apomixis", "Parthenocarpy", "Polyembryony", "Amphimixis"],
        "ans": 0, "topic": "Sexual Reproduction in Flowering Plants", "subtype": "theory_definition",
        "exp": "Apomixis is asexual seed formation bypassing meiosis and fertilization, allowing maternal genotypes to clone true to type."
    },
]
