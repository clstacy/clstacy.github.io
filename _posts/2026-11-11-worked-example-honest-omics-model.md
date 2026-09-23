---
title: 'A Worked Example: 286 Tumours, 22,000 Genes, 69 Events, and an Honest Answer'
date: 2026-11-11
permalink: /posts/2026/11/worked-example-honest-omics-model/
tags:
  - statistics
  - machine-learning
  - genomics
  - validation
  - calibration
  - tutorial
description: "The classification-versus-prediction series, applied to a real public dataset from raw expression matrix to a validated probability model, with the shortcuts run alongside so you can see what each one costs. Including the place where my own recommended method failed."
---

> On this dataset the popular pipeline reports an AUC of 0.89. The honest number is 0.59, and the model's probabilities are so overfit that it predicts worse than saying "24%" to everyone. A penalised model on all the genes reaches 0.71 and is calibrated. And the bootstrap I recommended in the last post got the wrong answer.

The seven posts in the [classification versus prediction series](/posts/2026/09/classification-vs-prediction/) each argued one point. This post runs all of them on one public dataset, end to end, with code you can execute. It also does the thing the series kept asking for: it looks for the version of the analysis where the recommended method breaks. It found one.

## The data

[GSE2034](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE2034) is the Wang et al. (2005) breast cancer cohort: 286 lymph-node-negative patients profiled on Affymetrix HG-U133A arrays. It is one of the seven studies Michiels and colleagues reanalysed when they showed that published microarray signatures were unstable, so it is a fitting place to see whether the lessons hold. The GEO record carries one clinical field, bone relapse, which 69 of the 286 patients had. That is the outcome here; the paper's own endpoint (distant metastasis) needs the clinical table from the supplement, and I wanted everything reproducible from GEO alone.

The arithmetic from the [events-per-variable post](/posts/2026/10/events-per-variable-omics/) comes first, because it frames everything after. 69 events. 22,215 probes after dropping the control probes. Events per candidate predictor: 0.003. An outcome-blind variance filter to the 5,000 most variable probes, the first thing the EPV post recommends, brings that to 0.014. Peduzzi's rule wants 10. We are three orders of magnitude short, and no method below changes that; the methods differ only in whether they tell you.

One number to hold onto: a model that ignores the genes and predicts the prevalence, 24.1%, for everyone has a Brier score of 0.183. Anything worse than that has made things worse.

## The popular pipeline

Rank the probes by a t-test between relapsed and non-relapsed patients, keep the top 50, fit a logistic regression, report performance. This is not a straw man; it is the shape of hundreds of published signatures.

Fit to all 286 patients, the 50-gene model has an apparent AUC of 0.889. Split the data 70/30 and test on the held-out third, and it reports 0.753. That looks like validation. It is not, because the 50 genes were chosen using all 286 patients, including the 86 in the test set. Choose the genes using only the 200 training patients and test on the same held-out third, and the AUC is 0.503. On this particular split, honest selection turns a publishable number into a coin flip.

A single split is one draw, so Figure 1 shows 200 of them.

![Distribution of test-set AUC across 200 random 70/30 splits, with and without leakage](/images/worked-example/fig1_split_variance.png)

With the leak, the splits average 0.727 and never fall below 0.60. Without it, they average 0.586 with a standard deviation of 0.058, and range from 0.45 to 0.72. Two things are wrong at once. The leak adds about 0.14 of AUC that does not exist. And even the honest estimate moves by a quarter of the way from chance to perfect depending only on which 86 patients you held out, which is the [single-test-set post](/posts/2026/11/one-test-set-is-not-validation/) in one picture.

## The signature does not exist

The [gene-signature post](/posts/2026/10/gene-signature-instability/) suggested an experiment: bootstrap the patients, rerun the selection, count how often each gene survives. Two hundred bootstrap resamples, top 50 by t-test each time.

![Selection frequency of probes across 200 bootstrap top-50 lists](/images/worked-example/fig2_selection_frequency.png)

1,140 different probes appeared in at least one list. No probe appeared in 80% of them. Seven appeared in half. Two lists drawn from resamples of the same patients shared, at the median, 10% of their genes (Jaccard 0.10), and a typical bootstrap list overlapped the full-data list on 18 of its 50 genes. This is what Ein-Dor and Michiels reported for this generation of studies, reproduced in a few minutes on one of the same cohorts. Whatever signal there is, it is spread thinly over hundreds of correlated probes, and which 50 come out on top is decided by the draw.

## The model the series recommends

Keep every one of the 5,000 variance-filtered probes. Standardise them. Fit ridge-penalised logistic regression with the penalty chosen by five-fold cross-validated log loss inside the training data. No gene selection by outcome anywhere. The whole procedure, filter included, is one function so that it can be refit on every resample.

The apparent AUC of that model on its own training data is 1.000. With 5,000 predictors and 286 patients it separates the training data perfectly even under heavy shrinkage, and that number tells you nothing about the model except that you must not report it.

Honest estimates, from repeated five-fold cross-validation (ten repeats, the entire pipeline refit in every fold): AUC 0.712, with a standard deviation of 0.016 across the ten repeats. Brier score 0.163 against the null model's 0.183. Log loss 0.499. Out-of-fold predictions run from 3.5% to 64%.

The [accuracy post](/posts/2026/09/accuracy-improper-score/) said to draw the calibration curve. Figure 3 (right) does, for the ridge model and the 50-gene signature, both from out-of-fold predictions.

![Five validation estimates of AUC for both models, and calibration curves of out-of-fold predictions](/images/worked-example/fig3_validation_and_calibration.png)

The ridge model has a calibration slope of 1.26 and an intercept of 0.41: it is somewhat underconfident, which is what heavy ridge shrinkage does, and its probabilities could be stretched a little. Its dots sit near the diagonal. The 50-gene signature has a calibration slope of 0.24. Its predictions span 0.1% to 85%, and the observed relapse rate barely moves across that range. Its out-of-fold Brier score is 0.202, worse than the null model's 0.183: the signature's probabilities carry less information than the prevalence, because they are confident in both directions and wrong in both. Its honest AUC is 0.595.

So the series' claims hold on this dataset. Shrinkage on all the genes beats selection of a few (0.71 against 0.59). A model that ranks moderately well can still be useless as a probability (the signature), and a calibration curve is how you find out. The number you would have published from the popular pipeline was 0.89.

## Where the recommended validation failed

The [last post in the series](/posts/2026/11/one-test-set-is-not-validation/) recommended the optimism-corrected bootstrap over a single split, on the strength of Steyerberg and Harrell's comparison. I ran it here, 200 resamples, whole pipeline refit each time. Figure 3 (left) shows five estimates of the same AUC side by side.

For the ridge model the optimism-corrected bootstrap gave 0.943. Repeated cross-validation gave 0.712. The bootstrap is wrong by 0.23, and it is wrong in the dangerous direction.

The mechanism is worth understanding. The optimism bootstrap estimates how much a model flatters itself by fitting to a bootstrap sample and comparing performance on that sample with performance on the original data. The correction assumes the model does not simply memorise its training points. With 5,000 predictors and 286 patients, it does: the ridge model fits any sample it is given perfectly. About 63% of the original patients are in each bootstrap sample, so when the bootstrap model is scored on the original data, two thirds of those patients are ones it has already fit, and the "optimism" comes out small. The same thing happens to the 50-gene signature, less severely (0.741 corrected against 0.595 from cross-validation), because it memorises less.

Steyerberg and Harrell's simulations, which are the evidence behind the recommendation, ran at 5 to 80 events per variable with a handful of predictors. This dataset has 0.014 events per variable. Their result does not cover this regime, and I should have said so in the post rather than presenting the bootstrap as a general default. That recommendation was an extrapolation presented as a standard, and this is the correction.

Two bootstrap variants do better. The out-of-bag estimate scores each bootstrap model only on the patients not in its sample, and gives 0.713, agreeing with cross-validation. Efron and Tibshirani's .632+ estimator blends out-of-bag and apparent performance with a weight that adapts to how much the model overfits, and gives 0.770, which is still optimistic here because the apparent AUC of 1.0 pulls it up. For the signature model the two give 0.591 and 0.627.

The practical rule I now use: when the apparent performance of a model is near perfect, the standard optimism bootstrap cannot be trusted, and repeated cross-validation or the out-of-bag bootstrap is the estimate to report. When events per variable are comfortable and the model cannot interpolate, the optimism bootstrap remains the efficient choice the last post described. The way to know which situation you are in is to run both and look; they take a few minutes.

## What this model is good for

An AUC of 0.71 for bone relapse from expression alone, calibrated, from 69 events, is a modest and honest result. It says the arrays carry some prognostic information about bone relapse in this cohort, that the information is spread across many genes rather than concentrated in a signature the data can name, and that a risk estimate from this model is worth about what it says it is worth. It does not say which genes matter, and it is not validated on a second cohort, which is the test that would matter clinically. Every one of those sentences is a finding the popular pipeline would have hidden behind 0.89.

## Code

The whole analysis is [capstone.py](/files/worked-example/capstone.py) (Python, scikit-learn; about six minutes on two cores) and the figures are [figures.py](/files/worked-example/figures.py). Every number in this post is in [results.json](/files/worked-example/results.json), which the script writes. The data download is one line:

```bash
curl -O https://ftp.ncbi.nlm.nih.gov/geo/series/GSE2nnn/GSE2034/matrix/GSE2034_series_matrix.txt.gz
python3 capstone.py && python3 figures.py
```

## Resources

- Wang, Klijn, Zhang et al., [Gene-expression profiles to predict distant metastasis of lymph-node-negative primary breast cancer](https://doi.org/10.1016/S0140-6736(05)17947-1), *The Lancet* 2005;365:671–679. The source of GSE2034.
- Michiels, Koscielny, Hill, [Prediction of cancer outcome with microarrays: a multiple random validation strategy](https://doi.org/10.1016/S0140-6736(05)17866-0), *The Lancet* 2005;365:488–492.
- Efron, Tibshirani, [Improvements on cross-validation: the .632+ bootstrap method](https://doi.org/10.1080/01621459.1997.10474007), *JASA* 1997;92(438):548–560.
- Steyerberg, Harrell, Borsboom, Eijkemans, Vergouwe, Habbema, [Internal validation of predictive models](https://doi.org/10.1016/S0895-4356(01)00341-9), *J Clin Epidemiol* 2001;54(8):774–781.
- Frank Harrell, [Regression Modeling Strategies](https://hbiostat.org/rmsc/).

---

If you rerun this on another public cohort and the bootstrap behaves differently, or you can see a flaw in how I set the comparison up, I would like to know. The point of publishing the code is that the disagreement can be specific.
