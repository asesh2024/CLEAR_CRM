# CLEAR-CRM

**Decision-Conditioned Verifiable Disclosure for Privacy-Aware Critical Raw Material Recovery with Digital Product Passports**

CLEAR-CRM investigates whether an end-of-life (EoL) recycler can choose a suitable treatment route by requesting only those confidential lifecycle predicates that are expected to improve its decision. The approach uses **Expected Value of Sample Information (EVSI)** to select the next authorized Boolean query and stops when its expected decision benefit no longer exceeds its declared cost.

This repository contains the Springer Nature LaTeX manuscript, executable Python experiments, synthetic datasets, saved algorithm outputs, statistical analyses, plots, and a separate finite-domain zero-knowledge threshold-proof prototype.

> **Research status:** This is a reproducible **synthetic research benchmark**, not a production Digital Product Passport (DPP) service or an industrially validated CRM recovery system. The horizontal/vertical data partitions and secure aggregation are emulated in a single Python process. The proof prototype is a Schnorr-OR construction, **not Groth16**, and is evaluated separately from the treatment-decision loop.

## Research question

Can a recycler select authorized, verifiable lifecycle predicates according to their effect on recovery decisions while reducing unnecessary disclosure and maintaining competitive recovery–emissions–cost outcomes?

The benchmark studies four questions:

1. **Decision quality (H1):** Does cost-aware EVSI querying reduce regret and the number of released Boolean answers compared with fixed disclosure under the same maximum query budget?
2. **Inference risk (H2):** What can an adversary infer about the proprietary CRM fraction from the authorized query transcript and released treatment route?
3. **Verification (H3):** Can a signed, epoch-bound threshold-proof prototype reject the tested invalid statements, replays, and unauthorized requests without releasing the quantized witness?
4. **Multi-objective trade-offs (H4):** Does the policy improve the recovery–emissions–cost frontier over restricted-information controls across alternative objective weights?

## Methods

- **BoL / MoL / EoL data:** Synthetic CRM composition, product condition and contamination, and process-model parameters; distinct organizations and feature partitions are emulated.
- **Model summaries:** Clients generate 32-bin local feature histograms, add Laplace noise, and participate in an emulated two-share aggregation. The differential-privacy accounting applies to the specified histogram releases only.
- **Decision controller:** Selects authorized Boolean threshold predicates by one-step EVSI minus query cost, updates a posterior model, and chooses among mechanical, selective, and hydrometallurgical treatment routes.
- **Threat model:** A specified Bayesian adversary observes the public context, predicate queries/answers, and released action and estimates a private CRM fraction.
- **Verification:** An independent signed finite-domain Schnorr-OR threshold-proof demonstration checks validity, context binding, authorization, epoch, and replay handling.
- **Outcomes:** Decision regret, recovered CRM mass, modeled CO₂-equivalent emissions, processing cost, number of disclosures, adversarial reconstruction error, sensitivity tests, and exploratory three-objective hypervolume.

The cited federated/secure optimization methods are **methodological antecedents**, not faithfully reimplemented empirical baselines.

## Main synthetic results

The principal experiment evaluates **1,680 products** (12 independent seeds × 140 products) under eight decision policies, yielding **13,440 product-policy decision records**.

| Metric (per product) | Fixed two-query disclosure | CLEAR-CRM, cost-aware |
|---|---:|---:|
| Mean decision regret (lower is better) | 4.223 | 2.113 |
| Mean Boolean answers | 2.000 | 1.413 |
| Recovered CRM (kg) | 16.324 | 16.389 |
| Modeled emissions (kg CO₂e) | 81.67 | 79.45 |
| Processing cost (synthetic units) | 110.38 | 107.97 |
| CRM-fraction attack MAE (higher means less accurate inference) | 0.0305 | 0.0393 |

Against the specified fixed-disclosure policy, CLEAR-CRM lowers mean regret by approximately **50.0%** and releases approximately **29.3%** fewer Boolean answers. An exhaustive EVSI policy has slightly lower regret but releases more answers. In the exploratory three-weight hypervolume comparison, **fixed disclosure scores higher than CLEAR-CRM** (0.2440 versus 0.1981); the study therefore **does not establish general multi-objective dominance**.

These results depend on the declared synthetic distributions, treatment coefficients, utility weights, and threat model. Attack MAE is **not** an end-to-end privacy guarantee or proof of GDPR compliance.

## Repository contents

```text
CLEAR_CRM/
├── main.tex                       # Springer Nature manuscript source
├── manuscript.pdf                 # Compiled manuscript
├── references.bib                 # BibTeX references
├── sn-jnl.cls                     # Journal class
├── sn-mathphys-num.bst            # Numeric citation style
├── README.md
├── requirements.txt
├── run_all.sh                     # Complete replication pipeline
├── src/experiment.py             # Synthetic generation and decision policies
├── proof/predicate_or_proof.py   # Separate finite-domain threshold-proof tests
├── scripts/                       # Statistics, plots, LaTeX macros, verification
├── tests/                         # Automated Python tests
├── data/                          # Saved executed CSV snapshots
├── outputs/main/                  # Main generated experimental results
├── tables/                        # Generated LaTeX tables/macros
└── figures/                       # Ten manuscript figures
```

The `data/` folder contains saved experimental snapshots for inspection, including:

| Path | Content |
|---|---|
| `data/synthetic_products_1680.csv` | 1,680 distinct synthetic test products reconstructed from executed decision records |
| `data/synthetic_training.csv` | 4,400 synthetic training records from seed 100 only |
| `data/decisions.csv` | 13,440 executed product-policy decisions and outcomes |
| `data/per_seed.csv` | Seed-level results for all eight policies |
| `data/summary.csv` | Aggregate policy results |
| `data/paired_comparisons.csv` | Paired seed-level statistical contrasts |
| `data/sweeps.csv` | Query-budget, DP-noise, contamination-shift and weight experiments |
| `data/three_objective_pareto.csv` | Exploratory three-objective policy points |
| `data/proof_benchmarks.csv` | Threshold-proof timing and size measurements |
| `data/proof_negative_tests.csv` | Verification rejection tests |
| `data/passport_lineage.csv` | Synthetic parent/recovered/residual CRM accounting |
| `data/CSV_MANIFEST.csv` | File descriptions, record counts, and hashes |

**Data provenance:** The experiment generates synthetic inputs in memory; it **does not read the saved product or training CSVs as input**. The `data/` directory preserves a snapshot of the executed run. Re-execution writes fresh files to `outputs/main/`; it does not automatically overwrite the snapshots in `data/`.

## Reproduce in WSL (Ubuntu 22.04/24.04)

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv build-essential \
  texlive-latex-recommended texlive-latex-extra texlive-science \
  texlive-publishers texlive-bibtex-extra texlive-binaries latexmk
```

### 2. Clone and install Python dependencies

After creating the GitHub repository and pushing the project files:

```bash
git clone https://github.com/asesh2024/CLEAR_CRM.git
cd CLEAR_CRM
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the repository is private, GitHub authentication is required when cloning.

### 3. Run the complete experiment and rebuild the paper

```bash
bash run_all.sh
```

The script runs the Python tests, generates the main experiment and sensitivity results, runs standalone proof tests, computes statistical summaries, produces the manuscript figures and tables, compiles the paper with BibTeX, and checks the outputs.

Find the generated files at:

```bash
ls -lh outputs/main/*.csv
ls -lh figures/
ls -lh tables/
ls -lh manuscript.pdf
```

### 4. Run tests independently

```bash
python -m unittest discover -s tests -v
python scripts/verify.py
```

### 5. Run a smaller synthetic pilot

```bash
python src/experiment.py \
  --output outputs/pilot \
  --seeds 2 --products 40 --particles 220 \
  --sweep-seeds 1 --sweep-products 20
```

The analysis and manuscript-generation scripts read `outputs/main/` by default; this smaller pilot does not automatically replace the paper's reported results.

### 6. Compile LaTeX from existing tables and figures

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Reproducibility notes and limitations

- Seeds for the primary synthetic experiment are fixed (100–111). Cryptographic randomness and timing measurements may vary across runs and machines.
- The results are not based on measured industrial assays, validated life-cycle inventory factors, or real manufacturers' private data.
- The secure-aggregation and lifecycle data partitions are simulated within one Python process, not deployed as a malicious-secure multi-host federated service.
- The proof experiments use a finite-domain Schnorr-OR scheme tested independently; no integrated Groth16-based DPP workflow is claimed.
- The histogram differential-privacy budget does not extend automatically to adaptive predicate transcripts or final actions.
- The output-inference study evaluates a defined Bayesian attacker and confidential CRM fraction, not every possible secret, attacker, or repeated-query setting.
- Material mass conservation is checked arithmetically; it does not validate real weighing or chemical assay accuracy.
- The selected fixed and random query policies are synthetic comparators; results are not head-to-head reproductions of DP-FSAEA, TEE-based vertical optimization, or other published algorithms.

For detailed experimental assumptions, see [`RESULTS_AND_LIMITATIONS.md`](RESULTS_AND_LIMITATIONS.md) and the manuscript.

## Citation

If you use this project, cite the associated CLEAR-CRM manuscript using its final publication details once available. The included [`references.bib`](references.bib) contains the manuscript's literature references; it is not a publication record for this repository.

## License

No license is specified in this repository by default. Add a `LICENSE` file after selecting the permissions under which others may use, modify, and redistribute the code and data.
