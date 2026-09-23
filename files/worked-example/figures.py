import json, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 11, "axes.titleweight": "bold",
                     "axes.titlelocation": "left", "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight"})
R = json.load(open("results.json"))
y = np.load("y.npy"); p_r = np.load("p_oof.npy"); p_s = np.clip(np.load("p_oof_sig.npy"), 1e-6, 1 - 1e-6)
clean = np.load("aucs_clean.npy"); leaky = np.load("aucs_leaky.npy")

# ---- Figure 1: what a single split can tell you
fig, ax = plt.subplots(figsize=(6.4, 3.4))
bins = np.linspace(0.4, 0.9, 26)
ax.hist(clean, bins=bins, color=BLUE, alpha=0.85, label="selection inside the split (honest)")
ax.hist(leaky, bins=bins, color=ORANGE, alpha=0.6, label="selection on all data first (leaks the test set)")
ax.axvline(0.5, color=MUTED, lw=1, ls=":")
ax.text(0.5, ax.get_ylim()[1] * 0.97, " chance", color=MUTED, va="top", fontsize=9)
ax.set_xlabel("test-set AUC of the 50-gene signature, one 70/30 split")
ax.set_ylabel("splits (of 200)")
ax.set_title("The same model, 200 different random splits")
ax.legend(frameon=False, fontsize=9, loc="upper right")
ax.grid(axis="y", color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)
fig.savefig("fig1_split_variance.png"); fig.savefig("fig1_split_variance.svg")

# ---- Figure 2: how stable is the gene list
freq = pd.read_csv("selection_frequency.csv", index_col=0).iloc[:, 0].sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(6.4, 3.2))
k = 150
ax.bar(np.arange(k), freq.values[:k], width=1.0, color=BLUE, edgecolor="none")
ax.axhline(0.8, color=ORANGE, lw=1.2)
ax.text(k - 1, 0.81, "in 80% of resamples: 0 genes", ha="right", va="bottom", color=ORANGE, fontsize=9)
ax.axhline(0.5, color=MUTED, lw=1, ls=":")
ax.text(k - 1, 0.51, f"in 50% of resamples: {R['B_n_probes_selected_in_50pct_of_bootstraps']} genes", ha="right", va="bottom", color=MUTED, fontsize=9)
ax.set_xlim(-1, k); ax.set_ylim(0, 1)
ax.set_xlabel(f"probe, ranked by how often it made the top-50 list ({R['B_n_probes_ever_selected']} probes ever did; first {k} shown)")
ax.set_ylabel("fraction of 200\nbootstrap lists")
ax.set_title("Which genes are in the signature depends on which patients you drew")
ax.grid(axis="y", color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)
fig.savefig("fig2_selection_frequency.png"); fig.savefig("fig2_selection_frequency.svg")

# ---- Figure 3: validation estimates side by side, and calibration
fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axes[0]
methods = ["apparent\n(training)", "optimism-\ncorrected\nbootstrap", ".632+\nbootstrap", "out-of-bag\nbootstrap", "repeated\n5-fold CV"]
ridge = [R["C_apparent_AUC"], R["C_corrected_AUC"], R["C_632plus_AUC"], R["C_oob_bootstrap_AUC"], R["C_repeatedCV_AUC_mean"]]
sig = [R["D_sig_apparent_AUC"], R["D_sig_corrected_AUC"], R["D_sig_632plus_AUC"], R["D_sig_oob_bootstrap_AUC"], R["D_sig_oof_AUC"]]
x = np.arange(len(methods)); w = 0.36
ax.bar(x - w / 2 - 0.02, ridge, w, color=BLUE, label="ridge on 5,000 genes")
ax.bar(x + w / 2 + 0.02, sig, w, color=ORANGE, label="top-50 signature")
for xi, v in zip(x - w / 2 - 0.02, ridge): ax.text(xi, v + 0.01, f"{v:.2f}", ha="center", fontsize=8, color=INK)
for xi, v in zip(x + w / 2 + 0.02, sig): ax.text(xi, v + 0.01, f"{v:.2f}", ha="center", fontsize=8, color=INK)
ax.axhline(0.5, color=MUTED, lw=1, ls=":")
ax.set_xticks(x); ax.set_xticklabels(methods, fontsize=8.5)
ax.set_ylim(0.4, 1.05); ax.set_ylabel("AUC")
ax.set_title("Five ways to estimate the same AUC")
ax.legend(frameon=False, fontsize=9, loc="upper right")
ax.grid(axis="y", color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)

ax = axes[1]
def binned(p, yy, nb=8):
    q = np.quantile(p, np.linspace(0, 1, nb + 1)); q[-1] += 1e-9
    idx = np.digitize(p, q[1:-1])
    return np.array([p[idx == i].mean() for i in range(nb)]), np.array([yy[idx == i].mean() for i in range(nb)]), np.array([(idx == i).sum() for i in range(nb)])
def logistic_cal(p, yy):
    lp = np.log(p / (1 - p)); lr = LogisticRegression(C=1e6).fit(lp.reshape(-1, 1), yy)
    g = np.linspace(0.02, 0.85, 100); lg = np.log(g / (1 - g))
    return g, 1 / (1 + np.exp(-(lr.intercept_[0] + lr.coef_[0, 0] * lg)))
ax.plot([0, 0.9], [0, 0.9], color=MUTED, lw=1, ls=":")
for p, col, lab in [(p_r, BLUE, "ridge"), (p_s, ORANGE, "top-50 signature")]:
    g, c = logistic_cal(p, y); ax.plot(g, c, color=col, lw=2, label=lab)
    mp, my, nn = binned(p, y); ax.scatter(mp, my, s=18 + nn / 4, color=col, edgecolor="white", lw=1, zorder=3)
ax.set_xlim(0, 0.9); ax.set_ylim(0, 0.9)
ax.set_xlabel("predicted probability of bone relapse (out-of-fold)")
ax.set_ylabel("observed fraction relapsed")
ax.set_title("Calibration of the out-of-fold predictions")
ax.text(0.86, 0.06, f"slope {R['C_oof_calibration_slope']:.2f}", color=BLUE, ha="right", fontsize=9)
ax.text(0.86, 0.01, f"slope {R['D_sig_oof_calibration_slope']:.2f}", color=ORANGE, ha="right", fontsize=9)
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.grid(color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)
fig.savefig("fig3_validation_and_calibration.png"); fig.savefig("fig3_validation_and_calibration.svg")
print("figures written")
