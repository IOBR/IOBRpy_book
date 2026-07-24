#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFERENCE_DIR="${REFERENCE_DIR:-${PROJECT_DIR}/reference}"
SOURCE_DIR="${REFERENCE_DIR}/gencode-v36"
INDEX_DIR="${INDEX_DIR:-${REFERENCE_DIR}/star-gencode-v36}"
THREADS="${THREADS:-4}"
SJDB_OVERHANG="${SJDB_OVERHANG:-100}"

FA_GZ="${SOURCE_DIR}/GRCh38.primary_assembly.genome.fa.gz"
FA="${SOURCE_DIR}/GRCh38.primary_assembly.genome.fa"
GTF_GZ="${SOURCE_DIR}/gencode.v36.annotation.gtf.gz"
GTF="${SOURCE_DIR}/gencode.v36.annotation.gtf"
FA_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/GRCh38.primary_assembly.genome.fa.gz"
GTF_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.annotation.gtf.gz"

for tool in STAR curl gzip; do
  command -v "${tool}" >/dev/null 2>&1 || {
    echo "${tool} is not on PATH. Complete the installation chapter first." >&2
    exit 2
  }
done

if [[ -s "${INDEX_DIR}/Genome" && -s "${INDEX_DIR}/genomeParameters.txt" ]]; then
  echo "STAR index already exists: ${INDEX_DIR}"
  exit 0
fi

mkdir -p "${SOURCE_DIR}" "${INDEX_DIR}"

if [[ ! -s "${FA_GZ}" ]]; then
  echo "Downloading the GENCODE v36 genome FASTA..."
  curl --fail --location --retry 3 --output "${FA_GZ}.part" "${FA_URL}"
  mv "${FA_GZ}.part" "${FA_GZ}"
fi

if [[ ! -s "${GTF_GZ}" ]]; then
  echo "Downloading the GENCODE v36 annotation GTF..."
  curl --fail --location --retry 3 --output "${GTF_GZ}.part" "${GTF_URL}"
  mv "${GTF_GZ}.part" "${GTF_GZ}"
fi

if [[ ! -s "${FA}" ]]; then
  echo "Decompressing the genome FASTA..."
  gzip -dc "${FA_GZ}" > "${FA}.part"
  mv "${FA}.part" "${FA}"
fi

if [[ ! -s "${GTF}" ]]; then
  echo "Decompressing the annotation GTF..."
  gzip -dc "${GTF_GZ}" > "${GTF}.part"
  mv "${GTF}.part" "${GTF}"
fi

echo "Building the STAR genome index..."
STAR \
  --runMode genomeGenerate \
  --runThreadN "${THREADS}" \
  --genomeDir "${INDEX_DIR}" \
  --genomeFastaFiles "${FA}" \
  --sjdbGTFfile "${GTF}" \
  --sjdbOverhang "${SJDB_OVERHANG}"

echo "Index ready: ${INDEX_DIR}"
