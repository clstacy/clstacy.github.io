---
title: "Post-hoc Bayesian Uncertainty for a Deployed Tumour Classifier: Calibration and Out-of-Distribution Detection Under Platform Shift"
collection: talks
type: "Poster"
permalink: /talks/2026-09-04-poster-MLSS-Tubingen
venue: "Machine Learning Summer School 2026 (MLSS 2026), Max Planck Institute for Intelligent Systems"
date: 2026-09-04
location: "Tübingen, Germany"
---

Stacy, C. L. and Das, S.

A deployed cross-platform methylation classifier (crossNN) is accurate but underconfident: its own scores sit above the calibration diagonal on every platform. A diagonal Laplace posterior on the frozen weights, with the prior set by the MacKay evidence, yields a probit predictive whose scale acts as a single temperature. Tracking the logit standard deviation carries that scale across platforms, so one number fixes the calibration of the 18-, 91- and 178-class models with nothing refit and no diagnosis changed. The poster also reports where this stops helping: out-of-distribution ranking barely moves, and no scalar detects a tumour outside the model's class set.

[Download the poster (PDF)](/files/Stacy_MLSS_2026_Tubingen_poster.pdf)
