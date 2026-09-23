---
title: 'You Probably Shouldn''t Balance Your Classes'
date: 2026-10-07
permalink: /posts/2026/10/stop-balancing-classes/
tags:
  - statistics
  - machine-learning
  - class-imbalance
  - calibration
  - genomics
description: "SMOTE, undersampling, and oversampling are standard responses to rare outcomes. For probability models they are usually a mistake. They corrupt calibration to fix a problem that was never really there."
---

> Class imbalance is not a disease of your data. It is a fact about the world: the outcome you care about is rare. "Correcting" it by throwing away controls or synthesizing cases does not make your model better. It makes your probabilities wrong, and then you have to do more work to make them wrong in the opposite direction.

This is the third post in a series on classification and prediction in genomics. The [first](/posts/2026/09/classification-vs-prediction/) argued that most of our classifiers should be probability models. The [second](/posts/2026/09/accuracy-improper-score/) argued that accuracy is a broken way to grade them. This one is about a practice that follows almost inevitably from getting those two things wrong: rebalancing the data. If you have accepted that you are building a classifier and grading it on accuracy, then imbalance really is a problem for you, and rebalancing really does "help." Both of those are symptoms. Fix the framing and the imbalance problem largely dissolves.

## Why imbalance looks like a problem

The reasoning goes like this. My outcome occurs in 1 of 1,000 cases. A classifier trained on that data learns to say "no" almost always, because saying "no" is right 99.9% of the time. So I balance the data, by undersampling the majority, oversampling the minority, or synthesizing new minority cases with SMOTE, until the classes are roughly equal, and now the classifier "pays attention" to the rare class.

Every step of that is downstream of two prior choices: building a classifier instead of a probability model, and judging it by accuracy. A probability model does not have this problem. Logistic regression fit to data with 1/1,000 prevalence will happily estimate small probabilities, and small probabilities are the *correct answer* when the outcome is rare. There is nothing to fix. The model saying "about 0.001 for most cases" is not a model that is failing to pay attention. It is a model telling you the truth about a rare event.

## What rebalancing actually does to you

When you resample to a prevalence your data does not have, you change the thing the model estimates. Train logistic regression on data you have undersampled to 1:1, and its intercept now reflects 50% prevalence instead of 0.1%. Every probability it emits is inflated, often by more than an order of magnitude. The model will tell you a case has a 40% chance of the outcome when the truth, at real-world prevalence, is nearer 1%. The ranking of cases may survive, so your AUROC looks fine and you conclude all is well, but the numbers are now systematically, badly miscalibrated. You have taken a model that produced correct probabilities and taught it to produce wrong ones.

Then, because the probabilities are obviously too high, the literature has produced a second layer of methods to "correct" the intercept back toward the true prevalence after resampling. So the workflow is: distort the data to fix a problem you created by choosing the wrong model and metric, then distort the model back to undo the distortion. Or you could recalibrate the intercept of a model fit to the untouched data, once, and skip both steps. As Harrell dryly observes, users of regression models would never exclude good data to get an answer.

SMOTE deserves its own line. It manufactures synthetic minority cases by interpolating between real ones in feature space. In genomics, where features are high-dimensional, correlated, and structured (expression vectors, variant contexts, chromatin signals), interpolating between two real cases can produce a point that corresponds to no biology at all. You are training on fabricated data drawn from the convex hull of your minority class, and then reporting performance as though it reflected reality. At best it does nothing once you account for the resulting miscalibration. Often it does harm.

## The evidence, not just the argument

This has been studied directly. van den Goorbergh and colleagues simulated exactly this setup with logistic regression and found that random undersampling, random oversampling, and SMOTE all yielded poorly calibrated models that strongly overestimated the probability of the minority class, with no improvement in AUROC relative to simply fitting the model on the real data. Their conclusion is that outcome imbalance is not a problem in itself, and that correcting it may worsen model performance. If your goal is a probability you can act on, the correction is a net negative.

## When resampling is defensible

I try not to be absolutist, because there are narrow cases. If you are in the genuinely high-signal, near-deterministic regime where classification is the right tool (see the first post), and you face a pure computational constraint because the majority class is so large you cannot fit it in memory or in reasonable time, then undersampling the majority as a *sampling* strategy, with the intercept correction applied afterward, is a reasonable engineering compromise. That is a computational decision, made with your eyes open. It is not a statistical improvement, and the distinction matters: you are trading a known bias you will correct for a tractable computation.

## What I do now

I fit the model to the data I actually have, at the prevalence it actually has. I use a probability model, not a classifier, for anything stochastic. I check calibration first, because that is where resampling damage shows up and where its absence is reassuring. If prevalence differs between my training data and my deployment population, which is common because case-control designs oversample cases by construction, I recalibrate the intercept to the target prevalence, a one-parameter fix with a clean justification. I keep every control. Discarding real observations to make a metric look better is the kind of thing that feels like rigor and is closer to the opposite.

## Resources

- van den Goorbergh, van Smeden, Timmerman, Van Calster, [The harm of class imbalance corrections for risk prediction models: illustration and simulation using logistic regression](https://doi.org/10.1093/jamia/ocac093), *JAMIA* 2022;29(9):1525–1534.
- Frank Harrell, [Classification vs. Prediction](https://www.fharrell.com/post/classification/). The source of the "would never exclude good data" line.
- Van Calster, McLernon, van Smeden, Wynants, Steyerberg, [Calibration: the Achilles heel of predictive analytics](https://doi.org/10.1186/s12916-019-1466-7), *BMC Medicine* 2019;17:230.

---

That is the core of the argument on classification versus prediction: build a probability model, score it properly, and leave the data at its real prevalence. The next few posts turn to neighboring habits that cause the same kind of damage, starting with the median split. Comments and disagreements welcome.
