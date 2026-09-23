---
title: 'Accuracy Is a Bad Way to Judge a Predictor'
date: 2026-09-30
permalink: /posts/2026/09/accuracy-improper-score/
tags:
  - statistics
  - machine-learning
  - model-evaluation
  - calibration
  - genomics
description: "Proportion classified correctly, sensitivity, and specificity are discontinuous improper scoring rules. They reward the wrong models and punish the right ones. Proper scoring rules and calibration are what you actually want."
---

> If your accuracy score can be improved by a model that is calibrated worse, the score is broken. Proportion classified correctly is exactly such a score. It is not a minor imperfection to note in the discussion section. It is a metric that will, given the chance, hand you the wrong model and a straight face.

In the [previous post](/posts/2026/09/classification-vs-prediction/) I argued that most genomics "classifiers" should be probability models. This post is about the other half of the same mistake: the way we grade them. Choosing the wrong method and choosing the wrong metric are usually the same error viewed from two angles, because the metric is what tells you the method worked. If the metric is improper, it will tell you the wrong method worked, and you will believe it.

## What "improper" actually means

A scoring rule takes a prediction and an observed outcome and returns a number telling you how good the prediction was. A rule is **proper** if it is optimized, in expectation, precisely when you report the true probabilities. It rewards honesty. The log score and the Brier score are proper: you cannot game them by shading your probabilities toward 0 or 1; the best you can do is report what you actually believe.

Proportion classified correctly, plain accuracy, is not proper. Neither are sensitivity and specificity taken as targets to optimize. These are discontinuous: they depend only on which side of a threshold a prediction falls, so a probability of 0.51 and a probability of 0.99 are treated as identical, and a shift from 0.49 to 0.51 is treated as an event even though nothing meaningful changed. A metric that is blind to the difference between 0.51 and 0.99 is throwing away most of what a good model knows. Worse, because it is discontinuous, it can be improved by making the model *worse*, by pushing probabilities around in ways that degrade calibration but flip a few borderline cases across the line. Harrell's worked example is worth reading: optimizing accuracy selects a model with the wrong predictors over the correct one. This is the ordinary behavior of these metrics.

## Why this bites hard in genomics

We work at extreme prevalences constantly. Pathogenic variants are rare. The interesting cell state is a small fraction of the sample. The regulatory element you care about is a needle in a genome of hay. Accuracy is at its most seductive and most useless exactly there.

Suppose you are calling a variant class that is truly present in 1 in 1,000 sites. The model that predicts "not present" everywhere achieves 99.9% accuracy. It is a completely useless model that has learned nothing, and by the metric that so many papers still lead with, it is nearly perfect. You cannot beat it on accuracy without taking on false positives, so a metric-chasing training process learns to say "no" more confidently. The accuracy goes up. The model gets worse. Everyone congratulates the pipeline.

Sensitivity and specificity are better than raw accuracy in that they at least separate the two error types, and as *descriptions* of a fixed decision rule they are fine. As *optimization targets* they still carry the discontinuity problem, and reporting a single sensitivity/specificity pair silently fixes a threshold, which, per the previous post, is not yours to fix. AUROC (the c-index) sidesteps the threshold by integrating over all of them, and it is a reasonable rank-based summary of discrimination. But discrimination is not the whole story, and AUROC is famously insensitive: two models with very different clinical usefulness can share an AUROC to three decimals. It tells you whether the model can order cases. It does not tell you whether the numbers it emits are true.

## Calibration is the property nobody reports and everybody needs

Here is the property I care about most and see reported least. A model is **calibrated** if, among all the cases where it says "probability 0.3," the outcome actually occurs about 30% of the time. Calibration is what makes a probability mean what it says. A model can have excellent AUROC and be badly miscalibrated, systematically overconfident, say, and a miscalibrated probability is a number that lies to the decision maker in exactly the way that classification was supposed to save us from.

You check calibration by plotting predicted probability against observed frequency, smoothed, and looking for departure from the diagonal. It is a five-minute plot and it is more informative than the entire table of accuracy, sensitivity, specificity, F1, and their friends. If I could make one change to how prediction models are reported in our field, it would be this: show me the calibration curve, and score the model with a proper rule. Then, if you must, show me discrimination.

## The F1 detour

F1 deserves a specific mention because it has become a reflex. It is the harmonic mean of precision and recall, it inherits the discontinuity of everything it is built from, it depends on prevalence in ways people rarely track across datasets, and it still requires a fixed threshold. It is popular because it produces a single number that feels balanced. A single number that is improper is not an improvement over several numbers that are improper. If the goal is one summary of a probability model, the Brier score is a better one, and it decomposes cleanly into calibration and refinement, which is to say it tells you *why* the model is good or bad rather than just asserting a grade.

## What I do now

I evaluate probability models with a proper scoring rule, usually the Brier score, decomposed, and the log score when I want to punish confident mistakes harder. I always draw the calibration curve, because it is the fastest way to catch a model that ranks well and lies about magnitudes. I report AUROC as a discrimination summary but never as the headline and never alone. I have stopped optimizing anything toward accuracy, sensitivity, specificity, or F1, because a training objective that rewards worse calibration will eventually give me a worse model and a better number. In this field those two things go together far more often than we admit.

## Resources

- Frank Harrell, [Damage Caused by Classification Accuracy and Other Discontinuous Improper Accuracy Scoring Rules](https://www.fharrell.com/post/class-damage/).
- Frank Harrell, [Classification vs. Prediction](https://www.fharrell.com/post/classification/).
- Van Calster, McLernon, van Smeden, Wynants, Steyerberg, [Calibration: the Achilles heel of predictive analytics](https://doi.org/10.1186/s12916-019-1466-7), *BMC Medicine* 2019;17:230.

---

Next in this series: why "balancing" your classes with SMOTE, undersampling, and the rest usually makes your probabilities worse. As always, corrections and counterarguments welcome.
