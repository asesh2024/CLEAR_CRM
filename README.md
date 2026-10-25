# CLEAR-CRM

**Decision-Conditioned Verifiable Disclosure for Privacy-Aware Critical Raw Material Recovery with Digital Product Passports**

CLEAR-CRM investigates whether an end-of-life (EoL) recycler can choose a suitable treatment route by requesting only those confidential lifecycle predicates that are expected to improve its decision. The approach uses **Expected Value of Sample Information (EVSI)** to select the next authorized Boolean query and stops when its expected decision benefit no longer exceeds its declared cost.

## Source code

| Path | Purpose |
|---|---|
| `src/experiment.py` | Generate synthetic records; run the decision policies, simulated partitioned statistics, inference evaluation, and sensitivity sweeps. |
| `proof/predicate_or_proof.py` | Run the separate finite-domain threshold-proof and negative-test experiments. |
| `scripts/analyze.py` | Calculate paired statistics, generate result CSVs, and create plots and tables. |
| `scripts/numbers.py` | Export numerical values from executed results. |
| `scripts/verify.py` | Check output counts, accounting identities, proof-test outcomes, and generated files after the full pipeline. |
| `tests/test_research.py` | Automated unit tests. |
| `run_all.sh` | Run tests, experiments, analyses, artifact generation, and verification in the required order. |
| `requirements.txt` | Python dependencies. |

## Data

The datasets are **synthetic**. The `data/` directory contains saved CSV snapshots from an executed run. The experiment script generates its synthetic records internally; it **does not read** `data/synthetic_products_1680.csv` or `data/synthetic_training.csv` as its input.

| File | Contents |
|---|---|
| `data/synthetic_products_1680.csv` | 1,680 unique synthetic test products, reconstructed from the saved decision records. |
| `data/synthetic_training.csv` | 4,400 saved synthetic training records from seed 100. |
| `data/decisions.csv` | 13,440 product-policy observations (eight policies per product). |
| `data/per_seed.csv` | Seed-level observations for the eight policies. |
| `data/summary.csv` | Policy-level aggregate statistics. |
| `data/paired_comparisons.csv` | Paired comparisons and confidence intervals. |
| `data/sweeps.csv` | Query-budget, noise, shift, and objective-weight sensitivity runs. |
| `data/passport_lineage.csv` | Synthetic material-accounting records. |
| `data/three_objective_pareto.csv` | Exploratory three-objective evaluation records. |
| `data/additional_private_setting_attack.csv` | Supplemental action-output inference observations. |
| `data/proof_benchmarks.csv` | Proof runtime and size measurements. |
| `data/proof_negative_tests.csv` | Results of invalid, replayed, and unauthorized proof tests. |
| `data/CSV_MANIFEST.csv` | Dataset row counts and SHA-256 hashes. |

Fresh outputs are written to **`outputs/main/`**. These can be compared against the archived CSVs in `data/`. Some cryptographic measurements and execution times are non-deterministic.

## Reproduce the experiments in WSL (Ubuntu 22.04/24.04)

### 1. Install system dependencies


sudo apt update
sudo apt install -y git python3 python3-pip python3-venv build-essential \
  texlive-latex-recommended texlive-latex-extra texlive-science \
  texlive-publishers texlive-bibtex-extra texlive-binaries latexmk


TeX Live is needed because the full runner also builds its generated document artifact. For data and code execution alone, follow the individual commands under Step 5.

### 2. Clone the repository


git clone https://github.com/asesh2024/CLEAR_CRM.git
cd CLEAR_CRM


Run the commands below from the directory containing `run_all.sh`. If the project was uploaded inside a `CLEAR_CRM_Rewritten/` subdirectory, run `cd CLEAR_CRM_Rewritten` first.

### 3. Set up Python


python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt


### 4. Run the complete pipeline

```bash
bash run_all.sh
```

This command executes the unit tests, synthetic benchmark, sensitivity sweeps, separate proof tests, statistical analysis, figure/table generation, document build, and output checks.

### 5. Run the computational experiments separately (without LaTeX)


python -m unittest discover -s tests -v

python src/experiment.py \
  --output outputs/main \
  --seeds 12 \
  --products 140 \
  --particles 320 \
  --sweep-seeds 3 \
  --sweep-products 45

python proof/predicate_or_proof.py outputs/main
python scripts/analyze.py
python scripts/numbers.py


The first experiment run uses seeds **100–111**, producing **1,680** synthetic evaluation products and **13,440** product-policy observations. The sensitivity sweeps use three seeds and 45 products per seed. Repeating the run overwrites files in `outputs/main/`; the archived `data/` snapshots are not automatically changed.

### 6. Check the generated data


ls -lh outputs/main/*.csv
head -n 5 outputs/main/summary.csv
wc -l outputs/main/decisions.csv


`decisions.csv` should contain **13,441 lines**, including its header. After a successful **full** run, the additional verification command is:


python scripts/verify.py


### 7. Optional smaller test run


python src/experiment.py \
  --output outputs/pilot \
  --seeds 2 \
  --products 40 \
  --particles 220 \
  --sweep-seeds 1 \
  --sweep-products 20


This writes a separate dataset to `outputs/pilot/` without replacing the main results. The analysis scripts are configured to read `outputs/main/` by default.

## Reproducibility notes

- All product records and process coefficients in this repository are synthetic, not industrial measurements.
- Client partitions, aggregation, and cross-tier data separation are emulated in one Python process.
- The proof program is a separate finite-domain protocol test, not an integrated production service.
- Fixed random seeds support numerical reproduction, subject to minor software/platform differences. Proof randomness, timings, and sizes may vary.
- The saved full-state synthetic CSVs are for reproducibility; they are **not** provided to the modeled inference adversary as private-state inputs.
