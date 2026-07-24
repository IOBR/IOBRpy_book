# Demo data

`demo_samples.csv` pins four public pretreatment paired-end RNA-seq runs from
the glioblastoma anti-PD-1 project `PRJNA482620`.

Run:

```bash
python scripts/fetch_demo_fastq.py
```

The script streams only the requested number of complete FASTQ records from
each source mate and writes deterministic gzip files under `data/fastq/`.
The default is 50,000 read pairs per sample.

The subset is intended for workflow teaching and smoke testing. It is not
large enough for stable biological comparisons, repertoire diversity
estimation, or publication-quality TME inference.
