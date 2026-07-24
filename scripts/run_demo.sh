#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FASTQ_DIR="${FASTQ_DIR:-${PROJECT_DIR}/data/fastq}"
INDEX_DIR="${INDEX_DIR:-${PROJECT_DIR}/reference/salmon-gencode-v36}"
RESULTS_DIR="${RESULTS_DIR:-${PROJECT_DIR}/results/gbm-demo}"
LOG_DIR="${PROJECT_DIR}/logs"
THREADS="${THREADS:-2}"
BATCH_SIZE="${BATCH_SIZE:-1}"
PROJECT_NAME="${PROJECT_NAME:-GBM_demo}"

for tool in iobrpy-cli iobrpy fastp salmon run-trust4; do
  command -v "${tool}" >/dev/null 2>&1 || {
    echo "${tool} is not on PATH. Complete the installation chapter first." >&2
    exit 2
  }
done

[[ -f "${FASTQ_DIR}/subset_manifest.json" ]] || {
  echo "FASTQ subset is missing. Run scripts/fetch_demo_fastq.py first." >&2
  exit 2
}

[[ -s "${INDEX_DIR}/versionInfo.json" ]] || {
  echo "Salmon index is missing. Run scripts/build_salmon_index.sh first." >&2
  exit 2
}

mkdir -p "${RESULTS_DIR}" "${LOG_DIR}"

echo "Checking the installed IOBRpy environment..."
iobrpy-cli doctor --json

echo "Mapping the FASTQ directory before execution..."
iobrpy-cli map --path "${FASTQ_DIR}" --json

echo "Requesting the CLI-native workflow recommendation..."
iobrpy-cli recommend \
  --path "${FASTQ_DIR}" \
  --task "Run the teaching FASTQ dataset through Salmon and the full IOBRpy workflow" \
  --json

echo "Starting the FASTQ-to-TME workflow..."
iobrpy-cli runall \
  --fastq "${FASTQ_DIR}" \
  --outdir "${RESULTS_DIR}" \
  --mode salmon \
  --index "${INDEX_DIR}" \
  --threads "${THREADS}" \
  --batch_size "${BATCH_SIZE}" \
  --project "${PROJECT_NAME}" \
  2>&1 | tee "${LOG_DIR}/runall.log"

echo "Workflow finished: ${RESULTS_DIR}"
