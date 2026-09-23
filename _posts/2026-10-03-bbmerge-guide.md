---
title: 'BBMerge: Overlapping Read Pairs, and the Adapter Trick Nobody Mentions'
date: 2026-10-03
permalink: /posts/2026/10/bbmerge-guide/
tags:
  - bioinformatics
  - bbtools
  - bbmerge
  - paired-end
  - tutorial
description: "A practical guide to BBMerge: merging overlapping paired reads into single longer reads, choosing a strictness level, checking the false-merge rate against known truth, and using BBMerge to discover the adapter sequences in a library you know nothing about."
---

This is part of a series on the BBTools suite. The demo data come from the [BBDuk post](/posts/2026/04/bbduk-guide/), and the [BBMap post](/posts/2026/09/bbmap-guide/) removed the phiX spike-in.

---

When a paired-end insert is shorter than twice the read length, the two reads overlap, and the overlap can be used to stitch them into one longer, higher-quality read. BBMerge does that. It is the tool in the suite I was most sceptical of, because a wrong merge is worse than no merge, so this post spends more time than usual on checking the answer. It also covers a feature that has saved me more than once: BBMerge can tell you what adapters are in a library from the reads alone.

## When merging is worth doing

Merging helps when the reads will be assembled, clustered, or used for anything where a single 250 bp read is more useful than two 150 bp reads that happen to overlap: amplicon studies, small-genome assembly, and anything k-mer based, where longer reads allow longer k-mers. The overlapping region also gets error-corrected in the process, because two independent reads of the same bases disagree where one of them is wrong.

Merging does not help when you will simply map the reads to a reference and count them, since a mapper handles pairs perfectly well, and it is a bad idea for long-mate-pair libraries, which are not in the "innie" orientation BBMerge expects. The BBMerge guide's rule of thumb is that if fewer than about 15% of pairs merge even at loose settings, merging is not worth the added complexity for that library.

## Discovering adapters first

This is the trick. Any pair whose insert is shorter than the read has adapter sequence after the insert, and once BBMerge has found the overlap it knows exactly where the insert ends and therefore where the adapter begins. Ask it to report the consensus of what follows:

```bash
bbmerge.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz outa=discovered_adapters.fa
```

On the raw demo reads this writes:

```
>Read1_adapter
AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATCACGATCTCGTATG
>Read2_adapter
AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCC
```

Those are the first 50 bases of the two adapters the simulator added, recovered exactly, with no adapter file given. When someone hands you FASTQ files with no record of the library kit, this is how you find out what to trim. It only works for libraries with some short inserts, which in practice is nearly all of them.

## Trim adapters, but not quality

The guide is explicit that adapter trimming before merging is fine and recommended, and that quality trimming is usually not, because it shortens the overlap and lowers the merge rate. So for merging, the BBDuk command drops `qtrim` and `trimq`:

```bash
bbduk.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz \
  out=atrim_R1.fq.gz out2=atrim_R2.fq.gz \
  ref=adapters ktrim=r k=23 mink=11 hdist=1 tpe tbo minlen=50

bbduk.sh in=atrim_R1.fq.gz in2=atrim_R2.fq.gz \
  out=atrim_nophix_R1.fq.gz out2=atrim_nophix_R2.fq.gz \
  ref=phix k=31 hdist=1
```

The difference is measurable. Merging the quality-trimmed reads from the BBDuk post gives 53.9% joined; merging the adapter-trimmed reads gives 57.3%. That is 700 more pairs merged for the price of leaving the quality trimming to a later step, and the merged region is error-corrected anyway.

## Merging

```bash
bbmerge.sh \
  in=atrim_nophix_R1.fq.gz \
  in2=atrim_nophix_R2.fq.gz \
  out=merged.fq.gz \
  outu=unmerged_R1.fq.gz \
  outu2=unmerged_R2.fq.gz \
  ihist=merge_ihist.txt \
  adapters=discovered_adapters.fa
```

Merged reads go to `out`, pairs that could not be merged go to `outu` and `outu2` unchanged, so nothing is lost. The `adapters=` argument is the discovered file from above (or a literal sequence, or the built-in `adapters.fa`); BBMerge uses it to confirm that a pair whose implied insert is shorter than the read really does have adapter where the insert ends, which the guide says substantially improves accuracy. Do not use it if the left end of the reads has been trimmed. The summary on the demo data:

```
Pairs:               20000
Joined:              11461    57.305%
Ambiguous:           0        0.000%
No Solution:         8539     42.695%
Too Short:           0        0.000%
Adapters Expected:   2        0.005%
Adapters Found:      2        0.005%

Avg Insert:          186.7
Standard Deviation:  50.8
Mode:                182

Insert range:        100 - 282
```

**Joined** is the merge rate. **Ambiguous** counts pairs where two overlap lengths scored comparably, which BBMerge refuses to guess at; zero here, a few percent on low-complexity data. **No Solution** is pairs with no usable overlap, which on this library is mostly pairs whose insert is longer than about 288 bp (two reads of 150 minus the 12-base minimum overlap). The insert statistics are computed only from merged pairs, so they describe the mergeable part of the distribution, not the library; for the whole library use the `ihist` from BBMap.

## Checking the answer

A merge rate tells you how many pairs were joined. It says nothing about whether they were joined at the right overlap, and a wrong overlap produces a chimeric read with a plausible length and no warning. Because the demo reads are simulated, I can check. Regenerating the same reads with `renamebyinsert=t` puts the true insert size in every read name, and a merged read is correct if its length equals that insert. Across the strictness levels:

```
level     joined            wrong length
vstrict   10724  (53.6%)    0
strict    11245  (56.2%)    0
default   11461  (57.3%)    0
loose     11882  (59.4%)    0
```

Zero false merges at every level, out of 12,544 pairs that were mergeable in principle. The guide claims BBMerge has by far the lowest false-positive rate of any overlap merger, and on clean simulated reads that is what I see. It is not a guarantee for your data; low-complexity amplicons and low-quality tails are where wrong overlaps come from, and the check above is cheap enough to run on a subsample of anything that matters. On a real library you do not have the truth, but you can map the merged reads back to the reference and look at how many align end-to-end.

The strictness levels are presets over the underlying parameters, from `xstrict` through `vstrict`, `strict`, default, `loose`, `vloose` to `xloose`. Stricter settings merge fewer pairs with fewer false positives. The guide's own practice is `vstrict` when preparing reads for assembly and `loose` when the goal is an insert-size distribution, and that is a sensible pair of defaults.

## Error correction without merging

If you want the accuracy benefit of the overlap but need to keep the reads paired, `ecco` corrects the overlapping bases in place and `mix` writes everything back out as pairs:

```bash
bbmerge.sh in=atrim_R1.fq.gz in2=atrim_R2.fq.gz \
  out=ecco_R1.fq.gz out2=ecco_R2.fq.gz ecco mix
```

On the demo data this corrected 6,616 bases across the 11,709 overlapping pairs and changed no read lengths. Where the two reads disagree, the base with the higher quality wins and the quality scores are adjusted; the reads that did not overlap pass through untouched.

## Settings worth knowing

**`minoverlap=12`** and **`mininsert=15`** are the floor on what counts as an overlap. For small-RNA libraries with very short inserts you lower both.

**`outa`** (the adapter discovery above) works on raw reads and should be run before any trimming.

**`ihist`** writes the insert-size histogram of merged pairs to a file, which is the right thing to plot when a sequencing core asks what your fragment size came out at.

**`qtrim2=r trimq=8`** is the guide's suggested compromise if a library has a bad right end and merges poorly: trim only after a merge attempt fails, and only gently.

**`extend2` and `k`** turn on k-mer extension using Tadpole, which can merge pairs that do not overlap by extending each read through the k-mer graph of the whole library. It needs coverage (5x or more), it needs a shotgun library rather than an amplicon, and it needs `bbmerge-auto.sh` rather than `bbmerge.sh` so that Java is given enough memory. The guide's command for maximising correct merges on a well-covered fragment library is `bbmerge-auto.sh in=reads.fq out=merged.fq adapter1=... adapter2=... rem k=62 extend2=50 ecct`.

## What I do

I run `outa` on every new library before I do anything else, because it takes seconds and it has caught mislabelled kits twice. I merge only when the downstream step benefits from longer reads, with adapter trimming but no quality trimming beforehand, with the adapter sequences passed in, and at `vstrict` if the reads are going into an assembler. And I do not trust a merge rate on its own: on a subsample I check that merged reads map end-to-end to whatever reference I have, because the failure mode of a read merger is quiet and the check is not expensive.

---

That covers the three tools that handle most of my read preprocessing: BBDuk, BBMap and BBMerge. Next in the series I want to look at the utilities that never get a write-up, starting with Reformat and Clumpify, which are the two I would miss most.
