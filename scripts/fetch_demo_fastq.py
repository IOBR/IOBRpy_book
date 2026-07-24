#!/usr/bin/env python3
"""Stream deterministic FASTQ prefixes for the IOBRpy teaching dataset."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path


USER_AGENT = "IOBRpy-Bookdown-Tutorial/1.0"


def parse_args() -> argparse.Namespace:
    project_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description=(
            "Stream the first N complete paired-end FASTQ records from the "
            "public PRJNA482620 files listed in data/demo_samples.csv."
        )
    )
    parser.add_argument(
        "--samples",
        type=Path,
        default=project_dir / "data" / "demo_samples.csv",
        help="Pinned sample metadata CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_dir / "data" / "fastq",
        help="Directory for the downsampled FASTQ files.",
    )
    parser.add_argument(
        "--reads-per-sample",
        type=int,
        default=50_000,
        help="Complete read pairs retained per sample (default: 50000).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing subset made with different settings.",
    )
    return parser.parse_args()


def load_samples(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"run_accession", "source_r1", "source_r2"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{path} is empty or missing required columns: {required}")
    return rows


def read_record(handle: gzip.GzipFile) -> tuple[bytes, bytes, bytes, bytes] | None:
    header = handle.readline()
    if not header:
        return None
    sequence = handle.readline()
    plus = handle.readline()
    quality = handle.readline()
    if not sequence or not plus or not quality:
        raise ValueError("Source FASTQ ended in the middle of a record")
    if not header.startswith(b"@") or not plus.startswith(b"+"):
        raise ValueError("Source does not look like FASTQ")
    if len(sequence.rstrip(b"\r\n")) != len(quality.rstrip(b"\r\n")):
        raise ValueError("Sequence and quality lengths differ")
    return header, sequence, plus, quality


def stream_prefix(url: str, output_path: Path, limit: int) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    part_path = output_path.with_suffix(output_path.suffix + ".part")
    count = 0

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            with gzip.GzipFile(fileobj=response, mode="rb") as source:
                with part_path.open("wb") as raw_output:
                    with gzip.GzipFile(
                        fileobj=raw_output,
                        mode="wb",
                        compresslevel=6,
                        mtime=0,
                    ) as destination:
                        while count < limit:
                            record = read_record(source)
                            if record is None:
                                break
                            for line in record:
                                destination.write(line)
                            count += 1
        if count != limit:
            raise ValueError(
                f"{url} supplied {count} records; {limit} were requested"
            )
        os.replace(part_path, output_path)
        return count
    finally:
        if part_path.exists():
            part_path.unlink()


def stream_with_retries(url: str, output_path: Path, limit: int) -> int:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            return stream_prefix(url, output_path, limit)
        except Exception as exc:  # network failures need a bounded retry
            last_error = exc
            if attempt < 3:
                delay = 2**attempt
                print(f"  retry {attempt}/2 after {delay}s: {exc}", file=sys.stderr)
                time.sleep(delay)
    assert last_error is not None
    raise last_error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    if args.reads_per_sample < 1:
        raise ValueError("--reads-per-sample must be positive")

    samples = load_samples(args.samples.resolve())
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "subset_manifest.json"

    if manifest_path.exists() and not args.force:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        old_n = old.get("reads_per_sample")
        expected = [
            output_dir / f"{row['run_accession']}_{mate}.fastq.gz"
            for row in samples
            for mate in (1, 2)
        ]
        if old_n == args.reads_per_sample and all(path.exists() for path in expected):
            print(
                f"FASTQ subset already exists with {old_n} read pairs per sample."
            )
            return 0
        raise RuntimeError(
            "An existing subset uses different settings. Re-run with --force "
            "or choose another --output-dir."
        )

    entries: list[dict[str, object]] = []
    for row in samples:
        accession = row["run_accession"]
        print(f"{accession}: streaming {args.reads_per_sample} read pairs")
        mate_counts: list[int] = []
        files: list[dict[str, object]] = []

        for mate in (1, 2):
            url = row[f"source_r{mate}"]
            output_path = output_dir / f"{accession}_{mate}.fastq.gz"
            count = stream_with_retries(url, output_path, args.reads_per_sample)
            mate_counts.append(count)
            files.append(
                {
                    "mate": mate,
                    "path": output_path.name,
                    "records": count,
                    "bytes": output_path.stat().st_size,
                    "sha256": sha256(output_path),
                    "source_url": url,
                    "source_md5": row.get(f"source_r{mate}_md5", ""),
                    "source_bytes": int(row.get(f"source_r{mate}_bytes", "0")),
                }
            )
            print(f"  R{mate}: {output_path.name} ({output_path.stat().st_size:,} B)")

        if mate_counts[0] != mate_counts[1]:
            raise ValueError(f"{accession}: R1/R2 record counts differ")
        entries.append(
            {
                "run_accession": accession,
                "patient": row.get("patient", ""),
                "group": row.get("group", ""),
                "records_per_mate": mate_counts[0],
                "files": files,
            }
        )

    manifest = {
        "dataset": "PRJNA482620 teaching subset",
        "reads_per_sample": args.reads_per_sample,
        "sample_count": len(samples),
        "deterministic_gzip_mtime": 0,
        "samples": entries,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

