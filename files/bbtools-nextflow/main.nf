#!/usr/bin/env nextflow
// BBTools preprocessing pipeline: adapter trimming, phiX removal, quality
// trimming + mapping, and read merging. Companion to the BBTools posts at
// clstacy.github.io. Nextflow DSL2.

nextflow.enable.dsl = 2

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

process CONTAMINANT_FILTER {
    tag "$sample"
    publishDir { "${params.outdir}/${sample}/contaminant_filter" }, mode: 'copy', pattern: '*.txt'

    input:
    tuple val(sample), path(r1), path(r2)

    output:
    tuple val(sample), path("${sample}_clean_R1.fq.gz"), path("${sample}_clean_R2.fq.gz"), emit: reads
    path "${sample}_contaminants.txt"

    script:
    """
    bbduk.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} \\
        in=$r1 in2=$r2 \\
        out=${sample}_clean_R1.fq.gz out2=${sample}_clean_R2.fq.gz \\
        ref=${params.contaminant} k=31 hdist=1 \\
        stats=${sample}_contaminants.txt
    """
}

process QUALITY_TRIM {
    tag "$sample"

    input:
    tuple val(sample), path(r1), path(r2)

    output:
    tuple val(sample), path("${sample}_qtrim_R1.fq.gz"), path("${sample}_qtrim_R2.fq.gz")

    script:
    """
    bbduk.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} \\
        in=$r1 in2=$r2 \\
        out=${sample}_qtrim_R1.fq.gz out2=${sample}_qtrim_R2.fq.gz \\
        qtrim=r trimq=20 minlen=50
    """
}

process MAP {
    tag "$sample"
    publishDir { "${params.outdir}/${sample}/map" }, mode: 'copy'

    input:
    tuple val(sample), path(r1), path(r2)
    path reference

    output:
    path "${sample}.bam"
    path "${sample}_covstats.txt"
    path "${sample}_ihist.txt"
    path "${sample}_mapstats.txt"

    script:
    """
    bbmap.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} nodisk \\
        ref=$reference in=$r1 in2=$r2 \\
        out=${sample}.bam \\
        covstats=${sample}_covstats.txt ihist=${sample}_ihist.txt \\
        statsfile=${sample}_mapstats.txt
    """
}

process MERGE {
    tag "$sample"
    publishDir { "${params.outdir}/${sample}/merge" }, mode: 'copy'

    input:
    tuple val(sample), path(r1), path(r2)

    output:
    path "${sample}_merged.fq.gz"
    path "${sample}_unmerged_R{1,2}.fq.gz"
    path "${sample}_merge_ihist.txt"
    path "${sample}_adapters.fa"

    script:
    """
    bbmerge.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} \\
        in=$r1 in2=$r2 outa=${sample}_adapters.fa
    bbmerge.sh -Xmx${task.memory.toGiga()}g t=${task.cpus} \\
        in=$r1 in2=$r2 \\
        out=${sample}_merged.fq.gz \\
        outu=${sample}_unmerged_R1.fq.gz outu2=${sample}_unmerged_R2.fq.gz \\
        ihist=${sample}_merge_ihist.txt adapters=${sample}_adapters.fa
    """
}

workflow {
    reads = Channel.fromPath(params.samplesheet)
        .splitCsv(header: true)
        .map { row -> tuple(row.sample, file(row.fastq_1), file(row.fastq_2)) }

    ADAPTER_TRIM(reads)
    CONTAMINANT_FILTER(ADAPTER_TRIM.out.reads)

    // mapping branch: quality-trim first
    QUALITY_TRIM(CONTAMINANT_FILTER.out.reads)
    MAP(QUALITY_TRIM.out, file(params.reference))

    // merging branch: adapter-trimmed only, no quality trimming
    MERGE(CONTAMINANT_FILTER.out.reads)
}
