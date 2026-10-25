#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1
python -m unittest discover -s tests -v
mkdir -p outputs/main
python src/experiment.py --output outputs/main --seeds 12 --products 140 --particles 320 --sweep-seeds 3 --sweep-products 45 | tee outputs/experiment.log
python proof/predicate_or_proof.py outputs/main | tee outputs/proof.log
python scripts/analyze.py | tee outputs/analysis.log
python scripts/numbers.py
# Use standard BibTeX when installed, or bibtex8 as a compatible fallback.
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
if command -v bibtex >/dev/null 2>&1; then
  bibtex main >/dev/null
elif command -v bibtex8 >/dev/null 2>&1; then
  bibtex8 main >/dev/null
else
  echo 'A BibTeX executable is required (bibtex or bibtex8).' >&2
  exit 2
fi
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
cp main.pdf manuscript.pdf
python scripts/verify.py
