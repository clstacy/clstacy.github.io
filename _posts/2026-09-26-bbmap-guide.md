---
title: 'BBMap: Alignment and Contamination Filtering Without the Ceremony'
date: 2026-09-26
permalink: /posts/2026/09/bbmap-guide/
tags:
  - bioinformatics
  - bbtools
  - bbmap
  - alignment
  - tutorial
description: "A practical guide to BBMap: building an index, mapping paired reads, reading the statistics it prints, and using it to pull contaminating reads out of a library. Every number comes from a run you can reproduce."
---

This is part of a series on the BBTools suite. The [overview](/posts/2026/04/bbtools-overview/) introduces the tools and the [BBDuk post](/posts/2026/04/bbduk-guide/) builds the demo data used here.

---

BBMap is the aligner in BBTools. It maps short or long reads to a reference, it is splice-aware, and it writes standard SAM or BAM. What makes it worth a post is less the alignment itself than the things around it: the index is built for you on first use, the statistics it prints answer the questions you would otherwise open a BAM to ask, and the same command that maps reads also sorts them into "belongs to my reference" and "does not", which is how I do most contamination filtering.

## The data

The reads are the simulated lambda-phage library from the BBDuk post, after adapter and quality trimming: 40,416 reads in `clean_R1.fq.gz` and `clean_R2.fq.gz`, of which 984 are phiX reads we spiked in as contamination. The reference is `lambda.fa.gz` from the BBTools `resources` folder. Because the reads are simulated, I know the truth for every one of them, which lets me grade the results below instead of just describing them.

## Building the index

```bash
bbmap.sh ref=lambda.fa.gz
```

This writes a `ref/` directory in the working directory holding the reference and its k-mer index. You do it once per reference; later runs find `ref/` automatically. For a small reference, or a one-off run, skip the disk entirely with `nodisk`, which builds the index in memory and writes nothing:

```bash
bbmap.sh ref=lambda.fa.gz nodisk in=reads.fq.gz out=mapped.sam
```

BBMap uses roughly 6 bytes of memory per reference base, so a human genome needs about 20 GB and a few minutes to index; there you want the on-disk version, built once. If you keep several references in one place, `build=2`, `build=3` and so on give each its own numbered index inside the same `ref/` folder.

## Mapping paired reads

```bash
bbmap.sh \
  in=clean_R1.fq.gz \
  in2=clean_R2.fq.gz \
  out=mapped.bam \
  covstats=covstats.txt \
  ihist=ihist.txt
```

Three things to note before looking at the output. BBMap detects that the input is paired from `in2` and maps the reads as pairs. The output extension decides the format: `.sam` for SAM, `.bam` for BAM, and `.fq` if all you want is the reads themselves, sorted by whether they mapped. (BBMap 40 wrote the BAM directly on my machine with no samtools installed; the guide still describes BAM output as needing samtools, so if yours fails, write SAM and use the `bamscript=bs.sh` option, which generates a small shell script that sorts and indexes it.) And the two extra flags ask for files you will always want: per-reference coverage and an insert-size histogram.

## Reading the statistics

BBMap prints a block of statistics to stderr when it finishes. This is the part of the output that most people scroll past and should not. On the demo data:

```
Read 1 data:        pct reads   num reads   pct bases   num bases
mapped:              97.5653%       19716    97.5170%     2778655
unambiguous:         97.5653%       19716    97.5170%     2778655
ambiguous:            0.0000%           0     0.0000%           0
perfect best site:   67.5624%       13653    67.9430%     1935973
Match Rate:                NA          NA    99.7036%     2770420
Error Rate:          30.7517%        6063     0.2964%        8235
Sub Rate:            30.7517%        6063     0.2964%        8235
Del Rate:             0.0000%           0     0.0000%           0
Ins Rate:             0.0000%           0     0.0000%           0

Reads:                       40416
Mapped reads:                39419
Percent mapped:              97.533
Percent proper pairs:        97.501
Average coverage:            115.268
Percent of reference bases covered:  100.00
```

**Percent mapped** is 97.5%. The 2.5% that did not map is 997 reads, and 984 of those are the phiX reads, which have no business mapping to lambda. So the unmapped fraction is telling you, correctly, how much of the library is not what you think it is. On real data this number is the first thing I look at: a library that should be 99% one organism and maps at 80% has a story to tell.

**Ambiguous** is the fraction of reads with more than one equally good mapping location. Lambda has no repeats to speak of, so it is zero here; on a mammalian genome you will see a few percent, and the `ambiguous=` flag decides what happens to them. The default, `best`, reports the first best site. `toss` treats them as unmapped, `random` picks one at random, and `all` reports every top-scoring site. For quantification, `toss` or `random` is usually the honest choice; `best` silently piles multi-mapping reads onto whichever copy comes first in the reference.

**Perfect best site** is the fraction of reads that aligned with no mismatches at all, 67.6%. The simulator added substitution errors at a rate implied by the quality scores; the observed per-base error rate is 0.30%, and 0.997 raised to the 150th power is 0.64, so about two thirds of reads should be error-free. They are. On real Illumina data this number is lower, and how much lower is a quick read on run quality.

**Error, Sub, Del and Ins rates** are given two ways. The per-read column (30.8% of reads contain at least one substitution) and the per-base column (0.30% of bases are substitutions) answer different questions, and the per-base one is what you compare between runs. Indel rates of zero are what you expect from a simulation without indels and are not what you will see on real data.

**Average coverage** and **percent of reference covered** come from the same alignments. 115-fold coverage across 100% of the lambda genome, with a standard deviation of 14, is a well-behaved library. `covstats.txt` has the same numbers per scaffold, which is what you want for a draft assembly or a metagenome where the interesting question is which contigs got covered.

`ihist.txt` reports the insert-size distribution estimated from mapped pairs. The mean here is 249.8 with a standard deviation of 87, which is what a flat distribution from 100 to 400 should produce (the mean of a uniform on that range is 250). On a real library this file is how you check that the fragment-size selection did what the core said it did.

## Contamination filtering

This is the use I reach for most often. Map the reads against the thing you want to remove, and keep whatever does not map:

```bash
bbmap.sh ref=phix.fa.gz nodisk \
  in=clean_R1.fq.gz in2=clean_R2.fq.gz \
  outu=nophix_R1.fq.gz outu2=nophix_R2.fq.gz \
  outm=isphix_R1.fq.gz outm2=isphix_R2.fq.gz \
  minid=0.95
```

`outu` receives unmapped reads and `outm` receives mapped ones. Because the output is FASTQ, the alignments are discarded and you get clean read files ready for the next step. The pairing rule matters: `outm` includes an unmapped read whose mate mapped, so pairs stay together and a pair is removed if either read hits the contaminant. `outu` therefore only gets pairs where neither read mapped.

Because the demo reads are named by origin, this run can be graded. 492 phiX pairs survived trimming; all 492 went to `outm`, and no lambda pair did. The BBDuk k-mer filter from the previous post gave exactly the same answer on these reads. The two approaches differ where it matters on real data: BBDuk asks whether a read shares any 31-mer with the contaminant and is fast and memory-light; BBMap asks whether the read aligns at a given identity and is slower but tolerates divergence. For phiX or a known vector, either is fine. For removing host reads from a microbiome sample, BBMap with `minid=0.95` is the one I use, and for removing something that might be a diverged relative of the reference, drop `minid` and add `local`.

**`minid=0.95`** sets the approximate minimum identity BBMap will look for. Higher is faster and less sensitive. The default is 0.76, which is deliberately permissive; for contamination filtering against a reference you trust, 0.95 says "only take it out if it really is this". Note that `minid` steers the search rather than filtering the results; `idfilter=0.95` is the strict version that discards alignments under the threshold after the fact.

## Settings worth knowing about

**`local`** switches from global to local alignment, which soft-clips poor read ends instead of forcing them to align. Useful for reads with residual adapter or for references that only partially match.

**`maxindel`** caps the indel length BBMap looks for, default 16,000. For RNA-seq against a genome with long introns the guide says to raise it to something like `maxindel=200k`, and to add `intronlen=10` so that deletions of at least 10 bp are written as `N` in the CIGAR string, which is what splice-aware downstream tools expect. `xstag=fs` (or `ss`, or `us` for unstranded) adds the XS strand tag that Cufflinks requires and StringTie uses.

**`fast`** and **`slow`** are macros that trade sensitivity for speed and back. `fast` is fine for a clean reference and short reads; the usage text warns that it is bad for RNA-seq. `vslow` exists for when you need every last divergent read.

**`qtrim=r trimq=10 untrim`** quality-trims reads before mapping and then restores the trimmed bases as soft-clipped in the output, so the alignment is cleaner without any bases being lost.

**`threads=N`** limits the worker threads; by default BBMap uses every core it can see, which is what you want on a laptop and not always what you want on a shared node.

**`-Xmx`** sets the Java heap, for example `bbmap.sh -Xmx24g ...`. The shell script picks a value automatically from available memory, and the only time you need to set it is when that guess is wrong: a big genome on a machine where other jobs are already holding most of the RAM.

## What I do

For a clean reference and a fragment library, the default command with `covstats` and `ihist` is what I run, and I read the stats block before I open the BAM. For contamination, I map against the contaminant with `outu` and a high `minid`, and I keep the `outm` reads rather than throwing them away, because a surprising amount of "contamination" turns out to be worth a look. For RNA-seq I raise `maxindel`, set `intronlen`, and add `xstag`. And when a mapping rate looks wrong, the first thing I do is run the reads through BBDuk's k-mer filter against a few likely contaminants, because the two tools agree on the easy cases and disagree informatively on the hard ones.

---

Next in the series: BBMerge, which turns overlapping read pairs into single longer reads, and which also discovers your adapter sequences for you. The demo data continues from here.
