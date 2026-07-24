#!/usr/bin/env python3
"""Check the structural contract of the IOBRpy FASTQ teaching run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EXPECTED_FILES = [
    "01-qc/.fastq_qc.done",
    "02-salmon/.batch_salmon.done",
    "02-salmon/.merge_salmon.done",
    "03-tpm/prepare_salmon.csv",
    "03-tpm/tpm_matrix.csv",
    "04-signatures/calculate_sig_score.csv",
    "05-tme/cibersort_results.csv",
    "05-tme/IPS_results.csv",
    "05-tme/estimate_results.csv",
    "05-tme/mcpcounter_results.csv",
    "05-tme/quantiseq_results.csv",
    "05-tme/epic_results.csv",
    "05-tme/deconvo_merged.csv",
    "06-LR_cal/lr_cal.csv",
    "07-TCRBCR/.trust4.done",
]


def parse_args() -> argparse.Namespace:
    project_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        default=project_dir / "results" / "gbm-demo",
        help="runall output directory.",
    )
    return parser.parse_args()


def csv_shape(path: Path) -> tuple[int, int, list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = sum(1 for row in reader if row)
    return rows, len(header), header


def main() -> int:
    root = parse_args().results.resolve()
    missing = [
        rel for rel in EXPECTED_FILES if not (root / rel).exists()
    ]

    report: dict[str, object] = {
        "results": str(root),
        "expected_file_count": len(EXPECTED_FILES),
        "missing": missing,
        "tables": {},
    }

    for rel in [
        "03-tpm/tpm_matrix.csv",
        "04-signatures/calculate_sig_score.csv",
        "05-tme/deconvo_merged.csv",
        "06-LR_cal/lr_cal.csv",
    ]:
        path = root / rel
        if path.exists():
            rows, columns, header = csv_shape(path)
            report["tables"][rel] = {
                "rows": rows,
                "columns": columns,
                "first_columns": header[:6],
            }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if missing:
        return 1

    tpm = report["tables"].get("03-tpm/tpm_matrix.csv", {})
    if tpm.get("rows", 0) < 1 or tpm.get("columns", 0) != 5:
        print(
            "TPM matrix should contain genes plus four teaching samples.",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

