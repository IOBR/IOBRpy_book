#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFERENCE_DIR="${REFERENCE_DIR:-${PROJECT_DIR}/reference}"
SOURCE_DIR="${REFERENCE_DIR}/gencode-v36"
INDEX_DIR="${INDEX_DIR:-${REFERENCE_DIR}/salmon-gencode-v36}"
FA_GZ="${SOURCE_DIR}/gencode.v36.transcripts.fa.gz"
FA="${SOURCE_DIR}/gencode.v36.transcripts.fa"
URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.transcripts.fa.gz"

command -v salmon >/dev/null 2>&1 || {
  echo "salmon is not on PATH. Install it from Bioconda first." >&2
  exit 2
}
command -v curl >/dev/null 2>&1 || {
  echo "curl is not on PATH." >&2
  exit 2
}
command -v gzip >/dev/null 2>&1 || {
  echo "gzip is not on PATH." >&2
  exit 2
}

if [[ -s "${INDEX_DIR}/versionInfo.json" ]]; then
  echo "Salmon index already exists: ${INDEX_DIR}"
  exit 0
fi

mkdir -p "${SOURCE_DIR}" "${INDEX_DIR}"

if [[ ! -s "${FA_GZ}" ]]; then
  echo "Downloading GENCODE v36 transcripts..."
  curl --fail --location --retry 3 --output "${FA_GZ}.part" "${URL}"
  mv "${FA_GZ}.part" "${FA_GZ}"
fi

if [[ ! -s "${FA}" ]]; then
  echo "Decompressing transcriptome FASTA..."
  gzip -dc "${FA_GZ}" > "${FA}.part"
  mv "${FA}.part" "${FA}"
fi

echo "Building Salmon index..."
salmon index \
  --transcripts "${FA}" \
  --index "${INDEX_DIR}" \
  --kmerLen 31

echo "Index ready: ${INDEX_DIR}"

