---
title: 'Your Gene Signature Probably Won''t Replicate'
date: 2026-10-21
permalink: /posts/2026/10/gene-signature-instability/
tags:
  - statistics
  - machine-learning
  - feature-selection
  - genomics
  - reproducibility
description: "The list of 'top genes' that separates your groups is far less stable than it looks. Selecting features from thousands of candidates on a few hundred samples produces signatures that are mostly interchangeable with other signatures that would have worked just as well."
---

> Take the same data, resample the patients, and rerun your selection. If the gene list comes back different every time, and it will, then the specific genes were never the finding. The finding was that many genes carry a little signal and your procedure picked some of them.

Here is an experiment worth running on your own data before you name a signature after it. Draw a bootstrap sample of your patients, run your entire feature-selection pipeline, and record which genes come out. Do it a hundred times. Then look at how often any given gene appears. In most omics settings the answer is sobering: the "top" genes are wildly unstable across resamples, and two runs on nearly identical data can share almost none of their selected features. The signature you published was one draw from a lottery with thousands of nearly equivalent tickets. I have watched this happen to lists I was proud of, and it is the single most useful diagnostic I know for keeping myself honest.

## Why the instability is structural

The problem is the shape of the data. We select a handful of features from tens of thousands of candidates using a few hundred samples, the classic p ≫ n regime. In that regime, many genes are correlated with each other and each carries a small, noisy association with the outcome. When many weak, correlated predictors compete for a few slots, which ones win is decided by sampling noise. Swap a few patients and a different but equally plausible set wins. This is not a failure of the algorithm; it is what the algorithm is being asked to do, and no amount of cross-validation on the *same* cohort reveals it, because cross-validation reuses the same patients and inherits the same accidents.

Ein-Dor and colleagues made this concrete for breast-cancer outcome prediction. Reanalyzing the van 't Veer data with the original selection method, they showed that the resulting gene set is not unique, that it is strongly influenced by which patients are used for selection, and that many equally predictive lists could have been produced from the same analysis. The explanation was exactly the structure above: many genes are correlated with survival, the differences between those correlations are small, and the correlations fluctuate strongly across subsets of patients. In a follow-up they estimated how many patients would be needed for two independent studies to agree on even half of their genes, and for breast cancer the answer was several thousand, orders of magnitude more than the studies had. Michiels and colleagues, reanalyzing the seven largest cancer-microarray prognosis studies with repeated random splits, found that the identified gene lists were highly unstable and depended strongly on which patients fell in the training set, that the original single-split reports were overoptimistic, and that five of the seven studies did not classify patients better than chance. Neither result is a story about sloppy labs. Both are stories about what selection does when candidates are many and samples are few.

## The signature is not the biology

The deepest confusion here is treating the selected list as a discovery about mechanism. If ten different gene sets predict the outcome comparably, then no one of them is *the* biological signature; they are ten samples from a large correlated pool of genes that co-vary with the phenotype. Reifying the particular list your pipeline emitted, building a story about those specific genes, and designing follow-up around them is chasing an artifact of your sampling. The genes may all be downstream of the same real process, which is interesting, but that is an argument for studying the process rather than canonizing one interchangeable list.

This matters commercially and clinically too, because a signature that doesn't replicate doesn't transport. Ship the exact gene list to a new lab, a new platform, a new cohort, and the performance that justified it erodes. The assay was not run badly. The list was overfit to the correlation structure of the original patients.

## What actually helps

The instability has real remedies, and none of them is "select harder."

**Shrink instead of selecting.** If the goal is prediction, a penalized model that shrinks all the coefficients (ridge, or an elastic net when you want some sparsity with less instability than the lasso alone) will usually predict better than a hard "pick the top k genes" filter, precisely because it declines to bet everything on which correlated feature won this draw. Shrinkage spreads the signal across the correlated set instead of gambling on one representative.

**Measure the stability and report it.** Bootstrap the whole pipeline, report selection frequencies, and be honest that a gene appearing in 30% of resamples is not a robust marker. If you must present a list, present it with its instability attached rather than as a clean top-20 table that implies a solidity it does not have.

**Respect the sample-size arithmetic.** If robust selection genuinely needs far more samples than you have, and in outcome prediction it usually does, then the appropriate output is a well-calibrated predictive model and an honest statement of uncertainty rather than a definitive gene list the data cannot support. Sometimes the correct finding is "these data can predict moderately well but cannot identify which genes are responsible," and saying so is more valuable than manufacturing false specificity.

## What I do now

Before I describe any selected feature set as a finding, I bootstrap the selection and look at how often each feature survives. If the list is unstable, and it almost always is, I say so, and I shift the claim from "these genes" to "a predictive signal exists in this pathway or region," which is what the data actually support. For prediction I default to penalized regression over hard feature selection, because shrinkage handles correlated weak predictors more gracefully than a top-k filter and doesn't pretend the losers carry no signal. I treat any single-split estimate of a signature's accuracy as optimistic until repeated resampling says otherwise. When someone asks for the gene list, I give it to them with selection frequencies attached, because a list without its stability is a headline without its error bars.

## Resources

- Ein-Dor, Kela, Getz, Givol, Domany, [Outcome signature genes in breast cancer: is there a unique set?](https://doi.org/10.1093/bioinformatics/bth469), *Bioinformatics* 2005;21(2):171–178.
- Ein-Dor, Zuk, Domany, [Thousands of samples are needed to generate a robust gene list for predicting outcome in cancer](https://doi.org/10.1073/pnas.0601231103), *PNAS* 2006;103(15):5923–5928.
- Michiels, Koscielny, Hill, [Prediction of cancer outcome with microarrays: a multiple random validation strategy](https://doi.org/10.1016/S0140-6736(05)17866-0), *The Lancet* 2005;365(9458):488–492.
- Frank Harrell, [Regression Modeling Strategies](https://hbiostat.org/rmsc/). On the instability of stepwise and data-driven variable selection, and shrinkage as the alternative.

---

Next: the arithmetic underneath all of this. How many outcome events you actually need per candidate predictor before a model means anything, and why high-dimensional omics violates that budget by factors of thousands. Disagreements welcome.
