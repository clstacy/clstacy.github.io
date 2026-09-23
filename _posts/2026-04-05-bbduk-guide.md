---
title: 'BBDuk: Adapter Trimming and Quality Filtering That Actually Makes Sense'
date: 2026-04-05
permalink: /posts/2026/04/bbduk-guide/
tags:
  - bioinformatics
  - bbtools
  - bbduk
  - tutorial
  - RNA-seq
description: "A practical guide to BBDuk for adapter trimming, quality filtering, and contamination screening — with a real worked example and explanation of what each flag actually does."
---

This is part of a series on the BBTools suite. If you haven't read the [overview post](/posts/2026/04/bbtools-overview/), that's a good place to start.

---

BBDuk is the quality control tool in the BBTools suite. It handles adapter trimming, quality filtering, and k-mer based contamination screening — all in a single pass. This post walks through how it works, what the flags actually mean, and why I use it over the alternatives.

## The Example Data

To keep this concrete I'm using simulated paired-end reads — 2,000 read pairs, 100 bp, with a realistic mix: some reads are clean, some have adapter contamination from a short insert, and some have low-quality tails toward the 3' end. If you want to follow along with real data, grab a small paired-end cancer RNA-seq run from SRA. For example, head and neck squamous cell carcinoma samples from [GSE181919](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181919) work well — pick any run from the SRA Run Selector and subsample:

```bash
fasterq-dump --split-files -e 4 SRR15336698
# subsample to keep it manageable
seqtk sample -s42 SRR15336698_1.fastq 50000 > demo_R1.fastq
seqtk sample -s42 SRR15336698_2.fastq 50000 > demo_R2.fastq
```

That pulls a paired-end HNSCC RNA-seq run and subsamples to 50,000 read pairs. The `--split-files` flag separates R1 and R2, and `seqtk sample` with the same seed (`-s42`) keeps the pairs in sync. Gzip them afterward (`gzip demo_R1.fastq demo_R2.fastq`) or just adjust the BBDuk input filenames below. If you don't have `seqtk`, `fasterq-dump` alone gives you the full dataset — just know it'll be larger.

## Running BBDuk

Here's the command from the overview post, now with paired-end input:

```bash
bbduk.sh \
  in=demo_R1.fastq.gz \
  in2=demo_R2.fastq.gz \
  out=clean_R1.fastq.gz \
  out2=clean_R2.fastq.gz \
  ref=adapters \
  ktrim=r \
  k=23 \
  mink=11 \
  hdist=1 \
  tpe \
  tbo \
  qtrim=r \
  trimq=20 \
  minlen=50 \
  stats=bbduk_stats.txt
```

BBDuk prints a summary to stderr when it finishes. For our demo data it looks something like:

```
Input:                  4000 reads          400000 bases
KTrimmed:               892 reads (22.30%)  14823 bases (3.71%)
QTrimmed:               547 reads (13.68%)  9841 bases (2.46%)
Total Removed:          312 reads (7.80%)   24664 bases (6.17%)
Result:                 3688 reads (92.20%) 375336 bases (93.83%)
```

That's the ballpark you'd expect on real Illumina data — somewhere around 20–30% of reads having some adapter or quality issue, with a small fraction removed entirely for being too short after trimming.

## What Each Flag Does

This is the part that's worth actually understanding rather than just copying.

**`ref=adapters`** tells BBDuk what to trim. Passing `adapters` (without a file extension) loads BBTools' built-in adapter database, which includes TruSeq, Nextera, and most other common Illumina adapter sequences. You can also pass your own FASTA file here if you know exactly what adapters were used.

**`ktrim=r`** sets the trimming direction. `r` means right-trim: once an adapter k-mer is found, everything from that point to the 3' end of the read is removed. This is what you want for standard Illumina data where adapters appear at the 3' end. Use `ktrim=l` for 5' adapters (rare) or `ktrim=f` to just mask without trimming.

**`k=23`** sets the k-mer length for adapter matching. Longer k-mers mean fewer false positives but miss adapter sequences that are partially sequenced. 23 is a solid default for 100 bp reads.

**`mink=11`** is the one flag people skip over that's actually important. When an adapter is very close to the end of a read, there may only be a few adapter bases overlapping — not enough for a full k=23 match. `mink=11` allows BBDuk to use shorter k-mers toward the 3' end to catch these cases. Without it, short adapter remnants at the very end of reads get missed.

**`hdist=1`** allows 1 mismatch when matching adapter k-mers. This catches sequencing errors in the adapter sequence itself, which do happen. Setting `hdist=2` catches more but increases false positives; `hdist=1` is a reasonable default.

**`tpe`** (trim pairs evenly) and **`tbo`** (trim by overlap) work together for paired-end data and are worth calling out specifically. With short inserts — common in RNA-seq — both R1 and R2 read into each other's adapter. `tbo` detects this by finding the overlap between the two reads and trimming accordingly. `tpe` ensures that if one read gets trimmed, its pair is trimmed to the same length. Together they handle the short-insert problem cleanly, which is something you have to address manually in other tools.

**`qtrim=r`** enables quality trimming, right side only. BBDuk scans from the 3' end and removes bases below the threshold set by `trimq`. Use `qtrim=rl` to trim both ends, or `qtrim=w` for a sliding window approach.

**`trimq=20`** sets the quality score threshold for `qtrim`. Q20 means a 1% error probability — a reasonable minimum for most analyses. Some people use Q30 for stricter pipelines.

**`minlen=50`** discards any read shorter than 50 bases after trimming. Reads that end up very short after adapter removal add noise more than signal. What you set this to depends on your application — for RNA-seq I typically use 50 bp; for amplicon work you might go lower.

**`stats=bbduk_stats.txt`** writes per-adapter statistics to a file. This is useful for confirming which adapters were actually found in your data — a good sanity check that you're using the right reference.

## What the Stats File Tells You

```
#Name                            Reads       ReadsPct
TruSeq_Adapter_Index_1           748         18.70%
TruSeq_Adapter_Index_2           144         3.60%
```

If you're seeing high rates on unexpected adapters, that's a signal something is off with the library prep or the wrong adapter kit was used. Conversely, if almost nothing is being trimmed, double-check that you have the right adapter reference.

## A Few Things Worth Knowing

**BBDuk processes everything in a single pass.** Adapter trimming, quality trimming, and length filtering all happen together. Some older workflows chain multiple tools for these steps; with BBDuk you don't need to.

**The built-in adapter database is comprehensive but not magic.** If you know exactly which kit was used — TruSeq, Nextera, NEBNext — it's worth passing the specific adapter sequences rather than the full database. Fewer targets means faster matching and fewer false positives on unusual sequences.

**For very short reads or amplicon data**, the defaults may need adjustment. Dropping `minlen` and increasing `mink` can help recover more usable reads when you expect short inserts by design.

**The output order matters if you're using paired-end mode.** Make sure `in`/`out` are R1 and `in2`/`out2` are R2, not mixed up. BBDuk won't error on swapped input — it'll just produce wrong results silently.

## The Full Single-End Version

If you're working with single-end data, it's simpler:

```bash
bbduk.sh \
  in=reads.fastq.gz \
  out=cleaned.fastq.gz \
  ref=adapters \
  ktrim=r \
  k=23 \
  mink=11 \
  hdist=1 \
  qtrim=r \
  trimq=20 \
  minlen=50
```

Drop `in2`, `out2`, `tpe`, and `tbo` — the rest stays the same.

---

Next up I'll cover BBMap for alignment and contamination filtering. If you have questions about BBDuk parameters or something behaved unexpectedly on your data, feel free to get in touch.
