"""Worked example for clstacy.github.io: from a public expression matrix to a
calibrated, honestly validated risk model, with the shortcuts shown next to it.

Data: GSE2034 (Wang et al. 2005, Lancet), 286 lymph-node-negative breast
cancers on HG-U133A, MAS5 values from the GEO series matrix. Outcome used:
bone relapse (the only clinical field in the GEO record): 69 events / 286.

Everything is computed here; the post quotes this script's output.
"""
import gzip, io, re, json, time, sys
import numpy as np, pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

rng = np.random.default_rng(2026)
t0 = time.time()
OUT = {}

# ---------------------------------------------------------------- data
with gzip.open("GSE2034_series_matrix.txt.gz", "rt") as f:
    lines = f.readlines()
chars = [l for l in lines if l.startswith("!Sample_characteristics_ch1")][0]
y = np.array([int(re.search(r": (\d)", v).group(1)) for v in chars.rstrip("\n").split("\t")[1:]])
tab = [l for l in lines if not l.startswith("!") and l.strip()]
df = pd.read_csv(io.StringIO("".join(tab)), sep="\t", index_col=0)
df = df.loc[[i for i in df.index if not i.startswith("AFFX")]]
X_all = np.log2(np.clip(df.values.T.astype(float), 1, None))   # samples x probes
probes = df.index.values
n, p_total = X_all.shape
events = int(y.sum())
OUT["n"] = n; OUT["p_total"] = int(p_total); OUT["events"] = events
OUT["prevalence"] = round(events / n, 4)
OUT["EPV_all_probes"] = round(events / p_total, 4)
print(f"n={n} probes={p_total} events={events} prevalence={events/n:.3f} EPV={events/p_total:.4f}")

# unsupervised, outcome-blind filter: top 5000 probes by variance
P = 5000
def variance_filter(X, k=P):
    v = X.var(axis=0)
    return np.argsort(v)[::-1][:k]
keep = variance_filter(X_all)
X = X_all[:, keep]
OUT["p_after_variance_filter"] = P
OUT["EPV_after_filter"] = round(events / P, 4)

# null model reference
p0 = events / n
OUT["brier_null"] = round(brier_score_loss(y, np.full(n, p0)), 4)

def ttest_select(Xtr, ytr, k):
    t, _ = stats.ttest_ind(Xtr[ytr == 1], Xtr[ytr == 0], equal_var=False)
    return np.argsort(np.abs(t))[::-1][:k]

def small_logit():
    # weakly penalised logistic for the "signature" model (C=1 on standardised inputs)
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))

# ---------------------------------------------------------- A. the naive pipeline
K = 50
# A1: select on ALL data, then split (leakage), single split
sel_all = ttest_select(X, y, K)
tr, te = train_test_split(np.arange(n), test_size=0.3, stratify=y, random_state=1)
m = small_logit().fit(X[tr][:, sel_all], y[tr])
OUT["A1_leaky_single_split_AUC"] = round(roc_auc_score(y[te], m.predict_proba(X[te][:, sel_all])[:, 1]), 3)
# A2: select within training data only, single split
sel_tr = ttest_select(X[tr], y[tr], K)
m = small_logit().fit(X[tr][:, sel_tr], y[tr])
OUT["A2_clean_single_split_AUC"] = round(roc_auc_score(y[te], m.predict_proba(X[te][:, sel_tr])[:, 1]), 3)
# A3: apparent (training) AUC of the leaky model
m = small_logit().fit(X[:, sel_all], y)
OUT["A3_apparent_AUC_top50"] = round(roc_auc_score(y, m.predict_proba(X[:, sel_all])[:, 1]), 3)

# A4: how much does a clean single split move? 200 random 70/30 splits
aucs_leaky, aucs_clean = [], []
for s in range(200):
    tr, te = train_test_split(np.arange(n), test_size=0.3, stratify=y, random_state=100 + s)
    m = small_logit().fit(X[tr][:, sel_all], y[tr])
    aucs_leaky.append(roc_auc_score(y[te], m.predict_proba(X[te][:, sel_all])[:, 1]))
    s_tr = ttest_select(X[tr], y[tr], K)
    m = small_logit().fit(X[tr][:, s_tr], y[tr])
    aucs_clean.append(roc_auc_score(y[te], m.predict_proba(X[te][:, s_tr])[:, 1]))
aucs_leaky, aucs_clean = np.array(aucs_leaky), np.array(aucs_clean)
OUT["A4_leaky_splits"] = dict(mean=round(aucs_leaky.mean(), 3), sd=round(aucs_leaky.std(), 3),
                             p5=round(np.percentile(aucs_leaky, 5), 3), p95=round(np.percentile(aucs_leaky, 95), 3))
OUT["A4_clean_splits"] = dict(mean=round(aucs_clean.mean(), 3), sd=round(aucs_clean.std(), 3),
                             p5=round(np.percentile(aucs_clean, 5), 3), p95=round(np.percentile(aucs_clean, 95), 3),
                             min=round(aucs_clean.min(), 3), max=round(aucs_clean.max(), 3))
np.save("aucs_clean.npy", aucs_clean); np.save("aucs_leaky.npy", aucs_leaky)
print("A done", time.time() - t0)

# ---------------------------------------------------------- B. signature instability
B = 200
lists = []
for b in range(B):
    idx = rng.choice(n, n, replace=True)
    lists.append(set(ttest_select(X[idx], y[idx], K)))
freq = pd.Series(np.concatenate([list(s) for s in lists])).value_counts() / B
full_list = set(sel_all)
jacc = [len(a & b) / len(a | b) for i, a in enumerate(lists) for b in lists[i + 1:i + 6]]
OUT["B_bootstrap_lists"] = B
OUT["B_median_pairwise_jaccard"] = round(float(np.median(jacc)), 3)
OUT["B_mean_overlap_with_full_list"] = round(float(np.mean([len(s & full_list) for s in lists])), 1)
OUT["B_n_probes_ever_selected"] = int(len(freq))
OUT["B_n_probes_selected_in_50pct_of_bootstraps"] = int((freq >= 0.5).sum())
OUT["B_n_probes_selected_in_80pct_of_bootstraps"] = int((freq >= 0.8).sum())
OUT["B_top_probe_frequencies"] = [(probes[keep][i], round(float(f), 2)) for i, f in freq.head(10).items()]
freq.to_csv("selection_frequency.csv")
print("B done", time.time() - t0)

# ---------------------------------------------------------- C. the honest model
def ridge_pipeline():
    return make_pipeline(StandardScaler(),
                         LogisticRegressionCV(Cs=np.logspace(-6, 0, 13), cv=5, penalty="l2",
                                              scoring="neg_log_loss", max_iter=3000, n_jobs=4))

def fit_full_pipeline(Xa, ya):
    """the ENTIRE procedure: variance filter -> standardise -> ridge with CV-chosen penalty"""
    k = variance_filter(Xa)
    mdl = ridge_pipeline().fit(Xa[:, k], ya)
    return k, mdl

def predict(pipe, Xn):
    k, mdl = pipe
    return mdl.predict_proba(Xn[:, k])[:, 1]

def cal_slope_intercept(yy, pp):
    lp = np.log(pp / (1 - pp))
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(lp.reshape(-1, 1), yy)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])

full = fit_full_pipeline(X_all, y)
p_app = predict(full, X_all)
OUT["C_chosen_C"] = float(full[1][-1].C_[0])
OUT["C_apparent_AUC"] = round(roc_auc_score(y, p_app), 3)
OUT["C_apparent_Brier"] = round(brier_score_loss(y, p_app), 4)

# optimism-corrected bootstrap, whole pipeline inside every resample
BB = 200
opt_auc, opt_brier, opt_slope, oob_auc = [], [], [], []
for b in range(BB):
    idx = rng.choice(n, n, replace=True)
    oob = np.setdiff1d(np.arange(n), idx)
    pipe_b = fit_full_pipeline(X_all[idx], y[idx])
    pb_boot = predict(pipe_b, X_all[idx]); pb_orig = predict(pipe_b, X_all)
    oob_auc.append(roc_auc_score(y[oob], pb_orig[oob]))
    opt_auc.append(roc_auc_score(y[idx], pb_boot) - roc_auc_score(y, pb_orig))
    opt_brier.append(brier_score_loss(y[idx], pb_boot) - brier_score_loss(y, pb_orig))
    opt_slope.append(1.0 - cal_slope_intercept(y, pb_orig)[0])   # apparent slope is 1 by construction
    if b % 20 == 0: print("  boot", b, round(time.time() - t0), "s")
OUT["C_bootstraps"] = BB
OUT["C_optimism_AUC"] = round(float(np.mean(opt_auc)), 3)
OUT["C_corrected_AUC"] = round(OUT["C_apparent_AUC"] - float(np.mean(opt_auc)), 3)
OUT["C_optimism_Brier"] = round(float(np.mean(opt_brier)), 4)
OUT["C_corrected_Brier"] = round(OUT["C_apparent_Brier"] - float(np.mean(opt_brier)), 4)
OUT["C_corrected_calibration_slope"] = round(1.0 - float(np.mean(opt_slope)), 3)
def six32plus(err_app, err_oob, gamma=0.5):
    err_oob = min(err_oob, gamma)
    R = (err_oob - err_app) / (gamma - err_app) if (gamma > err_app and err_oob > err_app) else 0.0
    w = 0.632 / (1 - 0.368 * R)
    return (1 - w) * err_app + w * err_oob
OUT["C_oob_bootstrap_AUC"] = round(float(np.mean(oob_auc)), 3)
OUT["C_632plus_AUC"] = round(1 - six32plus(1 - OUT["C_apparent_AUC"], 1 - float(np.mean(oob_auc))), 3)
print("C bootstrap done", time.time() - t0)

# cross-check: repeated 5-fold CV of the whole pipeline, out-of-fold predictions
rkf = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=7)
oof = np.zeros((10, n)); aucs_cv = []
for i, (tr, te) in enumerate(rkf.split(X_all, y)):
    pipe = fit_full_pipeline(X_all[tr], y[tr])
    pr = predict(pipe, X_all[te]); oof[i // 5, te] = pr
    if (i + 1) % 5 == 0: aucs_cv.append(roc_auc_score(y, oof[i // 5]))
p_oof = oof.mean(axis=0)
OUT["C_repeatedCV_AUC_mean"] = round(float(np.mean(aucs_cv)), 3)
OUT["C_repeatedCV_AUC_sd"] = round(float(np.std(aucs_cv)), 3)
OUT["C_oof_Brier"] = round(brier_score_loss(y, p_oof), 4)
OUT["C_oof_logloss"] = round(log_loss(y, p_oof), 4)
sl, ic = cal_slope_intercept(y, p_oof)
OUT["C_oof_calibration_slope"] = round(sl, 3); OUT["C_oof_calibration_intercept"] = round(ic, 3)
OUT["C_oof_pred_range"] = [round(float(p_oof.min()), 3), round(float(p_oof.max()), 3)]
np.save("p_oof.npy", p_oof); np.save("y.npy", y)
print("C cv done", time.time() - t0)

# ---------------------------------------------------------- D. the top-50 signature, validated honestly
# same optimism bootstrap for the t-test-select-50 + logistic pipeline
def fit_sig_pipeline(Xa, ya):
    k = variance_filter(Xa); s = ttest_select(Xa[:, k], ya, K)
    mdl = small_logit().fit(Xa[:, k][:, s], ya)
    return (k, s, mdl)
def predict_sig(pipe, Xn):
    k, s, mdl = pipe
    return mdl.predict_proba(Xn[:, k][:, s])[:, 1]
sig_full = fit_sig_pipeline(X_all, y); ps_app = predict_sig(sig_full, X_all)
OUT["D_sig_apparent_AUC"] = round(roc_auc_score(y, ps_app), 3)
opt = []; opt_sl = []; oob_s = []
for b in range(BB):
    idx = rng.choice(n, n, replace=True)
    oob = np.setdiff1d(np.arange(n), idx)
    pb = fit_sig_pipeline(X_all[idx], y[idx]); po = predict_sig(pb, X_all)
    oob_s.append(roc_auc_score(y[oob], po[oob]))
    opt.append(roc_auc_score(y[idx], predict_sig(pb, X_all[idx])) - roc_auc_score(y, po))
    opt_sl.append(1.0 - cal_slope_intercept(y, np.clip(predict_sig(pb, X_all), 1e-6, 1 - 1e-6))[0])
OUT["D_sig_optimism_AUC"] = round(float(np.mean(opt)), 3)
OUT["D_sig_corrected_AUC"] = round(OUT["D_sig_apparent_AUC"] - float(np.mean(opt)), 3)
OUT["D_sig_corrected_calibration_slope"] = round(1.0 - float(np.mean(opt_sl)), 3)
OUT["D_sig_oob_bootstrap_AUC"] = round(float(np.mean(oob_s)), 3)
OUT["D_sig_632plus_AUC"] = round(1 - six32plus(1 - OUT["D_sig_apparent_AUC"], 1 - float(np.mean(oob_s))), 3)
# out-of-fold predictions for the signature pipeline (one 5x10 repeated CV)
oof_s = np.zeros((10, n))
for i, (tr, te) in enumerate(rkf.split(X_all, y)):
    pb = fit_sig_pipeline(X_all[tr], y[tr]); oof_s[i // 5, te] = predict_sig(pb, X_all[te])
p_oof_s = oof_s.mean(axis=0)
OUT["D_sig_oof_AUC"] = round(roc_auc_score(y, p_oof_s), 3)
OUT["D_sig_oof_Brier"] = round(brier_score_loss(y, np.clip(p_oof_s, 1e-6, 1 - 1e-6)), 4)
sl, ic = cal_slope_intercept(y, np.clip(p_oof_s, 1e-6, 1 - 1e-6))
OUT["D_sig_oof_calibration_slope"] = round(sl, 3)
OUT["D_sig_oof_pred_range"] = [round(float(p_oof_s.min()), 3), round(float(p_oof_s.max()), 3)]
np.save("p_oof_sig.npy", p_oof_s)
print("D done", time.time() - t0)

OUT["runtime_s"] = round(time.time() - t0)
json.dump(OUT, open("results.json", "w"), indent=1)
print(json.dumps(OUT, indent=1))
