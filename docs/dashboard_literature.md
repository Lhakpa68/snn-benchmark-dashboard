# Dashboard Literature for the Thesis Literature Review

Peer-reviewed sources for the dashboard side of the literature review, organised
by the five areas the supervisor named. **22 sources**, minimum 3 per area.

Every entry below was located and its full text opened and read before being
listed. The "Free full text confirmed at" line records the exact URL at which the
complete document (not an abstract) was read. Where an author's or repository
copy omits the final volume/page metadata, the bibliographic details were taken
from the publisher/index record, which is noted.

Selection rules applied:

- Peer-reviewed journal article, paper in a refereed conference/workshop
  proceedings, or peer-reviewed book chapter only. No blogs, vendor material,
  unpublished preprints, or theses.
- Full text freely readable at the stated URL, confirmed by fetching and reading
  the document.

Cross-cutting flags for the three specific questions asked (evaluation without a
user study, figure readability, insufficiency of static tables) are collected in
the closing section, §6.

---

## 1. Information visualization literature

### 1.1 Shneiderman (1996) — Task by data type taxonomy

**Reference.**
B. Shneiderman, "The eyes have it: A task by data type taxonomy for information
visualizations," in *Proc. 1996 IEEE Symposium on Visual Languages (VL '96)*,
Boulder, CO, USA, 1996, pp. 336–343, doi: 10.1109/VL.1996.545307.

**Free full text.** <https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf>
— author's copy, University of Maryland. Full body text read; pp. 336–343 present.

**What it says.** Shneiderman crosses seven data types (1-D, 2-D, 3-D, temporal,
multi-dimensional, tree, network) against seven user tasks — overview, zoom,
filter, details-on-demand, relate, history, extract — and argues an interface
should be assessed by which cells of that matrix it actually supports. The paper
states the Visual Information Seeking Mantra: "overview first, zoom and filter,
then details-on-demand." "Extract" and "history" are first-class tasks in the
taxonomy: the user must be able to pull out a selected sub-collection and retrace
the steps that produced the current view.

**Area served.** 1 (information visualization); underpins area 4.

**Connection to the thesis.** Gives a citable task vocabulary for why the
benchmarking dashboard shows an overview of all simulators/configurations first,
then filtering and per-run detail, and why export of the current selection is a
designed feature rather than a convenience.

### 1.2 Munzner (2009) — Nested model for visualization design and validation

**Reference.**
T. Munzner, "A nested model for visualization design and validation," *IEEE
Transactions on Visualization and Computer Graphics*, vol. 15, no. 6,
pp. 921–928, 2009, doi: 10.1109/TVCG.2009.111.

**Free full text.** <https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/NestedModel.pdf>
— UBC Imager Lab copy. Full body text read. (Volume/issue/pages from the TVCG
record.)

**What it says.** Munzner decomposes visualization design into four nested
levels — characterise the domain problem and data; abstract these into generic
operations and data types; design the visual encoding and interaction; design the
algorithm — and attaches a distinct validity threat to each: "wrong problem,"
"wrong abstraction," "wrong encoding/interaction," "wrong algorithm." Each level
has *immediate* validation methods usable before deployment (interviews and
observation at the domain level, justification against perceptual principles at
the encoding level, complexity analysis at the algorithm level) and *downstream*
methods requiring users or a deployed system (field study, lab study, adoption
counts). A validation method applied at the wrong level cannot address that
level's threat — the model's central warning.

**Area served.** 1 and 5.

**Connection to the thesis.** The cleanest published justification for organising
the dashboard chapter as problem → abstraction → encoding → implementation, and
for validating the encoding level analytically (against perceptual results) when
no user study is run.

### 1.3 Heer and Bostock (2010) — Crowdsourced graphical perception

**Reference.**
J. Heer and M. Bostock, "Crowdsourcing graphical perception: Using Mechanical
Turk to assess visualization design," in *Proc. SIGCHI Conf. Human Factors in
Computing Systems (CHI '10)*, Atlanta, GA, USA, 2010, pp. 203–212,
doi: 10.1145/1753326.1753357.

**Free full text.** <http://vis.stanford.edu/files/2010-MTurk-CHI.pdf>
— Stanford Visualization Group author copy. Full body text read.

**What it says.** The paper replicates Cleveland and McGill's encoding-accuracy
ranking — position judgments significantly outperform length judgments — and
extends it: rectangular-area judgments are as error-prone as circular-area
judgments, and aspect ratio matters, with square rectangles (aspect ratio 1)
giving the *worst* comparison performance. Two results are directly actionable
for figure layout: increasing chart height beyond roughly 80 pixels yields little
further accuracy benefit, and gridlines should be spaced at least about 8 pixels
apart to remain useful. These are quantitative, citable thresholds, not style
advice.

**Area served.** 1. Also a figure-readability source (§6.2).

**Connection to the thesis.** Supports choosing position-based encodings (bar and
dot plots on a common scale) for benchmark metrics over area-based ones, and gives
numeric backing for the dashboard's minimum chart height and gridline density.

### 1.4 Crameri, Shephard and Heron (2020) — The misuse of colour

**Reference.**
F. Crameri, G. E. Shephard, and P. J. Heron, "The misuse of colour in science
communication," *Nature Communications*, vol. 11, art. 5444, 2020,
doi: 10.1038/s41467-020-19160-7.

**Free full text.** <https://www.nature.com/articles/s41467-020-19160-7>
— open access (CC BY). Full text read.

**What it says.** Rainbow/jet colour maps introduce artificial visual boundaries
because yellow is the brightest colour and draws the eye, yet sits neither at the
centre nor at an endpoint of the scale; the authors quantify the resulting
distortion as visual error exceeding 7% of the displayed data variation. They note
that roughly 8% of men and 0.5% of women have a colour-vision deficiency, so
red–green encodings at similar brightness exclude a substantial share of readers.
They set out four required properties for a scientific colour map: perceptual
uniformity, intuitive perceptual ordering, readability under colour-vision
deficiency, and legibility when converted to greyscale.

**Area served.** 1. Also a figure-readability source (§6.2).

**Connection to the thesis.** Directly justifies the dashboard's colour choices
for per-simulator series and heat-map-style metric displays, and gives a citable
reason to reject a default rainbow scale in a thesis figure that will also be
printed in greyscale.

### 1.5 Nuñez, Anderton and Renslow (2018) — Colormaps for colour-vision deficiency

**Reference.**
J. R. Nuñez, C. R. Anderton, and R. S. Renslow, "Optimizing colormaps with
consideration for color vision deficiency to enable accurate interpretation of
scientific data," *PLoS ONE*, vol. 13, no. 7, art. e0199239, 2018,
doi: 10.1371/journal.pone.0199239.

**Free full text.** <https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0199239>
— open access. Full text read.

**What it says.** The authors give an explicit optimisation procedure (the
`cmaputil` module): convert a colormap to CIECAM02-UCS space, interpolate the a′
and b′ components for equal perceptual spacing, and linearise the J′ (brightness)
range within sRGB limits. They show concretely how jet misleads — bright yellow
regions read as the highest values when the actual maxima are the dark red ones —
and derive *cividis*, a colormap that "enables nearly-identical visual-data
interpretation" for readers with and without colour-vision deficiency. The
practical recommendation is monotonic-brightness, perceptually uniform maps such
as cividis or viridis.

**Area served.** 1. Also a figure-readability source (§6.2).

**Connection to the thesis.** Gives a named, defensible default palette for the
dashboard's continuous scales and a method-level (not merely aesthetic) argument
for it, which matters because benchmark figures will be read by reviewers whose
colour vision the thesis cannot assume.

---

## 2. Benchmark and performance-reporting dashboards

### 2.1 Isaacs et al. (2014) — State of the art of performance visualization

**Reference.**
K. E. Isaacs, A. Giménez, I. Jusufi, T. Gamblin, A. Bhatele, M. Schulz,
B. Hamann, and P.-T. Bremer, "State of the art of performance visualization," in
*EuroVis – STARs (16th Eurographics Conf. Visualization, State of the Art
Reports)*, R. Borgo, R. Maciejewski, and I. Viola, Eds. Eurographics Association,
2014, pp. 141–160, doi: 10.2312/eurovisstar.20141177.

**Free full text.** <https://www.cs.umd.edu/~bhatele/pubs/pdf/2014/eurovis2014.pdf>
— co-author's copy, University of Maryland. Full body text read. (Page range and
DOI confirmed against the Eurographics Digital Library and the University of
Arizona research record.)

**What it says.** This is the reference survey of how performance measurement data
is visualized, organised by the context the data is attributed to: hardware
(network topology, nodes), software (source code, call graphs), tasks
(processes/threads, temporal or aggregated), and application (domain problem
space). Among its explicit gaps: insufficient support for *comparing ensembles of
runs* across multiple executions, poor scalability to tens of thousands of
concurrent tasks, and weak integration between scattered tools via coordinated
views. It recommends closer collaboration with domain experts, sampling for
terabyte-scale data, and better attribution of performance problems to
"semantically high-level reasons."

**Area served.** 2 (benchmark/performance dashboards); overlaps 4.

**Connection to the thesis.** The named gap — comparing many runs of a program
rather than profiling one — is precisely the gap a benchmarking dashboard for
simulator comparison fills, so this is the survey to cite when motivating the
artefact's existence.

### 2.2 Shadura, Vassilev and Bockelman (2019) — Continuous benchmarking dashboard for ROOT

**Reference.**
O. Shadura, V. Vassilev, and B. P. Bockelman, "Continuous performance
benchmarking framework for ROOT," *EPJ Web of Conferences*, vol. 214, art. 05003,
pp. 1–8, 2019, doi: 10.1051/epjconf/201921405003.

**Free full text.** <https://www.epj-conferences.org/articles/epjconf/pdf/2019/19/epjconf_chep2018_05003.pdf>
— open access (CC BY). Full text read.

**What it says.** ROOTBench runs Google-Benchmark micro-benchmarks nightly,
stores timestamped measurements in an InfluxDB time-series database, and exposes
them through Grafana dashboards so developers can browse historical performance
trends and spot anomalies across several processor architectures. The paper's
explicit argument is that isolated, one-off benchmark runs cannot detect
regressions: only continuously accumulated, browsable history can, and the
presentation layer is part of that capability rather than an add-on.

**Area served.** 2.

**Connection to the thesis.** This is the closest published precedent for the
thesis artefact — a real, deployed dashboard whose job is to make accumulated
benchmark results of scientific software interrogable over time — and it
establishes architecture (measurement store + query-driven dashboard) as the
reference pattern.

### 2.3 Liu et al. (2021) — ExplainaBoard: an explainable leaderboard

**Reference.**
P. Liu, J. Fu, Y. Xiao, W. Yuan, S. Chang, J. Dai, Y. Liu, Z. Ye, and G. Neubig,
"ExplainaBoard: An explainable leaderboard for NLP," in *Proc. 59th Annual
Meeting of the Association for Computational Linguistics and 11th Int. Joint
Conf. Natural Language Processing: System Demonstrations*, 2021, pp. 280–289,
doi: 10.18653/v1/2021.acl-demo.34.

**Free full text.** <https://aclanthology.org/2021.acl-demo.34.pdf>
— ACL Anthology, open access. Full text read. (Best Demonstration Paper,
ACL-IJCNLP 2021.)

**What it says.** The paper names three concrete failures of conventional
leaderboards: they compress a system into a single holistic number that hides
where it is strong or weak; they are static and non-interactive, so a reader
cannot pursue their own question; and they report no reliability information on
small test sets. ExplainaBoard replaces this with interpretable, interactive
reporting: per-system performance broken into buckets over attributes (e.g.
entity length, sentence length), pairwise system comparison showing exactly where
two systems diverge, data-bias analysis of the benchmark itself, system
combination to reveal complementarity, and confidence intervals/calibration for
reliability.

**Area served.** 2. Also a "static tables are insufficient" source (§6.3).

**Connection to the thesis.** It is the citable statement that a benchmark
*report* should be an interactive, decomposable artefact rather than a ranked
table — the exact design premise of the thesis dashboard, transplanted from NLP
benchmarking to simulator benchmarking.

### 2.4 Ethayarajh and Jurafsky (2020) — Critique of leaderboards

**Reference.**
K. Ethayarajh and D. Jurafsky, "Utility is in the eye of the user: A critique of
NLP leaderboards," in *Proc. 2020 Conf. Empirical Methods in Natural Language
Processing (EMNLP)*, 2020, pp. 4846–4853,
doi: 10.18653/v1/2020.emnlp-main.393.

**Free full text.** <https://aclanthology.org/2020.emnlp-main.393.pdf>
— ACL Anthology, open access. Full text read.

**What it says.** Using a microeconomic utility framing, the authors show that a
leaderboard's implicit utility function (accuracy, at any cost) diverges from the
practitioner's, so a maximally accurate but very expensive model ranks first while
delivering *less* utility to most users. They argue the ranking is therefore not
a neutral summary but an encoding of one particular preference. Their concrete
recommendation is disclosure alongside the accuracy figure: model size, energy
efficiency and inference latency, so that a reader can apply their own trade-off
rather than inherit the leaderboard's.

**Area served.** 2. Also a "static tables are insufficient" source (§6.3).

**Connection to the thesis.** It supplies the formal argument for why the
benchmarking dashboard must let a reader re-weight or re-sort by their own
criterion (accuracy vs. runtime vs. memory) instead of shipping one fixed
ranking of simulators.

### 2.5 Weber et al. (2019) — Essential guidelines for computational method benchmarking

**Reference.**
L. M. Weber, W. Saelens, R. Cannoodt, C. Soneson, A. Hapfelmeier, P. P. Gardner,
A.-L. Boulesteix, Y. Saeys, and M. D. Robinson, "Essential guidelines for
computational method benchmarking," *Genome Biology*, vol. 20, art. 125, 2019,
doi: 10.1186/s13059-019-1738-8.

**Free full text.** <https://pmc.ncbi.nlm.nih.gov/articles/PMC6584985/>
— PubMed Central, open access. Full text read.

**What it says.** This is the standard methodological reference for benchmarking
computational methods, and it addresses reporting explicitly: it states that
visualizations summarising multiple performance metrics are "highly informative
for method users," and that a single overall ranking is inadequate because "it is
unlikely that a single method will perform best across all metrics." It instead
recommends identifying consistently strong methods while making their distinct
strengths visible. For large benchmarks it recommends online resources that let
readers interactively explore results, plus extensibility via public code and
data so later methods can be added.

**Area served.** 2. Also a "static tables are insufficient" source (§6.3).

**Connection to the thesis.** This is the single best citation for the thesis's
core premise: an authoritative, heavily cited benchmarking-methodology paper that
explicitly prescribes interactive, extensible online presentation of results
rather than a static ranked table.

---

## 3. Decision-support dashboards

### 3.1 Dowding et al. (2015) — Dashboards for improving patient care

**Reference.**
D. Dowding, R. Randell, P. Gardner, G. Fitzpatrick, P. Dykes, J. Favela,
S. Hamer, Z. Whitewood-Moores, N. Hardiker, E. Borycki, and L. Currie,
"Dashboards for improving patient care: Review of the literature,"
*International Journal of Medical Informatics*, vol. 84, no. 2, pp. 87–100, 2015,
doi: 10.1016/j.ijmedinf.2014.10.001.

**Free full text.** <https://eprints.whiterose.ac.uk/id/eprint/84905/3/Dowding%20et%20al%20Dashboards%20Review%20FINAL-EDITED%20Sept%20CLEAN.pdf>
— White Rose Research Online (institutional repository), accepted manuscript.
Full text read.

**What it says.** Reviewing 11 empirical studies of clinical and quality
dashboards, the authors find some evidence that deployment improves adherence to
quality guidelines and can improve outcomes, with accessibility to the decision
maker (e.g. dashboards surfaced as a screen saver) a recurring success factor.
Most reviewed dashboards relied on traffic-light colour coding and tabular
formats, but the evidence base was too thin to say *which* design features
produce the benefit. The review's sharpest conclusion is methodological: few
studies rigorously examined how practitioners actually integrate dashboard
information into a decision, and most had significant design limitations.

**Area served.** 3 (decision-support dashboards); also 5.

**Connection to the thesis.** It licenses a modest, honest claim about the
dashboard's expected benefit, and is the citation for why the thesis evaluates the
dashboard's *design properties* rather than asserting a decision-quality
improvement it cannot measure.

### 3.2 Matheus, Janssen and Maheshwari (2020) — Dashboards for accountable decision making

**Reference.**
R. Matheus, M. Janssen, and D. Maheshwari, "Data science empowering the public:
Data-driven dashboards for transparent and accountable decision-making in smart
cities," *Government Information Quarterly*, vol. 37, no. 3, art. 101284, 2020,
doi: 10.1016/j.giq.2018.01.006.

**Free full text.** <https://www.sciencedirect.com/science/article/pii/S0740624X18300303>
— open access on ScienceDirect (Creative Commons). Full text read.

**What it says.** The authors define a dashboard as "the visualization of a
consolidated set [of] data for a certain purpose, which enables to see what is
happening and to initiate actions" — i.e. as an instrument of action, not display.
From Rio de Janeiro traffic and public-transport cases they identify the dominant
failure modes as data-quality problems, misinterpretation risk, and institutional
gaps, and derive ten design principles including accurate data collection,
customised views per audience, and real-time updating. Their central finding is
that visual design alone is insufficient: without documented data provenance and
governance, a dashboard can erode rather than build trust in the numbers it
shows.

**Area served.** 3.

**Connection to the thesis.** It supports the dashboard's provenance and
metadata surface (which simulator version, which hardware, which parameters
produced each number) as a *decision-support* requirement, not bookkeeping —
because a reader who cannot audit a benchmark figure cannot act on it.

### 3.3 Vornhagen et al. (2026) — Design practices for data dashboards in health care

**Reference.**
H. Vornhagen, S. Barrett, C. Carroll, L. K. Iladiva, G. Martin, D. McKeown, and
J. Martin, "Design practices for data dashboards in health care: Scoping review,"
*Journal of Medical Internet Research*, vol. 28, art. e77361, 2026,
doi: 10.2196/77361.

**Free full text.** <https://www.sciencedirect.com/org/science/article/pii/S1438887126001664>
— open access (CC BY), publisher mirror. Full text read. Also at
<https://www.jmir.org/2026/1/e77361>.

**What it says.** The review organises dashboard design practice into four
pillars: *approach* (engaging end users and stakeholders in defining needs,
iterative co-creation), *content* (selecting actionable metrics, data accuracy,
visual best practice), *behaviour* (usability, interactivity, accessibility for
users of differing capability), and *adoption* (workflow integration, governance,
training, sustainability). Its headline gap is that adoption-related factors —
governance, training, sustainability — were rarely addressed in the literature
despite determining whether a dashboard survives past its pilot.

**Area served.** 3 and 5.

**Connection to the thesis.** A recent, structured framework the thesis can use
to report its own design process against named practice categories, and to
acknowledge the adoption dimension (who maintains the benchmark dashboard as new
simulator versions appear) explicitly rather than silently.

---

## 4. Interactive analytics systems

### 4.1 Keim et al. (2008) — Visual analytics: definition, process, challenges

**Reference.**
D. Keim, G. Andrienko, J.-D. Fekete, C. Görg, J. Kohlhammer, and G. Melançon,
"Visual analytics: Definition, process, and challenges," in *Information
Visualization: Human-Centered Issues and Perspectives*, Lecture Notes in Computer
Science, vol. 4950. Berlin, Germany: Springer, 2008, pp. 154–175,
doi: 10.1007/978-3-540-70956-5_7.

**Free full text.** <https://kops.uni-konstanz.de/server/api/core/bitstreams/ad4fdc55-88af-4f5c-9800-1b8845900f6a/content>
— KOPS, University of Konstanz institutional repository. Full chapter read.
(Peer-reviewed book chapter.)

**What it says.** The chapter defines visual analytics as combining automated
analysis techniques with interactive visualizations "for an effective
understanding, reasoning and decision making on the basis of very large and
complex data sets" — an integration, not either half alone. It revises
Shneiderman's mantra into the Visual Analytics Mantra: "analyse first, show the
important, zoom, filter and analyse further, details on demand," on the grounds
that at scale computation must select what is displayed. It models the activity as
a sense-making loop in which the analyst alternates between visual exploration and
analytical computation, refining hypotheses and representation together.

**Area served.** 4.

**Connection to the thesis.** Licenses the dashboard's design of computing
aggregate and derived benchmark statistics up front and showing the salient
comparisons first, with drill-down to individual runs, instead of rendering every
raw measurement.

### 4.2 Satyanarayan et al. (2017) — Vega-Lite

**Reference.**
A. Satyanarayan, D. Moritz, K. Wongsuphasawat, and J. Heer, "Vega-Lite: A grammar
of interactive graphics," *IEEE Transactions on Visualization and Computer
Graphics*, vol. 23, no. 1, pp. 341–350, 2017,
doi: 10.1109/TVCG.2016.2599030.

**Free full text.** <https://idl.cs.washington.edu/files/2017-VegaLite-InfoVis.pdf>
— UW Interactive Data Lab author copy. Full body text read. (Volume/issue/pages
from the TVCG record.)

**What it says.** Vega-Lite defines a *unit specification* mapping data fields to
encoding channels (position, colour, size, shape) and a *view composition
algebra* with layer, facet, concatenate and repeat operators, so multi-view and
small-multiple displays are composed rather than hand-assembled. Its distinctive
contribution is a *selection* abstraction that treats an interaction as a named
set of backing points plus a predicate, which can then parameterise any encoding —
making panning, zooming, brushing and linked highlighting declarative and
systematically enumerable. The paper argues this decomposition is what allows a
concise specification to express interactive, coordinated multi-view dashboards.

**Area served.** 4; also 1.

**Connection to the thesis.** The formal account of the
multiple-coordinated-views and linked-selection mechanics the benchmarking
dashboard relies on to keep facetted per-metric charts and per-simulator
selections in sync.

### 4.3 Liu and Heer (2014) — Effects of interactive latency

**Reference.**
Z. Liu and J. Heer, "The effects of interactive latency on exploratory visual
analysis," *IEEE Transactions on Visualization and Computer Graphics*, vol. 20,
no. 12, pp. 2122–2131, 2014, doi: 10.1109/TVCG.2014.2346452.

**Free full text.** <https://idl.cs.washington.edu/files/2014-Latency-InfoVis.pdf>
— UW Interactive Data Lab author copy. Full body text read. (Volume/issue/pages
from the TVCG record.)

**What it says.** The study injects an additional 500 ms of delay per operation
into an exploratory visual analysis tool and compares against a low-latency
control. The delay significantly reduced interaction rates (brushing, mouse
activity) and reduced coverage of the dataset, measured as unique data regions
visited. Verbal-protocol coding showed it also lowered the rates at which
participants made observations, drew generalisations and generated hypotheses —
latency degraded analytical *output*, not merely comfort — and some effects
persisted after the delay was removed.

**Area served.** 4.

**Connection to the thesis.** Turns the dashboard's responsiveness
(pre-aggregation, client-side filtering, caching) from an implementation detail
into a design requirement with measured consequences for what a reader will
actually discover in the benchmark data.

### 4.4 Wongsuphasawat et al. (2016) — Voyager

**Reference.**
K. Wongsuphasawat, D. Moritz, A. Anand, J. Mackinlay, B. Howe, and J. Heer,
"Voyager: Exploratory analysis via faceted browsing of visualization
recommendations," *IEEE Transactions on Visualization and Computer Graphics*,
vol. 22, no. 1, pp. 649–658, 2016, doi: 10.1109/TVCG.2015.2467191.

**Free full text.** <https://idl.cs.washington.edu/files/2015-Voyager-InfoVis.pdf>
— UW Interactive Data Lab author copy. Full body text read. (Volume/issue/pages
from the TVCG record.)

**What it says.** Voyager is a mixed-initiative system that presents *faceted
browsing of recommended charts*, chosen by statistical and perceptual measures by
its Compass engine, which proposes additional variables beyond those the user
selected. In a controlled study against PoleStar (a manual chart-specification
tool of the Tableau/Polaris kind), Voyager participants were exposed to over three
times as many variable sets and interacted with about 1.5 times more unique
variable combinations. Preferences split by task: 15 of 16 participants preferred
Voyager for initial exploration, PoleStar for answering a specific targeted
question — evidence that breadth-first and depth-first analysis need different
affordances.

**Area served.** 4.

**Connection to the thesis.** Justifies offering both a browsable set of
pre-composed benchmark views (for the reader with no specific question) and
direct control over axes and filters (for the reader who has one) — and supplies a
measured effect size for why the first matters.

---

## 5. User-centred dashboard design frameworks

### 5.1 Sarikaya et al. (2019) — What do we talk about when we talk about dashboards?

**Reference.**
A. Sarikaya, M. Correll, L. Bartram, M. Tory, and D. Fisher, "What do we talk
about when we talk about dashboards?," *IEEE Transactions on Visualization and
Computer Graphics*, vol. 25, no. 1, pp. 682–692, 2019,
doi: 10.1109/TVCG.2018.2864903.

**Free full text.** <https://alper.datav.is/assets/publications/dashboards/dashboards-preprint.pdf>
— first author's copy of the accepted TVCG paper. Full body text read
(introduction through conclusion and references). (Volume/issue/pages from the
TVCG record.)

**What it says.** From a corpus of 83 dashboards "in the wild" plus a
multi-domain literature review, the authors derive 15 design dimensions grouped
into purpose (strategic / tactical / operational decision support, plus
communication and learning), audience (circulation and expected visualization
literacy), visual features and interactivity (construction, multipage layout,
interactive interfaces, highlighting), and data semantics (alerting, benchmarks,
updatability). Hierarchical clustering yields seven dashboard clusters, showing
"dashboard" spans genres well beyond the single-screen business monitor and that
guidance must be conditioned on genre. Notably, *benchmarks* is an explicit
data-semantics dimension: whether the dashboard supplies reference values against
which the displayed numbers are to be read.

**Area served.** 5; also 3, since the purpose dimension is framed around decision
support.

**Connection to the thesis.** Lets the thesis place its artefact precisely inside
a published design space — an analytic, high-literacy, benchmark-bearing,
multipage dashboard for comparison and communication — instead of using
"dashboard" as an undefined term.

### 5.2 Bach et al. (2023) — Dashboard design patterns

**Reference.**
B. Bach, E. Freeman, A. Abdul-Rahman, C. Turkay, S. Khan, Y. Fan, and M. Chen,
"Dashboard design patterns," *IEEE Transactions on Visualization and Computer
Graphics*, vol. 29, no. 1, pp. 342–352, 2023,
doi: 10.1109/TVCG.2022.3209448.

**Free full text.** <https://eprints.gla.ac.uk/281864/1/281864.pdf>
— University of Glasgow Enlighten repository, accepted version. Full body text
read.

**What it says.** The paper catalogues 42 dashboard design patterns split into
*content* patterns (what information is present: data information, metadata,
derived values, visual representations, annotation) and *composition* patterns
(how it is arranged across screen space and pages — structure, relationships,
navigation). It identifies six dashboard genres — static, analytic, magazine,
infographic, repository, and embedded mini dashboards — each a characteristic
combination of patterns. It then names the trade-off space explicitly: abstraction
versus detail, screen space, pagination, and interactivity, arguing these must be
balanced deliberately rather than resolved by default.

**Area served.** 5.

**Connection to the thesis.** Supplies named, citable patterns for each layout
decision in the benchmarking dashboard (overview page, per-metric detail pages,
annotation of reference runs) and a published vocabulary for the
abstraction/pagination trade-offs the thesis actually had to make.

### 5.3 Wall et al. (2019) — ICE-T: heuristic, value-driven evaluation

**Reference.**
E. Wall, M. Agnihotri, L. Matzen, K. Divis, M. Haass, A. Endert, and J. Stasko,
"A heuristic approach to value-driven evaluation of visualizations," *IEEE
Transactions on Visualization and Computer Graphics*, vol. 25, no. 1,
pp. 491–500, 2019, doi: 10.1109/TVCG.2018.2865146.

**Free full text.** <https://faculty.cc.gatech.edu/~john.stasko/papers/infovis18-icet.pdf>
— author's copy, Georgia Tech. Full body text read. (Volume/issue/pages from the
TVCG record.)

**What it says.** ICE-T operationalises Stasko's "value equation" as a three-tier
instrument: 21 low-level heuristic statements roll up into guidelines, which roll
up into four value components — Insight, Confidence, Essence and Time.
Visualization-knowledgeable raters, *not end users*, score each heuristic on a
7-point scale and the scores aggregate upward into component scores. Validated
with 15 expert raters across three college-data visualizations, the instrument
gave consistent results with roughly five raters, making it a practical
substitute for a user study.

**Area served.** 5; flagged again in §6.1.

**Connection to the thesis.** A concrete, published protocol the thesis can
actually run on its own dashboard — a small panel of expert raters producing
Insight/Confidence/Essence/Time scores — giving the dashboard chapter a real
evaluation instead of an assertion.

### 5.4 Tory and Möller (2005) — Do expert reviews work?

**Reference.**
M. Tory and T. Möller, "Evaluating visualizations: Do expert reviews work?,"
*IEEE Computer Graphics and Applications*, vol. 25, no. 5, pp. 8–11, 2005,
doi: 10.1109/MCG.2005.102.

**Free full text.** <https://eprints.cs.univie.ac.at/4978/1/2005_-_evaluating_visualizations.pdf>
— University of Vienna institutional repository. Full body text read.
(Volume/issue/pages from the CG&A record.)

**What it says.** The authors ran expert reviews on two visualization interfaces
(spectral volume-rendering lighting controls; a table versus a parallel-coordinates
interface for volume exploration) with reviewers drawn from HCI specialists,
visualization experts and end users. The reviews surfaced usability issues and
design insights far more cheaply than a formal study, and in one case the expert
verdict agreed with the later formal user-study result. Their recommendations are
specific: include reviewers with *data-display* expertise as well as usability
expertise, and use heuristics derived from visualization guidelines as well as
general usability guidelines — while not treating expert review as a full
substitute for user testing.

**Area served.** 5; flagged again in §6.1.

**Connection to the thesis.** The citation for why an expert review of the
benchmarking dashboard is a legitimate evaluation, what composition the reviewer
panel should have, and — read honestly — what the thesis cannot claim from it.

### 5.5 Farzandipour, Nabovati and Sadeqi Jabali (2022) — Heuristic evaluation versus cognitive walkthrough

**Reference.**
M. Farzandipour, E. Nabovati, and M. Sadeqi Jabali, "Comparison of usability
evaluation methods for a health information system: Heuristic evaluation versus
cognitive walkthrough method," *BMC Medical Informatics and Decision Making*,
vol. 22, art. 157, 2022, doi: 10.1186/s12911-022-01905-7.

**Free full text.** <https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-022-01905-7>
— open access (CC BY). Full text read.

**What it says.** Five experienced evaluators applied both expert-based methods
independently to the nursing module of a hospital information system: heuristic
evaluation guided by Nielsen's principles, and cognitive walkthrough simulating
task performance across five user scenarios. Heuristic evaluation identified 104
distinct problems at a mean severity of 2.34 (mostly minor); cognitive walkthrough
identified 24 problems at a mean severity of 2.77 (mostly major); only 33.3% of
problems were found by both. The authors conclude the methods are complementary —
breadth versus severity — and should be combined rather than substituted.

**Area served.** 5; flagged again in §6.1.

**Connection to the thesis.** Gives the thesis a defensible two-method
inspection protocol (heuristic evaluation for breadth, cognitive walkthrough over
the dashboard's intended reader tasks for severity) together with published
figures showing why one method alone would miss two-thirds of the problems.

---

## 6. Flagged sources for three specific claims

### 6.1 Formally evaluating a dashboard *without* a user study

These are the sources that let the thesis run and defend an evaluation with no
participants.

| Source | What it supplies |
|---|---|
| Wall et al. (2019), §5.3 | ICE-T: a validated 21-heuristic, four-component (Insight, Confidence, Essence, Time) rating instrument completed by visualization-knowledgeable raters, reliable at about five raters. The most directly usable protocol on this list. |
| Farzandipour et al. (2022), §5.5 | Side-by-side application of heuristic evaluation and cognitive walkthrough by five expert evaluators, with problem counts and severities for each, and the finding that only a third of problems overlap — the justification for running both. |
| Tory and Möller (2005), §5.4 | Empirical evidence that expert reviews find real issues cheaply and can agree with later user-study findings, plus prescriptions on reviewer composition and on using visualization-specific (not only usability) heuristics. |
| Munzner (2009), §1.2 | The framing argument: each design level has *immediate* validation methods that do not require users — perceptual/design justification at the encoding level, complexity and timing analysis at the algorithm level — and a method applied at the wrong level proves nothing. This is how to structure the evaluation chapter so its no-user-study status is a principled choice, not an omission. |
| Dowding et al. (2015), §3.1 | Task-based analytical framing from the other direction: the review shows the dashboard literature is weak precisely because it rarely examines how information enters a decision, which motivates walking the dashboard through the reader's benchmark-interpretation tasks explicitly. |

**Suggested combination for the thesis.** Frame the evaluation with Munzner's
immediate-validation argument; run ICE-T with ~5 expert raters (Wall et al.);
supplement with a heuristic evaluation plus a cognitive walkthrough over the
intended reader tasks, citing Farzandipour et al. for the protocol and the
expected complementarity, and Tory and Möller for reviewer selection.

### 6.2 What makes a dashboard's figures readable

| Source | What it supplies |
|---|---|
| Heer and Bostock (2010), §1.3 | Position beats length beats area for value comparison; rectangular-area comparison is as error-prone as circular-area, and worst at aspect ratio 1; little accuracy gain above ~80 px chart height; gridlines need ≥ ~8 px spacing. Quantitative thresholds for chart sizing and gridline density, and the argument for reading exact values from a table or labels rather than estimating them from area. |
| Crameri et al. (2020), §1.4 | Rainbow/jet maps create false boundaries and introduce visual error above 7% of the data variation; ~8% of men and ~0.5% of women have a colour-vision deficiency; a scientific colour map must be perceptually uniform, perceptually ordered, CVD-readable and greyscale-legible. |
| Nuñez et al. (2018), §1.5 | A reproducible optimisation method (CIECAM02-UCS, linearised brightness) and the resulting *cividis* map, shown to give near-identical interpretation for CVD and non-CVD readers; the concrete recommendation to use monotonic-brightness maps such as cividis/viridis. |
| Bach et al. (2023), §5.2 | Content patterns that cover exactly the "figure plus numbers" question — data information, derived values, metadata and annotation patterns, and the tabular/detail patterns that sit a table of values beside or beneath a chart — and the abstraction-versus-detail trade-off that decides when to show both. |
| Weber et al. (2019), §2.5 | Direct statement that visualizations summarising *multiple* metrics are highly informative for method users, which is the citation for showing several metrics side by side rather than one composite score. |

**Note on value labels and tables beside charts.** No single paper on this list is
devoted to value labelling. The defensible construction is: Heer and Bostock give
the perceptual reason (area and, to a lesser degree, length judgments carry real
error, so a reader needing the exact number cannot recover it from the mark), and
Bach et al.'s content/annotation patterns plus Weber et al.'s multi-metric
recommendation supply the design response (print the value, and pair the chart
with the table). Do not attribute a specific "always label values" rule to any of
these papers; build the argument from the perceptual finding plus the pattern.

### 6.3 Why a static table of benchmark results is insufficient

| Source | What it supplies |
|---|---|
| Weber et al. (2019), §2.5 | The strongest and most quotable: a single overall ranking is inadequate because no method is best on every metric; for extensive benchmarks, online resources that let readers *interactively explore* the results are recommended, along with extensibility so later methods can be added. From a mainstream benchmarking-methodology paper, not a visualization paper. |
| Ethayarajh and Jurafsky (2020), §2.4 | A ranking encodes one utility function (accuracy at any cost) which diverges from the reader's; the fix is disclosure of cost dimensions (size, energy, latency) so readers can apply their own trade-off. The formal argument that a fixed ranking answers the author's question, not the reader's. |
| Liu et al. (2021), §2.3 | Names the failure directly: leaderboards compress a system to one holistic number, are static and non-interactive so the reader cannot pursue their own question, and omit reliability information. Then demonstrates the alternative (bucketed per-attribute breakdowns, pairwise comparison, confidence intervals). |
| Shneiderman (1996), §1.1 | The task argument: a static table supports neither zoom, filter, relate, history nor extract; a reader with their own question needs those operations, and the taxonomy states which. |
| Wongsuphasawat et al. (2016), §4.4 | Measured evidence that presentation format changes what a reader actually examines: browsing recommended views exposed analysts to over 3× more variable sets than manual specification, and participants preferred different affordances for open exploration versus targeted questions. |
| Isaacs et al. (2014), §2.1 | From the performance-visualization side: comparing *ensembles* of runs is an identified gap, and static per-run reports are what leave it open. |
| Liu and Heer (2014), §4.3 | The complementary caution: interactivity only helps if it is fast — 500 ms of added latency measurably reduced dataset coverage and the rate of observations, generalisations and hypotheses. |

---

## Appendix: sources sought but not included

Recorded so the omissions are deliberate and not repeated.

- **Zuk et al., "Heuristics for information visualization evaluation" (BELIV
  2006)** and **Forsell and Johansson, "An heuristic set for evaluation in
  information visualization" (AVI 2010)** — both highly relevant to §6.1, but no
  copy whose full text could be confirmed readable was found (the ACM pages
  refuse automated access and the author-copy hosts disallow retrieval). Excluded
  under the free-full-text rule. Wall et al. (§5.3) and Farzandipour et al.
  (§5.5) cover the same ground with confirmed access.
- **Lam et al., "Empirical studies in information visualization: Seven
  scenarios" (IEEE TVCG, 2012)** — the natural companion to Munzner (§1.2), but
  no confirmable free full-text copy was reachable. Excluded.
- **Nielsen and Molich, "Heuristic evaluation of user interfaces" (CHI 1990)** —
  full text is behind the ACM paywall for automated access; excluded, with
  Farzandipour et al. (§5.5) standing in as the citable application of Nielsen's
  heuristics.
- **Schwendimann et al., "Perceiving learning at a glance" (IEEE Trans. Learning
  Technologies, 2017)** — a strong learning-analytics dashboard review, but the
  EPFL repository record carries no free PDF. Excluded.
- **Stadler et al., "Improving the efficiency and ease of healthcare analysis
  through use of data visualization dashboards" (Big Data, 2016)** — confirmed
  paywalled. Excluded.
- **Dong, Du and Gardner, "An interactive web-based dashboard to track COVID-19
  in real time" (Lancet Infect. Dis., 2020)** — excluded on the peer-review rule:
  it is a Correspondence item, not a peer-reviewed research article.
- **"Development and actionability of the Dutch COVID-19 dashboard" (JMIR Public
  Health Surveill., 2021)** — genuinely open access and directly relevant to §6.1
  (it uses an expert appraisal), but PubMed Central and Europe PMC both refused
  automated retrieval during this search, so full text could not be confirmed.
  Worth one manual check at
  <https://publichealth.jmir.org/2021/10/e31161/> before submission; if it opens,
  it is a good addition to areas 3 and 5.
