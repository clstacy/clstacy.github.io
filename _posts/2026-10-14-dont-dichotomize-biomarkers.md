---
title: 'Don''t Cut Your Continuous Biomarker in Half'
date: 2026-10-14
permalink: /posts/2026/10/dont-dichotomize-biomarkers/
tags:
  - statistics
  - biomarkers
  - dichotomization
  - model-evaluation
  - genomics
description: "'High vs. low' expression, median splits, and data-driven optimal cutpoints throw away information you paid to collect and manufacture bias you can't see. A continuous predictor should almost always stay continuous."
---

> A median split takes a variable that distinguishes a thousand shades of signal and reduces it to a coin that only knows heads from tails. We would never dilute a reagent tenfold to save pipetting. We do the analytic equivalent constantly, and we call it interpretability.

The last three posts were about classifiers, scoring rules, and class balance. This one is about a neighboring habit that comes up so often in omics work that I want it written down: dichotomizing continuous predictors, turning a real-valued measurement into "high" and "low," usually at the median, sometimes at a cutpoint the data handed us. It is one of the most common analytic moves in the field and one of the most quietly damaging. I did it for years because it made the story simple. It made the story simple by deleting most of the evidence.

## What you throw away

A continuous biomarker, whether a normalized expression value, a methylation beta, a polygenic score, or a protein abundance, carries information across its entire range. A sample at the 95th percentile and a sample at the 55th percentile are both "high" after a median split, and the model is then forbidden from knowing they differ. But they do differ, often by more than the "high" and "low" groups differ from each other on average. Cohen worked out the cost in 1983: under bivariate normality, dichotomizing a predictor at its mean reduces the variance explained by about a third, equivalent to discarding roughly 38% of the sample. Altman and Royston put the same figure in front of clinical readers two decades later, and the loss grows when the cut is placed away from the middle of the distribution. The exact figure depends on the shape of the relationship, but the direction never changes: you always lose, and you lose most when the predictor is most informative.

The tell is that the loss is invisible in the output. The dichotomized analysis runs fine, produces a clean odds ratio for "high versus low," and reports a confidence interval that looks perfectly respectable. Nothing in the result announces that the interval is wider and the estimate noisier than it needed to be. You have paid for a high-resolution measurement and then reported it at one bit of resolution, and the software will not warn you, because from its perspective you simply asked a different question.

## The optimal-cutpoint trap

The worse version is choosing the cutpoint by looking at the outcome. You scan candidate thresholds, pick the one that maximizes separation (the smallest p-value, the biggest hazard ratio) and report that as *the* cutpoint for high versus low expression. This feels like rigor. It is the opposite. Searching over cutpoints and keeping the best one is multiple testing that you then fail to account for, and it biases the effect estimate away from the null essentially every time. Altman, Lausen, Sauerbrei, and Schumacher showed in 1994 that the resulting p-values are spuriously small and the effect sizes overestimated, and Royston, Altman, and Sauerbrei restated the case a decade later: a data-derived "optimal" cutpoint leads to serious bias. The threshold will not replicate in the next cohort, because it is an artifact of the noise in the sample you happened to draw. The practice is still everywhere in biomarker papers, usually presented as a discovery rather than a distortion.

There is a seductive figure that comes with it: the Kaplan-Meier curve with two cleanly separated arms, split at the optimal cut. It looks like strong evidence. It is partly a picture of the cutpoint search finding the widest gap in this particular dataset. The gap shrinks, sometimes to nothing, when someone applies the same threshold to new data.

## "But the clinic needs a cutoff"

This is the honest objection, and it deserves the same answer I gave for classification generally: the need for a threshold at the point of decision does not justify building the threshold into the analysis. If a continuous marker genuinely relates to outcome, model it continuously, estimate the relationship as smoothly as the data allow, and *then*, if a clinical workflow requires a binary call, choose the operating cutpoint using the utilities of that specific decision. The cutpoint is a deployment choice made with costs in hand rather than an analysis choice made by p-value. Estimating the curve first also tells you something a split never can: whether the relationship is linear, whether it flattens, and whether there is a genuine threshold effect in the biology rather than one you imposed with a knife.

Often there is no threshold in the biology at all. Risk rises steadily with the marker. Forcing a step function onto a smooth relationship misrepresents it, and it hides the fact that a patient just above the cut and a patient just below it are nearly identical.

## Modeling it continuously is not hard

The reflex defense of dichotomization is that the alternative is complicated. It is not. A continuous predictor enters a regression as a continuous term. If you are worried about nonlinearity, a restricted cubic spline with three or four knots captures a smooth curve without you specifying its shape in advance, costs only a couple of degrees of freedom, and gives you a plot of estimated risk across the whole range of the marker, which is far more informative than two boxes. You keep the power you paid for, you get an interpretable dose-response picture, and you avoid manufacturing a cutpoint that won't survive contact with the next dataset. Once you stop counting the cutpoint search's false convenience as free, the continuous analysis is less work.

## What I do now

I keep continuous predictors continuous. I never split at the median, and I never let the outcome choose a cutpoint. When I suspect nonlinearity I fit a spline and look at the estimated curve rather than guessing at a threshold. If a downstream decision truly needs a binary flag, I estimate the continuous relationship first and set the operating point at the end, using the costs of the actual decision, and I report it as an operating choice rather than a property of the marker. When a reviewer asks for a "high versus low" table, I provide the continuous model and, if pressed, a split at a pre-specified clinically meaningful value, never a data-derived optimum, with a note that the split is for display and the model is the analysis. It has cost me a few simple-looking figures. It has never cost me a result I later had to walk back.

## Resources

- Cohen, [The cost of dichotomization](https://doi.org/10.1177/014662168300700301), *Applied Psychological Measurement* 1983;7(3):249–253.
- Altman, Royston, [The cost of dichotomising continuous variables](https://doi.org/10.1136/bmj.332.7549.1080), *BMJ* 2006;332:1080.
- Altman, Lausen, Sauerbrei, Schumacher, [Dangers of using "optimal" cutpoints in the evaluation of prognostic factors](https://doi.org/10.1093/jnci/86.11.829), *JNCI* 1994;86(11):829–835.
- Royston, Altman, Sauerbrei, [Dichotomizing continuous predictors in multiple regression: a bad idea](https://doi.org/10.1002/sim.2331), *Statistics in Medicine* 2006;25(1):127–141.
- Frank Harrell, [Statistical Errors in the Medical Literature](https://www.fharrell.com/post/errmed/). See the section on "dichotomania."

---

Next in this series: why the gene signature that looked so convincing in the training cohort probably won't replicate, and why that is a predictable consequence of how it was selected rather than bad luck. Corrections and counterarguments welcome, as always.
