---
title: 'One Test Set Is Not Validation'
date: 2026-11-04
permalink: /posts/2026/11/one-test-set-is-not-validation/
tags:
  - statistics
  - machine-learning
  - validation
  - model-evaluation
  - genomics
description: "A single train/test split is the ritual we treat as the gold standard of honest evaluation. In the p >> n world it is one of the noisiest and most wasteful things you can do. The bootstrap estimates optimism better and keeps all your data."
---

> A held-out test set answers one question: how did this model do on these particular held-out patients? You wanted a different answer, how it will do on the next patients, and a single split estimates that with a sample size of one experiment, run on the data you could least afford to set aside.

We have trained a generation of analysts to believe that splitting the data into training and test sets is what makes an evaluation honest. It is certainly better than reporting the fit on the training data. But treated as *the* validation method, especially in small high-dimensional studies, the single split is statistically wasteful, high-variance, and quietly gameable, and there is a better default that has been sitting in the biostatistics literature for decades. This is the last post in this run, and it is the one I most wish someone had made me sit through early.

## The single split is high-variance

Here is the uncomfortable demonstration. Take your data, split it 70/30, train, and record the test performance. Now do it again with a different random split. And again. In a study with a few hundred samples, those numbers bounce around alarmingly; with a few dozen events in the test set, an AUC can easily move by a tenth of a point depending only on which patients landed there. So which split is the "real" performance? None of them. Each is one noisy draw. By reporting a single split you have picked one of these draws, often, if we are honest, after peeking at a few, and presented its number as the answer, when the honest answer is a distribution you chose not to look at.

The variance is worst exactly where we live: small n, large p, rare events. You need the test set to be big enough to estimate performance precisely, and you need the training set to be big enough to fit a decent model, and in a small study you cannot have both. Every patient in the test set is a patient the model didn't learn from, and every patient in the training set is one the estimate didn't get to use. The single split forces a lose-lose allocation of a resource you don't have enough of.

## The bootstrap uses everything and estimates the right thing

The alternative is the optimism-corrected bootstrap, and its logic is worth internalizing because it is cleverer than it first looks. Fit the model on the full dataset, all of it, no holdout. Then, to estimate how optimistic that apparent performance is, draw a bootstrap sample, refit the entire modeling procedure on it, and measure how much better the model does on its own bootstrap sample than on the original data. That gap is an estimate of optimism, the amount by which in-sample performance flatters the model. Average it over a couple hundred bootstraps and subtract it from the apparent performance. You get an honest, low-variance estimate of how the model will perform on new data, and you never had to throw a single patient into a holdout.

Steyerberg, Harrell, and colleagues compared these procedures head to head on samples drawn from a large trial at 5 to 80 events per variable. Split-sample validation gave overly pessimistic estimates with large variability; bootstrapping gave stable estimates with low bias. Their conclusion was that split-sample validation is inefficient, and they recommended the bootstrap for internal validation of logistic regression models. The bootstrap won because it uses all the data for both fitting and honest assessment, while the single split spends half its information proving a point about the other half.

## The word "entire" is doing all the work

There is one way to turn any validation scheme, whether bootstrap, cross-validation, or a clean test set, into a lie, and it is the most common mistake in the field: freezing part of the pipeline before validating. If you select features, tune a threshold, or standardize using the whole dataset and *then* validate only the final model, you have already leaked the outcome, and every downstream estimate inherits that leak no matter how principled the resampling looks afterward. The rule is absolute: whatever the procedure looked at the outcome to decide, it must be redone inside every bootstrap or every fold. Feature selection is part of the model. Threshold tuning is part of the model. If it consulted y, it gets resampled. Validation only measures the pipeline you actually resample; the parts you froze outside are being reported at their optimistic, in-sample value.

## When you do want a separate test set

I am not against holding out data on principle, and there is a case where it is exactly right: external validation. A test set drawn from a *different* cohort, another hospital, another platform, another time period, tests something the bootstrap cannot, which is transportability. That is the real gold standard, and it answers the question that actually predicts field performance: does this model survive the shift from where it was built to where it will be used? A random split of a single cohort does not test that; it tests the model against more of the same, and then congratulates it for passing. If you have the luxury of a genuinely independent cohort, use it for external validation. If all you have is one dataset, resample it honestly rather than amputating a piece and calling the stump rigor.

## What I do now

For internal validation I use the optimism-corrected bootstrap, a couple hundred resamples, with the entire modeling pipeline (selection, tuning, any preprocessing that touches the outcome) refit inside every one. I do not do single 70/30 splits, because they waste data I don't have and report a number with more variance than I'm admitting. I reserve held-out data for genuine external validation, from a different cohort, where it tests transportability rather than repetition. Whatever the scheme, I check calibration on the validated predictions and not just discrimination, because a model can survive validation on its ranking and still lie about its probabilities, which is where this whole series began.

## Resources

- Steyerberg, Harrell, Borsboom, Eijkemans, Vergouwe, Habbema, [Internal validation of predictive models: efficiency of some procedures for logistic regression analysis](https://doi.org/10.1016/S0895-4356(01)00341-9), *Journal of Clinical Epidemiology* 2001;54(8):774–781.
- Frank Harrell, [Regression Modeling Strategies](https://hbiostat.org/rmsc/). On optimism, the bootstrap, and validating the whole modeling process.
- Steyerberg, [Clinical Prediction Models](https://doi.org/10.1007/978-3-030-16399-0), 2nd ed., Springer 2019. Book-length treatment of internal and external validation.

---

That closes this run on classification and prediction in genomics: thresholds, scoring rules, class balance, dichotomization, signature stability, sample-size arithmetic, and validation. If there's appetite, I'll turn it into the worked, end-to-end example I keep promising. Corrections, counterarguments, and better references always welcome.
