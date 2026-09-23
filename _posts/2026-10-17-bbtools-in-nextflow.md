---
title: 'BBTools in Nextflow: The Whole Preprocessing Chain in One Reproducible Pipeline'
date: 2026-10-17
permalink: /posts/2026/10/bbtools-in-nextflow/
tags:
  - bioinformatics
  - bbtools
  - nextflow
  - reproducibility
  - tutorial
description: "BBDuk, BBMap and BBMerge as a small Nextflow DSL2 pipeline: a samplesheet in, a results folder out, one file that decides whether it runs on a laptop, in a container, or on a SLURM cluster, and resume that reruns only what changed. Runs on the demo data from the series."
---

This closes the run of BBTools posts. The [BBDuk](/posts/2026/04/bbduk-guide/), [BBMap](/posts/2026/09/bbmap-guide/), [BBMerge](/posts/2026/10/bbmerge-guide/) and [Reformat/Clumpify](/posts/2026/10/reformat-and-clumpify/) posts each ran one tool by hand on the same simulated library. A pipeline is what you write once you have done that by hand enough times to know what the steps are, and Nextflow is the tool I use for it. Everything below was run, and the three files are downloadable at the end.

## What the pipeline does

One samplesheet lists the samples. For each one: adapter-trim with BBDuk, remove phiX with BBDuk's k-mer filter, and then two branches. The mapping branch quality-trims and maps with BBMap, keeping the BAM, coverage and insert-size histogram. The merging branch takes the adapter-trimmed reads without quality trimming, discovers the adapters with BBMerge, and merges. The split follows the advice from the individual posts: quality trimming helps mapping and hurts merging, so the two branches get different inputs.

```
samplesheet.csv
      │
 ADAPTER_TRIM (bbduk ktrim)
      │
 CONTAMINANT_FILTER (bbduk ref=phix)
      ├── QUALITY_TRIM (bbduk qtrim) ── MAP (bbmap)
      └── MERGE (bbmerge outa, then merge)
```

Five processes, 130 lines of Nextflow including comments, and on the demo library the whole thing runs in about 25 seconds on a laptop.

## The samplesheet

```
sample,fastq_1,fastq_2
demo,data/raw_R1.fq.gz,data/raw_R2.fq.gz
```

A CSV with a header is the input format I recommend for any pipeline, because it is what a collaborator can produce in a spreadsheet and what you can diff. Nextflow reads it in three lines:

```groovy
reads = Channel.fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row -> tuple(row.sample, file(row.fastq_1), file(row.fastq_2)) }
```

Add a second row and the pipeline runs both samples, in parallel where the machine allows.

## One process, read closely

```groovy
process ADAPTER_TRIM {
    tag "$sample"
    publishDir { "${params.outdir}/${sample}/adapter_trim" }, mode: 'copy', pattern: '*.txt'

    input:
    tuple val(sample), path(r1), path(r2)

    output:
    tuple val(sample), path("${sample}_atrim_R1.fq.gz"), path("${sample}_atrim_R2.fq.gz"), emit: reads
    path "${sample}_adapters.txt"

    script:
    """
    bbduk.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} \\
        in=$r1 in2=$r2 \\
        out=${sample}_atrim_R1.fq.gz out2=${sample}_atrim_R2.fq.gz \\
        ref=adapters ktrim=r k=23 mink=11 hdist=1 tpe tbo minlen=50 \\
        stats=${sample}_adapters.txt
    """
}
```

The command inside the triple quotes is the BBDuk command from the BBDuk post. Two things are new. `-Xmx${task.memory.toGiga()}g` and `t=${task.cpus}` hand BBDuk the memory and threads that Nextflow allocated to the task, so the same process definition runs with 2 GB on a laptop and 32 GB on a cluster without editing the script. And `publishDir` with a `pattern` copies only the stats file to `results/`; the trimmed reads are intermediates and stay in Nextflow's `work/` directory, which is where the next process reads them from.

`emit: reads` names the output channel so the workflow block can say `ADAPTER_TRIM.out.reads` and pass it on. The workflow block is the whole DAG:

```groovy
workflow {
    ADAPTER_TRIM(reads)
    CONTAMINANT_FILTER(ADAPTER_TRIM.out.reads)
    QUALITY_TRIM(CONTAMINANT_FILTER.out.reads)
    MAP(QUALITY_TRIM.out, file(params.reference))
    MERGE(CONTAMINANT_FILTER.out.reads)
}
```

Nothing here says "run MAP and MERGE in parallel"; Nextflow works that out from the fact that neither depends on the other.

## The config file is where portability lives

`nextflow.config` holds the parameters, the default resources, and a set of profiles. The pipeline script never mentions where it is running.

```groovy
params {
    samplesheet = 'samplesheet.csv'
    reference   = 'lambda.fa.gz'
    contaminant = 'phix'
    outdir      = 'results'
}

process {
    cpus   = 2
    memory = 2.GB
    withName: MAP { memory = 4.GB }
}

profiles {
    standard    { process.executor = 'local' }
    docker      { docker.enabled = true
                  process.container = 'quay.io/biocontainers/bbmap:40.02--h09cc210_0' }
    singularity { singularity.enabled = true; singularity.autoMounts = true
                  process.container = 'quay.io/biocontainers/bbmap:40.02--h09cc210_0' }
    conda       { conda.enabled = true; process.conda = 'bioconda::bbmap=40.02' }
    slurm       { process.executor = 'slurm'; process.queue = 'normal'
                  process.cpus = 4; process.memory = 8.GB; process.time = 2.h
                  withName: MAP { cpus = 8; memory = 32.GB } }
}
```

`nextflow run main.nf -profile standard` uses whatever `bbduk.sh` is on your PATH. `-profile docker` or `-profile singularity` pulls the Biocontainers image for BBTools 40.02, pinned by tag, so the run is reproducible down to the tool version. `-profile conda` builds an environment from bioconda (the package is called `bbmap`, which I had wrong in the overview post and have now fixed). `-profile slurm` submits each task as a job with the resources listed. Profiles combine: `-profile slurm,singularity` is the usual cluster setup.

One honest caveat: I ran the `standard` profile end to end on the demo data, and the other profiles are written from the Nextflow documentation and the image tag I confirmed exists on quay.io, but there was no container runtime or scheduler where I ran this, so they are untested by me. If one misbehaves for you, tell me.

Three more lines in the config turn on Nextflow's provenance files:

```groovy
timeline { enabled = true; overwrite = true; file = "${params.outdir}/pipeline_info/timeline.html" }
report   { enabled = true; overwrite = true; file = "${params.outdir}/pipeline_info/report.html" }
trace    { enabled = true; overwrite = true; file = "${params.outdir}/pipeline_info/trace.txt" }
```

The trace from the demo run:

```
hash       name                       duration  realtime
1a/a649fc  ADAPTER_TRIM (demo)        3.6s      3.5s
45/c9573b  CONTAMINANT_FILTER (demo)  1.9s      1.8s
68/a36cf0  QUALITY_TRIM (demo)        1.3s      1.3s
fc/72d001  MAP (demo)                 10.2s     10.2s
05/d8c068  MERGE (demo)               8.2s      8.1s
```

Every task has a hash, which is the directory under `work/` where its inputs, script, logs and outputs live. When something fails, `cd work/fc/72d001*` and `cat .command.log` is the entire debugging workflow.

## Resume is the feature that changes how you work

```bash
nextflow run main.nf -profile standard -resume
```

```
[SUCCESS] completed=0 failed=0 cached=5
```

Nothing changed, so nothing ran. Then I edited the MERGE process to add `strict`, and resumed:

```
[PROCESS 65/26b767] MERGE (demo)
[SUCCESS] completed=1 failed=0 cached=4
```

Only MERGE reran, because only its script changed; the four upstream tasks were reused from `work/`. Nextflow decides this by hashing each task's script and inputs, so editing a downstream step never costs you the upstream compute. On the demo that saves twenty seconds. On a real cohort it saves the day of mapping you would otherwise repeat to change a merge flag.

One behaviour worth knowing, because it bit me while writing this. After the `strict` run, I reverted the edit and resumed again. Nextflow correctly reused the original MERGE task (11,461 merged reads, the same as the BBMerge post), but `results/demo/merge/` still held the files from the strict run (11,245), because the published copies from the later run were already sitting there. Deleting `results/` and resuming republished the right files without recomputing anything. So treat `results/` as a snapshot of the last run rather than of the current code, and when a resumed run has been through a few edits, publish to a fresh `--outdir`.

## Checking the outputs against the hand-run posts

Because the inputs are the same demo library, the pipeline should reproduce the earlier posts, and it does. The contaminant filter reports 999 phiX reads matched out of 1,000 (the k-mer filter runs on adapter-trimmed rather than quality-trimmed reads here, so the count differs from the 984 in the BBDuk post for the right reason: fewer reads had been discarded before it). BBMap reports 100% of read 1 and 99.9% of read 2 mapped, 19,703 mated pairs and a mean insert of 250.65, matching the BBMap post once the phiX is gone. BBMerge recovers the same two adapter sequences and merges 11,461 pairs, the exact count from the BBMerge post. A pipeline that reproduces your hand-run numbers is one you can hand to someone else.

## What I would add next

For a real project the additions are, in order: a `MULTIQC`-style summary step that collects every stats file into one report; `errorStrategy = 'retry'` with `maxRetries = 2` and memory that scales with `task.attempt`, so a job killed for memory resubmits itself larger; a `--help` block and parameter validation; and a test profile with the demo data so `nextflow run main.nf -profile test` proves the installation before real data go near it. None of that changes the five processes above, which is the point of writing them this way.

## Files

- [main.nf](/files/bbtools-nextflow/main.nf)
- [nextflow.config](/files/bbtools-nextflow/nextflow.config)
- [samplesheet.csv](/files/bbtools-nextflow/samplesheet.csv)
- [bbtools_demo_data.sh](/files/bbtools_demo_data.sh) makes the reads (put them in `data/`)

Run with Nextflow 26.04 or later and BBTools 40.02:

```bash
BB=/path/to/bbmap bash bbtools_demo_data.sh && mkdir -p data && mv raw_R?.fq.gz data/
cp /path/to/bbmap/resources/lambda.fa.gz .
nextflow run main.nf -profile standard
```

---

That is the BBTools series for now: an overview, one post each on BBDuk, BBMap, BBMerge, Reformat and Clumpify, and this pipeline. If there is a tool in the suite you would like the same treatment for, or a step here that does not work on your data, I would like to hear about it.
