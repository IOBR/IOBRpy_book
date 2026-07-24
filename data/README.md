# Demo data

`demo_samples.csv` pins four public paired-end RNA-seq runs from
`PRJNA482620`. They are the pretreatment responder/non-responder samples used in
the RIMA tutorial's glioblastoma anti-PD-1 example.

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

