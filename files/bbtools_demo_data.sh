#!/usr/bin/env bash
# Demo data for the BBTools posts at clstacy.github.io
# Simulates a lambda-phage paired-end library with TruSeq adapters and a phiX
# spike-in. Everything used here ships with BBTools (https://bbmap.org).
#
# Usage:  BB=/path/to/bbmap ./bbtools_demo_data.sh
#         (BB is the directory containing bbduk.sh and the resources/ folder)
set -euo pipefail
BB=${BB:?Set BB to your BBTools install directory}
export PATH="$BB:$PATH"

cp "$BB/resources/lambda.fa.gz" lambda.fa.gz
cp "$BB/resources/phix174_ill.ref.fa.gz" phix.fa.gz

# 20,000 lambda pairs, 2x150 bp, flat insert distribution 100-400 bp.
# fragadapter/fragadapter2 are the TruSeq indexed adapter (read 1) and the
# reverse complement of the TruSeq universal adapter (read 2); randomreads
# appends them whenever the insert is shorter than the read.
randomreads.sh ref=lambda.fa.gz out=lambda_R1.fq out2=lambda_R2.fq \
  reads=20000 length=150 paired=t mininsert=100 maxinsert=400 flat=t \
  minq=18 midq=30 maxq=36 qv=6 illuminanames=t prefix=lambda seed=42 \
  fragadapter=AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATCACGATCTCGTATGCCGTCTTCTGCTTG \
  fragadapter2=AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT

# 500 phiX pairs as "contamination"
randomreads.sh ref=phix.fa.gz out=phix_R1.fq out2=phix_R2.fq \
  reads=500 length=150 paired=t mininsert=150 maxinsert=400 flat=t \
  minq=18 midq=30 maxq=36 qv=6 illuminanames=t prefix=phix seed=7

cat lambda_R1.fq phix_R1.fq | gzip > raw_R1.fq.gz
cat lambda_R2.fq phix_R2.fq | gzip > raw_R2.fq.gz
rm lambda_R?.fq phix_R?.fq
echo "Wrote raw_R1.fq.gz and raw_R2.fq.gz (20,500 pairs)"
