---
title: 'Let the Tumour Classifier Say "I Don''t Know"'
date: 2026-11-18
permalink: /posts/2026/11/let-the-classifier-say-i-dont-know/
tags:
  - statistics
  - machine-learning
  - methylation
  - calibration
  - conformal-prediction
  - cancer
description: "A DNA methylation classifier can be 96% accurate and still print a confidence number that means nothing, and its confident mistakes can land on the patients it has seen least of. Two posters from this year, written up for people who order the test rather than build it."
---

> A classifier that is right 96% of the time and says "66% confident" every time is not being humble. It is being uninformative. And a classifier that says "99.9%" and is wrong is not being confident. It is being dangerous.

This post is the prose version of two posters I presented this year, at the Machine Learning Summer School on Reliability and Safety in Kraków and at MLSS in Tübingen. Both are about the same tool, a DNA methylation tumour classifier, and both are about the number it prints next to the diagnosis. I have written it for clinicians, pathologists and wet-lab colleagues rather than for the people who build these models, because the people who order the test are the ones the number is for. The analyses are my own and are not yet peer reviewed; the posters are linked at the end.

## What the classifier does

Every cell carries chemical tags on its DNA, and the pattern of tags differs by cell type and by cancer. A methylation classifier reads that pattern from a tumour sample and returns a tumour type. For rare tumours that look alike under the microscope, sinonasal and skull-base tumours among them, this is often the most reliable way to tell them apart, and it is the technology at the heart of the SPELCASTER project I work on.

The classifier in both posters is crossNN, a published model that works across measurement platforms. It is, by any ordinary standard, accurate: 96.2% on brain tumours and 98.4% on head and neck tumours in my runs. Next to each call it prints a confidence score. The question both posters ask is what that score is worth.

## Accurate but underconfident

The Tübingen poster starts from an odd observation. On the brain-tumour cohort the model is right 96% of the time, but its average reported confidence is 66%. Every point on a calibration plot sits above the diagonal: the model is far better than it says it is.

The reason turns out to be a missing constant. The published score divides the model's raw outputs by their spread before turning them into probabilities, which is a sensible way to make scores comparable across samples with different amounts of data. But the division has a coefficient of one in front of it because nobody put one there, and nothing in training ever asked the result to behave like a probability. Fit that one coefficient on the brain-tumour cohort (it comes out at 0.34) and the calibration error drops from 0.31 to 0.007. Freeze it and reuse it unchanged elsewhere, and the calibration error falls from 0.35 to 0.016 on the head and neck model, from 0.51 to 0.07 on the pan-cancer model, and from 0.56 to 0.09 on nanopore data covering 1.7% of the genome. A Bayesian treatment of the frozen weights (a Laplace posterior) predicts nearly the same correction, 0.44, from no labels at all.

Two things about this matter for a clinical reader. First, nothing about the diagnoses changes. Dividing by a positive number does not change which class wins, so the tool makes exactly the same calls before and after; only the number printed next to each call changes, and it changes from meaningless to meaningful. Second, the fix is one constant, not a retrained model. The poster is also honest about where it stops: the correction does nothing for detecting a tumour that is outside the model's list of classes altogether, and on the pan-cancer model the corrected scores are still overconfident in a way a single constant cannot fix.

## Precisely wrong

The Kraków poster asks the harder question. Suppose the confidence score is fixed. Can you trust a confident call equally for every patient?

The reference data behind most methylation classifiers come from The Cancer Genome Atlas, which is about 80% European ancestry: in the cohort I audited, 6,099 European, 795 African and 590 Asian ancestry cases, with American Indian/Alaska Native (21) and Native Hawaiian/Pacific Islander (10) too few to audit any single cancer. So I asked, within a single cancer type, how often a confident call (calibrated probability at least 0.8) is wrong, by ancestry.

For stomach cancer, confident calls were wrong in 0.8% of European-ancestry patients (2 of 253) and 7.9% of Asian-ancestry patients (7 of 89), a tenfold gap. For endometrioid uterine cancer, 1.9% of European-ancestry patients (4 of 208) against 11.1% of African-ancestry patients (7 of 63), nearly sixfold. Across the 28 ancestry-by-cancer cells with enough patients to test, confident mistakes were about twice as likely in people of non-European ancestry.

I call these loud errors: wrong, and confident about it. They are the failure a clinician cannot see coming, because the number next to the call is exactly the number that should have warned them.

## Why the errors are not just noise

The natural objection is that small groups give noisy estimates. Two things argue against that reading. The confidence intervals are on the poster and the gaps survive them. More tellingly, the misclassified tumours genuinely carry the methylation signature of the cancer they were mistaken for. Stomach cancers in Asian-ancestry patients that were called oesophageal adenocarcinoma score like oesophageal adenocarcinoma on that cancer's own markers. Endometrioid uterine cancers in African-ancestry women that were called the aggressive serous subtype have a serous-like methylation profile about twice as often as the same cancer in European-ancestry women, which matches the known excess of aggressive endometrial disease in that group.

So the model is not malfunctioning. It is reporting a real biological resemblance, and it has learned, from a reference set dominated by one ancestry, where the boundary between look-alike cancers lies for that ancestry. Patients whose tumours sit differently relative to that boundary get a confident, wrong answer. An ensemble of models trained the same way gives no warning, because every member learned the same boundary; the errors come from bias rather than variance, and averaging models does not remove bias.

## The third option: a set instead of a label

There are two obvious responses, and both are bad. The first is to carry on predicting confidently for patients unlike the training data, which produces loud errors. The second is to abstain whenever a patient comes from an under-represented group, which excludes exactly the people precision medicine already serves worst.

The third option is to let the classifier return a short list instead of a single answer, with a guarantee attached. This is conformal prediction. Rather than "this is oesophageal adenocarcinoma, 92%", the output is "the true type is one of {stomach adenocarcinoma, oesophageal adenocarcinoma}, and lists like this contain the true type 90% of the time". The width of the list is the honesty: an easy case gets a list of one, a hard case gets a longer one, and nobody is refused an answer.

The guarantee has to be made per ancestry group, because a 90% guarantee averaged over the whole cohort can be 95% for the majority and 80% for a minority while still averaging 90%. Group-conditional conformal prediction calibrates the threshold within each group separately, and on the TCGA cohort it delivered about 90% coverage within European, African and Asian ancestry alike. The lists stayed short: the median set size was one class for European and African ancestry and two for Asian ancestry, out of 149 possible classes, with a long tail for the genuinely ambiguous cases. For the stomach-versus-oesophageal look-alike cases, the 90% set contained the true type 85% of the time where the single top label was right 52% of the time.

## What this means if you order the test

A methylation classification report should carry a probability that means what it says, and the Tübingen result shows that for at least one widely used tool the published number does not, for a reason that is fixable with one constant and no change to any diagnosis. Ask whether the confidence on your report has been calibrated, and on what.

A confident call is not equally reliable for every patient. If your patient's ancestry is under-represented in the reference cohort, a high confidence score deserves the scrutiny you would give a borderline one, and a result that conflicts with histology is a reason to look harder rather than to defer to the number.

A short list with a coverage guarantee is a legitimate output. It is closer to how a good pathologist reports a difficult case ("consistent with A; B not excluded") than a single label with a percentage is, and it degrades gracefully for the patients the model knows least about instead of failing loudly. Building that into how these tools report is, I think, the most useful thing the machine-learning side can do for the clinical side in the next few years, and it is what I am working on.

## Posters

- [Precisely Wrong: Conformal Prediction for Honest Precision Oncology](/talks/2026-07-01-poster-MLSS-RS-Krakow) (MLSS^R&S 2026, Kraków). Group-conditional conformal prediction after Romano et al. 2020 (APS scores) and Lu et al. 2021.
- [Post-hoc Bayesian Uncertainty for a Deployed Tumour Classifier](/talks/2026-09-04-poster-MLSS-Tubingen) (MLSS 2026, Tübingen).
- The classifier is crossNN (Yuan et al. 2025). Ancestry composition of TCGA follows Carrot-Zhang et al. 2020.

---

This post sits alongside the [classification versus prediction](/posts/2026/09/classification-vs-prediction/) series, which makes the general argument that a model should hand back a probability and let the decision be made by the person who knows the costs. Here the probability was broken and the decision was being made for patients who were not in the room. Corrections and disagreements welcome, from either side of the bench.
