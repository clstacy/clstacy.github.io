# Social posts for clstacy.github.io

One entry per blog post. Each has a LinkedIn version (a few short paragraphs, no hashtag wall) and a short version for Bluesky / X / Mastodon (under 300 characters including the link). Post on or after the date the article goes live. Links are the permalinks the posts are published at.

Suggested order of posting: BBTools posts on Saturdays as they go live, the statistics series on Wednesdays. The series posts reference each other, so posting them in order matters; the BBTools posts stand alone.

---

## BBTools overview (live now)
https://clstacy.github.io/posts/2026/04/bbtools-overview/

**LinkedIn**

Most of my early bioinformatics tool choices weren't really choices. I used what my advisor used, which was what their advisor used.

BBTools is the suite I wish someone had shown me on day one: one aligner, one QC tool, one read merger, and a pile of utilities that all share the same flag conventions, with documentation that explains why the defaults are what they are.

I wrote an introduction for people who haven't tried it, covering which tools to start with and where the docs hide. First of a series.

**Short**

BBTools is the bioinformatics suite I wish I'd been shown on day one: consistent flags, sensible defaults, and docs that explain the reasoning. An introduction for people who haven't tried it, first of a series: https://clstacy.github.io/posts/2026/04/bbtools-overview/

---

## BBDuk guide (live now)
https://clstacy.github.io/posts/2026/04/bbduk-guide/

**LinkedIn**

Adapter trimming is the step everyone runs and almost nobody reads the output of.

I rewrote my BBDuk guide so every number in it comes from a run you can reproduce in under a minute, on a simulated library built with the suite's own tools. It walks through what each flag does (mink and tbo are the two people skip that actually matter), how to read the summary BBDuk prints, why the adapter stats table names adapters that were never in your library, and how the same tool screens out phiX or any other contaminant.

The demo script is linked from the post if you want to follow along.

**Short**

Rewrote my BBDuk guide: every number now comes from a reproducible run on simulated reads. What each flag does, how to read the output, why the stats table lists adapters you never used, and contamination filtering with the same tool. https://clstacy.github.io/posts/2026/04/bbduk-guide/

---

## BBMap guide (26 September)
https://clstacy.github.io/posts/2026/09/bbmap-guide/

**LinkedIn**

BBMap prints a block of statistics after every run, and most people scroll straight past it. That block answers the questions you would otherwise open the BAM to ask: how much of the library is actually your organism, how many reads are multi-mapping, what the per-base error rate is, and whether the insert size came out where the core said it would.

New post: building an index, mapping paired reads, reading those statistics line by line, and using BBMap to pull contaminating reads out of a library with outu and outm. Because the demo reads are simulated, every claim in the post is graded against the truth: the phiX filter caught 492 of 492 spiked-in pairs and no false positives, and the "perfect alignment" fraction matches what the simulated error rate predicts.

**Short**

New in the BBTools series: BBMap for alignment and contamination filtering. How to read the stats block it prints (most people don't), and outu/outm for pulling contaminants out of a library, graded against known truth. https://clstacy.github.io/posts/2026/09/bbmap-guide/

---

## BBMerge guide (3 October)
https://clstacy.github.io/posts/2026/10/bbmerge-guide/

**LinkedIn**

Someone hands you FASTQ files and no record of which library kit was used. What adapters do you trim?

BBMerge can tell you. Any pair whose insert is shorter than the read has adapter after the insert, and once BBMerge finds the overlap it knows where the adapter starts. One flag (outa) writes the consensus adapter sequences from the reads alone. On my demo library it recovered the exact TruSeq sequences with no adapter file given.

The rest of the post covers the merging itself: why you adapter-trim but don't quality-trim before merging (700 more pairs merged on the demo data), how to pick a strictness level, and a check that matters more than the merge rate: I regenerated the reads with the true insert size in the name and counted wrong merges. Zero, at every strictness level.

**Short**

BBMerge can tell you which adapters are in a library from the reads alone (outa; it recovered the exact TruSeq sequences on my demo). New post on merging pairs, choosing strictness, and checking wrong merges against truth: 0 of 11,461. https://clstacy.github.io/posts/2026/10/bbmerge-guide/

---

## Your Classifier Is Answering the Wrong Question (23 September)
https://clstacy.github.io/posts/2026/09/classification-vs-prediction/

**LinkedIn**

Most of the "classifiers" built in computational biology should not be classifiers.

They should be probability models. A classifier bundles two things that belong to different people: estimating how likely an outcome is (the analyst's job) and deciding what to do about it (the clinician's, the assay designer's, the person with the budget). The threshold that turns a probability into a label encodes a cost trade-off, and it is almost never the analyst's to set.

First post in a series on classification versus prediction in genomics. It also says where classification is exactly right (base calling, barcode assignment, anything near-deterministic) and why prognosis is not one of those places.

**Short**

Most genomics "classifiers" should be probability models. The threshold that turns a probability into a label encodes a cost trade-off that isn't the analyst's to set. First in a series on classification vs prediction: https://clstacy.github.io/posts/2026/09/classification-vs-prediction/

---

## Accuracy Is a Bad Way to Judge a Predictor (30 September)
https://clstacy.github.io/posts/2026/09/accuracy-improper-score/

**LinkedIn**

If a metric can be improved by a model that is calibrated worse, the metric is broken. Accuracy is such a metric. So are sensitivity and specificity when used as optimisation targets, and F1 inherits the problem from all of them.

The reason is that they are discontinuous: a prediction of 0.51 and a prediction of 0.99 count the same, and a shift from 0.49 to 0.51 counts as an event. A rule that is blind to the difference between 0.51 and 0.99 is throwing away most of what a good model knows.

Second post in the series: what a proper scoring rule is, why calibration is the property nobody reports and everybody needs, and what I use instead (Brier score, decomposed, and the calibration curve).

**Short**

If a metric can be improved by a worse-calibrated model, the metric is broken. Accuracy, sensitivity, specificity and F1 are all such metrics. What to report instead, and why calibration is the property nobody shows: https://clstacy.github.io/posts/2026/09/accuracy-improper-score/

---

## You Probably Shouldn't Balance Your Classes (7 October)
https://clstacy.github.io/posts/2026/10/stop-balancing-classes/

**LinkedIn**

Class imbalance is not a disease of your data. It is a fact about the world: the outcome you care about is rare.

"Correcting" it with SMOTE, undersampling or oversampling changes what the model estimates. Train logistic regression on data undersampled to 1:1 and its intercept now reflects 50% prevalence instead of 0.1%. Every probability it emits is inflated, the ranking may survive so the AUC looks fine, and the numbers are wrong. van den Goorbergh and colleagues showed exactly this in simulation: corrections produced strongly overestimated risks with no gain in discrimination.

Third post in the series, on why rebalancing feels like rigour and is closer to the opposite, and the narrow case where undersampling is a defensible engineering choice.

**Short**

Class imbalance is not a problem to fix. SMOTE and undersampling make your probabilities wrong (intercept now reflects 50% prevalence), AUC looks fine, and you've built a model that lies about magnitudes. Third in the series: https://clstacy.github.io/posts/2026/10/stop-balancing-classes/

---

## Don't Cut Your Continuous Biomarker in Half (14 October)
https://clstacy.github.io/posts/2026/10/dont-dichotomize-biomarkers/

**LinkedIn**

A median split on a continuous biomarker costs about as much statistical power as throwing away a third of your samples. Cohen worked this out in 1983; Altman and Royston put it in the BMJ in 2006; the practice is still everywhere in biomarker papers.

The worse version is choosing the cutpoint that gives the smallest p-value. That is uncorrected multiple testing, it biases the effect away from the null, and the cutpoint will not replicate in the next cohort. The Kaplan-Meier curve with two cleanly separated arms is partly a picture of that search.

New post on keeping continuous predictors continuous, what a restricted cubic spline buys you, and how to give the clinic a cutoff without building it into the analysis.

**Short**

A median split costs about as much power as discarding a third of your samples (Cohen 1983). An "optimal" cutpoint chosen by p-value is worse. Keep continuous biomarkers continuous; here's how and why: https://clstacy.github.io/posts/2026/10/dont-dichotomize-biomarkers/

---

## Your Gene Signature Probably Won't Replicate (21 October)
https://clstacy.github.io/posts/2026/10/gene-signature-instability/

**LinkedIn**

Before you name a gene signature, try this: bootstrap your patients, rerun the whole feature-selection pipeline, and record which genes come out. Do it a hundred times.

In most omics settings the list changes every time. Ein-Dor and colleagues showed for breast cancer that many equally predictive gene lists could be produced from the same data, and later estimated that agreeing on even half the genes between two studies would take several thousand patients. Michiels and colleagues reanalysed the seven largest microarray prognosis studies and found five did no better than chance.

The signature is not the biology; it is one draw from a large pool of correlated genes. New post on why the instability is structural, and what actually helps (shrinkage instead of selection, and reporting selection frequencies with the list).

**Short**

Bootstrap your patients and rerun your gene selection 100 times. If the list changes every time, the specific genes were never the finding. Why signature instability is structural, and what helps: https://clstacy.github.io/posts/2026/10/gene-signature-instability/

---

## Count Your Events Before You Count Your Variables (28 October)
https://clstacy.github.io/posts/2026/10/events-per-variable-omics/

**LinkedIn**

A model does not learn from your samples. It learns from your events. Forty outcome events and twenty thousand candidate genes means forty facts adjudicating twenty thousand questions.

Events per variable is the number that governs whether a prediction model can mean anything, and in omics we are almost always broke while reporting our wealth in the wrong denomination. What counts as a variable is everything you considered, not the twenty you kept. Cross-validation does not fix this; it only measures it, and only if the whole pipeline is inside the folds.

New post on where the EPV rule comes from (Peduzzi 1996), what Harrell and Riley now recommend instead of a rule of thumb, and the three things that actually help: outcome-blind dimension reduction, penalisation, and calculating the sample size before the study rather than after the failed replication.

**Short**

A model learns from your events, not your samples. 40 events and 20,000 genes is 40 facts adjudicating 20,000 questions. Where the events-per-variable rule comes from and what to do when you're broke: https://clstacy.github.io/posts/2026/10/events-per-variable-omics/

---

## One Test Set Is Not Validation (4 November)
https://clstacy.github.io/posts/2026/11/one-test-set-is-not-validation/

**LinkedIn**

Split your data 70/30, train, record the test AUC. Now do it again with a different random split. In a study with a few hundred samples the number moves by a tenth of a point depending on which patients landed in the test set. So which split is the real performance? None of them.

The single train/test split is the ritual we treat as the gold standard of honest evaluation. In the small-n, large-p world it is statistically wasteful and high-variance, and Steyerberg and Harrell showed in 2001 that it is the least efficient internal validation method available. The optimism-corrected bootstrap uses every patient for both fitting and honest assessment.

Last post in the series: how the bootstrap estimates optimism, why "the entire pipeline" is the phrase doing all the work, and the one case where a held-out set is exactly right (a different cohort, for external validation).

**Short**

Split 70/30, record the AUC, repeat with a different split. It moves by a tenth of a point. A single test set is a noisy draw, not validation. Why the optimism-corrected bootstrap is the better default, last in the series: https://clstacy.github.io/posts/2026/11/one-test-set-is-not-validation/

---

## Reformat and Clumpify (10 October)
https://clstacy.github.io/posts/2026/10/reformat-and-clumpify/

**LinkedIn**

Reformat is the BBTools utility I have trouble explaining until someone has needed it. Exact subsampling with the pairs kept in sync. Interleave, de-interleave, and a one-word check (vpair) that your files really are paired. Pull the unmapped reads out of a BAM in one command. Bin quality scores and shrink a FASTQ by 31% without touching a base.

Clumpify does one odd thing, sorting reads so similar ones sit together, and gets three benefits from it: smaller files, faster downstream tools, and duplicate removal with no reference. I planted 2,000 duplicate pairs in the demo library; it found 4,002 at exact matching. The extra one was two genuine fragments with identical ends, which is the caveat every duplicate remover carries.

**Short**

Two BBTools utilities nobody writes about: Reformat (exact subsampling, interleaving, reads out of a BAM in one command) and Clumpify (smaller files, reference-free duplicate removal). Planted 2,000 duplicates, it found 4,002; the extra one is the lesson. https://clstacy.github.io/posts/2026/10/reformat-and-clumpify/

---

## BBTools in Nextflow (17 October)
https://clstacy.github.io/posts/2026/10/bbtools-in-nextflow/

**LinkedIn**

The BBTools series ends with the pipeline: BBDuk, BBMap and BBMerge as five Nextflow processes, a samplesheet in and a results folder out, with one config file deciding whether it runs on a laptop, in a Biocontainers image, or on a SLURM cluster.

It reproduces every number from the hand-run posts, which is the test a pipeline should pass before anyone else uses it. The post walks through one process line by line, shows what resume actually reruns when you change a step (only that step), and documents a gotcha that bit me: the results folder is a snapshot of the last run, not of the current code.

All three files are downloadable, and the demo data script builds the input in seconds.

**Short**

BBDuk + BBMap + BBMerge as a small Nextflow pipeline: samplesheet in, results out, one config for laptop / container / SLURM, resume that reruns only what changed. Reproduces the hand-run numbers. Files included. https://clstacy.github.io/posts/2026/10/bbtools-in-nextflow/

---

## Worked example (11 November)
https://clstacy.github.io/posts/2026/11/worked-example-honest-omics-model/

**LinkedIn**

I ran the whole classification-versus-prediction series on one public dataset: 286 breast tumours, 22,000 probes, 69 bone relapses (Wang et al. 2005, GSE2034).

The popular pipeline (top 50 genes by t-test, logistic regression, one train/test split) reports an AUC of 0.89. Select the genes without looking at the test set and the same split gives 0.50. Across 200 honest splits it ranges from 0.45 to 0.72. Bootstrap the gene selection 200 times and no gene appears in more than 80% of the lists. The signature's out-of-fold probabilities are worse than predicting the prevalence for everyone.

Ridge on all 5,000 filtered genes reaches an honest 0.71 and is calibrated. And the optimism-corrected bootstrap I recommended in the last post gave 0.94 for that model, against 0.71 from cross-validation. At 0.014 events per variable a model that memorises its training data breaks the standard bootstrap correction. The post explains why, shows which estimators survive, and corrects the earlier advice. Code and every number included.

**Short**

Ran the whole series on a public breast cancer cohort (286 tumours, 69 events). Popular pipeline says AUC 0.89; honest answer 0.59. Ridge on all genes: 0.71, calibrated. And the bootstrap I recommended failed at EPV 0.014. Code included. https://clstacy.github.io/posts/2026/11/worked-example-honest-omics-model/

---

## Let the classifier say "I don't know" (18 November)
https://clstacy.github.io/posts/2026/11/let-the-classifier-say-i-dont-know/

**LinkedIn**

A DNA methylation tumour classifier can be 96% accurate and print "66% confident" on every call. The published score for one widely used tool is missing a single constant; fit it once and the calibration error falls from 0.31 to 0.007, with no diagnosis changed. That was my Tübingen poster.

The Kraków poster asked the harder question: once the score is fixed, is a confident call equally trustworthy for every patient? In TCGA, which is 80% European ancestry, confident errors in stomach cancer were ten times more frequent for Asian-ancestry patients, and nearly six times more frequent in endometrioid uterine cancer for African-ancestry patients. The misclassified tumours genuinely resemble the cancer they were mistaken for; the model learned the boundary between look-alikes from one ancestry.

The fix is not to refuse those patients an answer. It is to let the classifier return a short list with a per-group coverage guarantee. Written for the people who order the test rather than the people who build it.

**Short**

A tumour classifier that's 96% accurate and says "66% confident" every time; and, once fixed, confident errors 10x more frequent for Asian-ancestry stomach cancer patients. Why the answer is a short list with a guarantee, not a refusal. For clinicians. https://clstacy.github.io/posts/2026/11/let-the-classifier-say-i-dont-know/
