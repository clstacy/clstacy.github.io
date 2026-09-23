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
description: "A practical guide to BBDuk for adapter trimming, quality filtering, and contamination screening, with a worked example you can reproduce and an explanation of what each flag actually does."
---

This is part of a series on the BBTools suite. If you haven't read the [overview post](/posts/2026/04/bbtools-overview/), that's a good place to start.

---

BBDuk is the quality control tool in the BBTools suite. It handles adapter trimming, quality filtering, and k-mer based contamination screening in a single pass. This post walks through how it works, what the flags actually mean, and why I use it over the alternatives. Every number below comes from a run you can reproduce on your own machine in under a minute.

## The example data

Rather than hand you a command and a screenshot, I want you to be able to run everything in this series yourself, so the example data is simulated with a tool that ships inside BBTools. `randomreads.sh` generates reads from a reference, and if you tell it the adapter sequences, it inserts them exactly where a real library would: at the 3' end of any pair whose insert is shorter than the read. The reference is the lambda phage genome, which also ships with BBTools, so nothing needs downloading.

```bash
# BB is the directory where BBTools is installed
BB=/path/to/bbmap
cp $BB/resources/lambda.fa.gz $BB/resources/phix174_ill.ref.fa.gz .
mv phix174_ill.ref.fa.gz phix.fa.gz

# 20,000 lambda pairs, 2x150 bp, inserts 100-400 bp, TruSeq adapters
randomreads.sh ref=lambda.fa.gz out=lambda_R1.fq out2=lambda_R2.fq \
  reads=20000 length=150 paired=t mininsert=100 maxinsert=400 flat=t \
  minq=18 midq=30 maxq=36 qv=6 illuminanames=t prefix=lambda seed=42 \
  fragadapter=AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATCACGATCTCGTATGCCGTCTTCTGCTTG \
  fragadapter2=AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT

# 500 phiX pairs spiked in as contamination
randomreads.sh ref=phix.fa.gz out=phix_R1.fq out2=phix_R2.fq \
  reads=500 length=150 paired=t mininsert=150 maxinsert=400 flat=t \
  minq=18 midq=30 maxq=36 qv=6 illuminanames=t prefix=phix seed=7

cat lambda_R1.fq phix_R1.fq | gzip > raw_R1.fq.gz
cat lambda_R2.fq phix_R2.fq | gzip > raw_R2.fq.gz
```

The whole script is at [/files/bbtools_demo_data.sh](/files/bbtools_demo_data.sh). With a flat insert distribution from 100 to 400 bp and 150 bp reads, about one pair in six has an insert shorter than the read, so about one pair in six carries adapter sequence. That is a realistic fraction for an RNA-seq library. The phiX spike-in becomes relevant in the [BBMap post](/posts/2026/09/bbmap-guide/). If you would rather use real data, any small paired-end run from SRA works; the flags below do not change.

## Running BBDuk

Here is the command from the overview post, now with paired-end input:

```bash
bbduk.sh \
  in=raw_R1.fq.gz \
  in2=raw_R2.fq.gz \
  out=clean_R1.fq.gz \
  out2=clean_R2.fq.gz \
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

BBDuk prints a summary to stderr when it finishes. On the demo data (BBTools 40.02):

```
Input:                  41000 reads     6150000 bases.
QTrimmed:               19396 reads (47.31%)  275594 bases (4.48%)
KTrimmed:               5382 reads (13.13%)   171934 bases (2.80%)
Trimmed by overlap:     1332 reads (3.25%)    7498 bases (0.12%)
Total Removed:          584 reads (1.42%)     455026 bases (7.40%)
Result:                 40416 reads (98.58%)  5694974 bases (92.60%)
```

Read this line by line, because each row answers a different question. `KTrimmed` plus `Trimmed by overlap` is the adapter story: 6,714 reads had adapter removed, which is 16.4% of the input and matches the one-in-six pairs we built with short inserts. `QTrimmed` counts reads that lost at least one base to quality trimming, and the number of reads is large (47%) while the number of bases is small (4.5%); that is the signature of trimming a few low-quality bases off the tail of many reads rather than gutting a few bad ones. `Total Removed` is reads discarded outright, here 584 reads that fell under 50 bp after trimming. On real Illumina data you should expect the same shape: adapter on a minority of reads, light quality trimming on many, and a small fraction discarded.

## What each flag does

This is the part that's worth understanding rather than copying.

**`ref=adapters`** tells BBDuk what to trim. The bare keyword `adapters` (no path, no file extension) loads the adapter file that ships in `resources/adapters.fa`, which has 158 entries covering TruSeq, Nextera, and most other common Illumina adapters. You can pass your own FASTA file instead if you know exactly which adapters were used, and you can pass literal sequences with `literal=ACGT...`.

**`ktrim=r`** sets the trimming direction. `r` means right-trim: once an adapter k-mer is found, everything from that point to the 3' end of the read is removed. This is what you want for standard Illumina data. `ktrim=l` trims to the left for 5' adapters, which is rare. `ktrim=f` is the default and means no trimming at all; in that mode BBDuk filters whole reads that match a reference k-mer, which is the contamination-screening mode covered below. Masking instead of trimming is a separate option, `kmask=N`.

**`k=23`** sets the k-mer length for adapter matching. Longer k-mers mean fewer false positives but miss adapters that are only partially present. The BBDuk guide recommends 23 for adapter trimming, and if the data are low quality it suggests dropping to `k=21` with `hdist=2`.

**`mink=11`** is the flag people skip that actually matters. When an adapter starts within the last few bases of a read, there are not 23 adapter bases to match. `mink=11` lets BBDuk use progressively shorter k-mers, down to 11, at the read tip, so those short adapter remnants are caught. Without it they stay in the read.

**`hdist=1`** allows one mismatch when matching adapter k-mers, which catches sequencing errors inside the adapter. `hdist=2` catches more at the cost of more false positives and more memory.

**`tpe`** and **`tbo`** are the two paired-end flags, and they work together. With short inserts, both R1 and R2 read through into adapter. `tbo` (trim by overlap) finds the overlap between the two reads and trims adapter based on where the insert ends, which needs no adapter sequence at all. `tpe` (trim pairs evenly) trims both reads to the same length when a k-mer hit was found in only one of them. In the run above, `tbo` caught 1,332 reads that the k-mer search alone would have missed.

**`qtrim=r`** enables quality trimming on the right end only. BBDuk uses the Phred algorithm for this: rather than scanning inward and stopping at the first base above the threshold, it keeps the contiguous stretch of the read whose bases are, in aggregate, better than the threshold, and trims everything outside it. That is why a single good base in a bad tail does not stop the trim. `qtrim=rl` trims both ends and `qtrim=w` uses a sliding window. Quality trimming runs after all k-mer operations.

**`trimq=20`** is the threshold for `qtrim`. Q20 is a 1% error probability and a reasonable default for most analyses. If you plan to merge the pairs afterwards, skip quality trimming or use something gentle like `trimq=8`; the [BBMerge post](/posts/2026/10/bbmerge-guide/) explains why.

**`minlen=50`** discards any read shorter than 50 bases after trimming. Very short reads add noise, not signal. For RNA-seq I use 50; for amplicon work you might go lower.

**`stats=bbduk_stats.txt`** writes per-adapter counts to a file, which is the quickest way to confirm that the adapters you expect are the adapters you have.

## What the stats file tells you

```
#File   raw_R1.fq.gz  raw_R2.fq.gz
#Total  41000
#Matched  5345  13.03659%
#Name                               Reads  ReadsPct
Reverse_adapter                     2025   4.93902%
pcr_dimer                           1348   3.28780%
TruSeq_Adapter_Index_1_6            910    2.21951%
PCR_Primers                         606    1.47805%
Nextera_LMP_Read2_External_Adapter  387    0.94390%
TruSeq_Universal_Adapter            56     0.13659%
```

We simulated exactly two adapters, a TruSeq indexed adapter on read 1 and the reverse complement of the universal adapter on read 2, yet the table names six. This is worth understanding so it does not alarm you on real data. Many entries in the adapter file share k-mers (`pcr_dimer` and `PCR_Primers` are built from the same TruSeq sequences), and each read is credited to the first entry whose k-mer it matched. The table is a sanity check, not a census: read it for the family of adapters it points at (all TruSeq here, no Nextera transposase) rather than the exact split between rows. If you see a family you did not expect, the library prep or the kit is not what you were told. If almost nothing is trimmed, double-check that the reference is right.

## Contamination screening

The same k-mer machinery filters whole reads against anything you name. This removes the phiX spike-in from the cleaned reads:

```bash
bbduk.sh in=clean_R1.fq.gz in2=clean_R2.fq.gz \
  out=nophix_R1.fq.gz out2=nophix_R2.fq.gz \
  outm=isphix_R1.fq.gz outm2=isphix_R2.fq.gz \
  ref=phix k=31 hdist=1
```

```
Input:          40416 reads   5694974 bases.
Contaminants:   984 reads (2.43%)   141746 bases (2.49%)
Result:         39432 reads (97.57%)  5553228 bases (97.51%)
```

No `ktrim` is set, so BBDuk is in its default filter mode, and `ref=phix` is another built-in keyword. `k=31` is the default and is the right choice for filtering: a 31-mer is long enough to be specific, and any read sharing a single 31-mer with phiX is pulled out. Because the reads are named by origin, this run can be graded: 492 phiX pairs survived trimming, all 492 landed in `outm`, and no lambda read did. If either read in a pair matches, the whole pair goes to `outm`; that is the `rieb` (remove if either bad) default and it is what you want. The [BBMap post](/posts/2026/09/bbmap-guide/) does the same job by alignment and compares the two.

## A few things worth knowing

**BBDuk processes everything in a single pass.** Adapter trimming, quality trimming, and length filtering happen together, and k-mer trimming always runs before quality trimming regardless of the order you type the flags.

**The k-mer modes are mutually exclusive.** `ktrim`, `kmask`, and the default filter mode cannot be combined in one run. To trim adapters and filter phiX you run BBDuk twice, as above, or pass both references to a single filter-mode run if trimming is not needed.

**Pass the adapters you actually used when you know them.** The built-in file is broad, which is what you want when you are unsure. When you are sure, a two-sequence file is faster and gives a cleaner stats table.

**Check the pairing of your file arguments.** `in`/`out` are read 1, `in2`/`out2` are read 2. BBDuk will not complain if you swap them; it will just produce the wrong answer quietly.

**Reads are discarded as pairs.** If one read of a pair drops below `minlen`, the pair goes. That keeps `out` and `out2` in sync, which downstream tools require.

## The single-end version

```bash
bbduk.sh \
  in=reads.fq.gz \
  out=cleaned.fq.gz \
  ref=adapters \
  ktrim=r \
  k=23 \
  mink=11 \
  hdist=1 \
  qtrim=r \
  trimq=20 \
  minlen=50
```

Drop `in2`, `out2`, `tpe`, and `tbo`. Everything else stays the same.

---

Next in the series: BBMap for alignment and contamination filtering, on the same data. If something behaved unexpectedly on your reads, or a flag here is unclear, get in touch.
