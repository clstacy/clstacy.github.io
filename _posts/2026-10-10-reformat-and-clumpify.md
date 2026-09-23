---
title: 'Reformat and Clumpify: The Two BBTools Utilities I Would Miss Most'
date: 2026-10-10
permalink: /posts/2026/10/reformat-and-clumpify/
tags:
  - bioinformatics
  - bbtools
  - reformat
  - clumpify
  - tutorial
description: "Reformat handles the unglamorous file plumbing of sequencing work (subsampling, interleaving, format conversion, pulling reads out of a BAM) and Clumpify makes files smaller and finds duplicates without a reference. Worked examples with real output."
---

This is part of a series on the BBTools suite; the demo data are built in the [BBDuk post](/posts/2026/04/bbduk-guide/) and the BAM comes from the [BBMap post](/posts/2026/09/bbmap-guide/).

---

In the overview I said Reformat is the tool I have trouble explaining until someone has needed it. Here is my attempt anyway, alongside Clumpify, which does one strange thing (it sorts reads so that similar ones sit next to each other) that turns out to be useful in three different ways. Neither tool aligns anything or calls anything. They are the plumbing, and good plumbing is most of what makes a pipeline pleasant.

## Reformat

`reformat.sh` reads sequence data in one shape and writes it out in another. It accepts FASTA, FASTQ, SAM and BAM, gzipped or not, paired or interleaved, and it autodetects most of that from the file names. Every example below runs in about a second on the demo library.

### Exact subsampling

```bash
reformat.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz \
  out=sub_R1.fq.gz out2=sub_R2.fq.gz \
  samplereadstarget=5000 sampleseed=42
```

```
Input:    41000 reads          6150000 bases
Output:   10000 reads (24.39%) 1500000 bases (24.39%)
```

`samplereadstarget` asks for an exact number of output pairs, and it delivers exactly that (5,000 pairs, so 10,000 reads), with the pairs kept in sync across the two files. `samplerate=0.25` is the alternative if a fraction is what you want, and `sampleseed` makes either reproducible. This is the command I use to make a small test set from a large run before building anything, and to get equal read depth across samples when a downstream method is sensitive to that.

### Interleaving and de-interleaving

Some tools want one file with read 1 and read 2 alternating; others want two files. Reformat converts in either direction from the file arguments alone:

```bash
# two files -> one interleaved file
reformat.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz out=raw_interleaved.fq.gz

# one interleaved file -> two files
reformat.sh in=raw_interleaved.fq.gz out=deint_R1.fq.gz out2=deint_R2.fq.gz
```

Interleaving is detected from the read names when a single input is given, and `int=t` or `int=f` overrides the guess. If you have ever had a tool silently treat an interleaved file as single-end, add `vpair` to any Reformat command and it checks the names really do alternate:

```bash
reformat.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz vpair
```

```
Names appear to be correctly paired.
```

### FASTQ to FASTA, and the read-level histograms

```bash
reformat.sh in=clean_R1.fq.gz in2=clean_R2.fq.gz out=clean.fa.gz fastawrap=0
```

The output format follows the extension. `fastawrap=0` writes each sequence on one line, which is what most downstream parsers actually want despite the 70-column convention. In the other direction, FASTA to FASTQ needs a quality to invent (`qfake=30`).

The same pass can write histograms of everything Reformat sees, which is the fastest QC summary I know of:

```bash
reformat.sh in=clean_R1.fq.gz in2=clean_R2.fq.gz out=null \
  lhist=lhist.txt qhist=qhist.txt aqhist=aqhist.txt gchist=gchist.txt
```

`lhist` is read length (after BBDuk this shows the trimmed tail from 50 bp up to the untouched 150 bp reads), `qhist` is quality by position for each read of the pair, `aqhist` is average quality per read, and `gchist` is GC content. `out=null` means no reads are written, only the histograms. I look at `lhist` and `qhist` after every trimming run, because they show what the summary line only counts.

### Pulling reads back out of a BAM

This is the Reformat use that people do not know about, and it replaces a `samtools view | awk | samtools fastq` chain:

```bash
reformat.sh in=mapped.bam out=unmapped.fq.gz unmappedonly primaryonly
```

```
Input:    40416 reads
Output:   997 reads (2.47%)
```

Those 997 unmapped reads are the ones BBMap could not place on lambda, and 984 of them are the phiX spike-in from the BBMap post. `mappedonly` does the reverse. `primaryonly` drops secondary alignments so a read appears once, which matters whenever the output is going to be re-mapped or counted. Reformat can also filter on alignment properties (`minmapq`, `minidfilter`) and on read properties (`minlength`, `maxlength`, `minavgquality`, `mingc`, `maxgc`) in the same pass.

### Shrinking files without losing reads

```bash
reformat.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz out=q_R1.fq.gz out2=q_R2.fq.gz \
  quantize=0,8,13,22,27,32,37
```

Illumina quality scores from a NovaSeq already come binned; older runs have forty distinct values, and most of that resolution carries no information downstream tools use. Binning the qualities to the seven listed values took `raw_R1.fq.gz` from 3.01 MB to 2.07 MB, 31% smaller, with every base untouched. For archival storage that is worth having; for anything that is going to be base-quality recalibrated, leave the scores alone.

### Other things Reformat does that I reach for

`trd` (trim read descriptions) drops everything after the first space in the read name, which fixes tools that choke on Illumina's long headers. `underscore` swaps the spaces for underscores instead. `addslash` appends `/1` and `/2` for older tools that need them. `rcomp` reverse-complements everything, `rcompmate` only read 2. `tossjunk` discards reads with invalid characters, and `tossbrokenreads` discards reads whose sequence and quality lengths differ, which by default crashes the run so you notice. `reads=1000` processes only the first thousand, which is how I test a pipeline in seconds.

## Clumpify

Clumpify sorts reads so that reads sharing a k-mer, and therefore probably overlapping in the genome, are written next to each other. Nothing about the reads changes; only the order does. That one trick has three consequences.

### Smaller files

```bash
clumpify.sh in=raw_R1.fq.gz in2=raw_R2.fq.gz \
  out=clumped_R1.fq.gz out2=clumped_R2.fq.gz reorder
```

```
Reads In:        41000
Clumps Formed:    5405
```

gzip works by pointing back at earlier copies of a sequence, so similar reads placed next to each other compress better. `raw_R1.fq.gz` went from 3.01 MB to 2.34 MB, 22% smaller, and the reads are identical (I checked by sorting both files and diffing). On a real 100-fold-coverage library the gain is larger, because there are more overlapping reads to cluster. `reorder` sorts the clumps themselves for a little extra. Add `zl=9` for maximum compression, and if you do not need the qualities or the headers, the Clumpify guide's recipe is FASTA with `fastawrap=0` and renamed headers, which is the smallest a read file gets.

Because the read order changes, do not clumpify a file whose order carries meaning, for example one already sorted to match another file. Pairs stay together; clumping is done on read 1 and read 2 follows.

### Faster downstream tools

Tools that build caches keyed on sequence (aligners, k-mer counters, assemblers) run faster when consecutive reads hit the same part of the reference, because the relevant index blocks are already in memory. The guide lists this as a primary purpose. On the 20,000-pair demo the effect is not measurable, and I have not benchmarked it on a large one, so treat this as the guide's claim rather than mine.

### Duplicate removal without a reference

This is the use I want to draw attention to. Duplicate marking usually happens after alignment, from mapped coordinates. Clumpify finds duplicates from the sequences alone, so it works before alignment, on data with no reference, and on amplicons. To test it, I appended an exact copy of 2,000 randomly chosen pairs to the demo library (22,500 pairs total) and asked Clumpify to remove duplicates:

```bash
clumpify.sh in=withdups_R1.fq.gz in2=withdups_R2.fq.gz \
  out=dedup_R1.fq.gz out2=dedup_R2.fq.gz dedupe
```

```
Reads In:               45000
Duplicates Found:        4016    8.924%
Reads Out:              40984
```

Sixteen more reads than the 4,000 I added. That is not an error. The default `subs=2` calls two reads duplicates if they differ by at most two substitutions, and in a 48.5 kb genome sequenced to 115-fold coverage, eight pairs of simulated fragments happened to start and end at the same coordinates; with independent sequencing errors they differ by a base or two. With `subs=0` (exact matches only) Clumpify finds 4,002: my 4,000 plus one coincidental pair. The lesson is the one every duplicate-marking tool carries: on small genomes, deep coverage, or amplicons, a fragment with the same ends as another is not necessarily a PCR duplicate, and removing "duplicates" removes real reads. Clumpify keeps the highest-quality copy by default; `markduplicates` appends " duplicate" to the name instead of removing anything, which is what I use so the decision stays reversible, and `addcount` writes the copy number into the name instead.

For optical duplicates (clusters that are near each other on the flowcell, which arise from the instrument rather than the library) add `optical` and set `dupedist` for your platform; the usage text lists recommended values, and the reads need real Illumina names carrying tile and coordinates, which simulated reads do not have. `dedupe optical spany adjacent` is the combination the usage text gives for NovaSeq-style patterned flowcells.

## What I do

Every new dataset gets `reformat.sh ... reads=1000` first, to prove the pipeline runs before it runs on everything, and `vpair` if the files came from anyone else. I subsample with `samplereadstarget` for tests and for depth matching. I pull unmapped reads out of BAMs with Reformat rather than samtools because it takes one command. And I clumpify with `markduplicates` early, before alignment, because seeing the duplicate rate before I have chosen an aligner tells me something about the library that the alignment-based rate later confirms.

---

Next in the series: putting BBDuk, BBMap and BBMerge into a small Nextflow pipeline, with a container, profiles for a laptop and a cluster, and resume.
