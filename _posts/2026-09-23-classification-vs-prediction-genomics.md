---
title: 'Your Classifier Is Answering the Wrong Question'
date: 2026-09-23
permalink: /posts/2026/09/classification-vs-prediction/
tags:
  - statistics
  - machine-learning
  - classification
  - prediction
  - genomics
description: "Most of the time we reach for a classifier in genomics, what we actually want is a probability. Classification bundles prediction and decision-making into a single premature step, and the bundle usually costs us."
---

> A classifier forces a choice. A probability model quantifies a tendency and hands the choice back to whoever is actually equipped to make it. In most of the problems I work on, the second thing is what I want, and the first thing is what I built by accident.

Here is a claim I have come to hold strongly: the majority of the "classifiers" built in computational biology should not be classifiers at all. They should be probability models, and the classification step, if it is needed at all, belongs at the point of decision rather than in the analysis. I did not always believe this. I built classifiers for years without noticing that I had quietly made a decision on behalf of every downstream user of my model, and that I had no right to.

The distinction is easy to state and easy to lose track of. **Prediction** is the estimation of a tendency: given what I know about this sample, this variant, this cell, what is the probability of the outcome? **Classification** is a decision: I will call this a positive. A classifier bundles the two together. It takes the probability (which it computed internally, whether or not it shows it to you) and applies a threshold, and the threshold encodes a cost tradeoff that you almost certainly did not specify and that your users do not share.

## The threshold is not yours to set

Consider a model that flags tumor samples as likely to harbor a particular actionable mutation from expression data. If I ship a classifier, I have baked in a single answer to the question "how bad is a false positive relative to a false negative?" That ratio is not a property of the model. It is a property of the situation the model is used in. A screening context where a positive triggers a cheap confirmatory assay tolerates false positives happily. A context where a positive sends a patient toward an invasive procedure does not. Same model, opposite thresholds. If I hand over a probability, both users are served. If I hand over a class label, I have served neither of them and pretended to serve both.

This is Frank Harrell's point, made repeatedly and more elegantly than I will manage here, and it took me embarrassingly long to absorb: classification "usurps the decision maker in specifying costs of wrong decisions." The person who knows the utilities is the clinician, the assay designer, or the person allocating a fixed sequencing budget. It is never the person who trained the model on data collected before any of those constraints were known.

## "But I need a yes or no at the end"

The most common objection I hear is that the pipeline has to emit a decision eventually, so it may as well emit one now. This does not follow. A great many decisions in genomics are revocable or sequential. You do not commit to a diagnosis on the basis of one model output; you order another assay, you increase sequencing depth, you flag the sample for manual review, you wait for more data. The best action when a probability sits at 0.45 is very often "get more information," and a classifier cannot express that. It has exactly two things it can say, and "I don't know yet" is not one of them.

When a hard call genuinely must be made, it should be made when the costs are known, which is at the point of use. A probability of 0.1 carries its own error rate: if you decline to act and the truth is positive, you were wrong with probability 0.1, by definition. Probabilities are their own uncertainty measure. A class label throws that away and replaces it with false confidence.

## Where classification actually belongs

I want to be fair to classification, because there are situations where it is exactly right, and pretending otherwise is how you lose the argument. Classification is appropriate when the signal-to-noise ratio is very high and the outcome is effectively deterministic, so that two inputs that look identical will essentially always give the same answer. Base calling from raw signal is like this. Assigning a read to a barcode is like this. A great deal of sequence-level pattern matching is like this: there is a right answer, replicates agree, and nobody needs a credible interval on whether a read contains a given adapter k-mer.

The trouble starts when we take methods built for that regime and apply them to problems soaked in biological variation, where two patients, or two cells, or two tumors, with identical measured features routinely have different outcomes. Prognosis is not base calling. Treatment response is not barcode assignment. Applying a forced-choice classifier to a stochastic outcome is a category error, and no amount of cross-validation will save you from it, because you are estimating the wrong quantity well.

## The tell: people call logistic regression a "classifier"

You can see how deep the confusion runs in the vocabulary. Logistic regression is a probability model. It estimates the probability of an outcome as a smooth function of predictors, and it is one of the best tools we have for exactly the stochastic, additive, modestly sized problems that dominate genomics. Yet it is routinely filed under "classification algorithms" alongside random forests and support vector machines, as though its purpose were to emit a label. If you are thresholding the output of a logistic model to report accuracy, you have taken a probability model and thrown away the thing that made it useful.

There is also a practical payoff to modeling probabilities that gets overlooked. Regression models that exploit additivity, which holds approximately far more often than people expect, can produce well-calibrated probabilities on the modest datasets we usually have, without the enormous sample sizes that flexible classifiers demand. When the outcome has more than two levels, or is a survival time, a single probability model gives you means, quantiles, exceedance probabilities, and hazards from one fit. A classifier gives you a label.

## What I do now

When I catch myself about to build a classifier, I ask one question: is this outcome deterministic given the inputs, or is there real biological variation between identical-looking cases? If it is deterministic and high signal-to-noise, fine, classify. If there is genuine variation, I build a probability model, I check its calibration, and I stop there. I let the person who owns the decision own the threshold. My job is to estimate the tendency as honestly as I can. Their job is to decide what to do about it, and they know things I don't.

## Resources

- Frank Harrell, [Classification vs. Prediction](https://www.fharrell.com/post/classification/). The essay that reorganized how I think about this.
- Frank Harrell, [Damage Caused by Classification Accuracy and Other Discontinuous Improper Accuracy Scoring Rules](https://www.fharrell.com/post/class-damage/). The companion argument about why the metric matters as much as the method.
- van den Goorbergh, van Smeden, Timmerman, Van Calster, [The harm of class imbalance corrections for risk prediction models](https://doi.org/10.1093/jamia/ocac093), *JAMIA* 2022;29(9):1525–1534.

---

This is the first of a series of posts working through the classification-versus-prediction problem as it shows up in genomics. Next I want to take on the metric itself: why "accuracy" is a worse way to judge a predictor than almost everyone assumes. If you think I've got something wrong here, I'd like to hear it.
