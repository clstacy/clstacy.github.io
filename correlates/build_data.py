"""Build the data pack for the 'Everything correlates with survival' page.
GSE7390 (TRANSBIG, Desmedt et al. 2007): 198 node-negative breast cancers, HG-U133A.
Outcome: distant-metastasis-free survival (t.dmfs days, e.dmfs)."""
import gzip, io, json, base64, numpy as np, pandas as pd

lines = gzip.open("GSE7390_series_matrix.txt.gz", "rt").readlines()
clin = {}
for l in [l for l in lines if l.startswith("!Sample_characteristics_ch1")]:
    vals = [v.strip().strip('"') for v in l.rstrip("\n").split("\t")[1:]]
    clin[vals[0].split(":")[0]] = [v.split(":", 1)[1].strip() for v in vals]
cl = pd.DataFrame(clin)
tab = [l for l in lines if not l.startswith("!") and l.strip()]
ex = pd.read_csv(io.StringIO("".join(tab)), sep="\t", index_col=0)
ex = ex.loc[[i for i in ex.index if not i.startswith("AFFX")]]
assert list(ex.columns) == [v.strip('"') for v in [l for l in lines if l.startswith("!Sample_geo_accession")][0].rstrip("\n").split("\t")[1:]]

raw = gzip.open("GPL96.annot.gz", "rt").read().split("\n")
start = next(i for i, l in enumerate(raw) if l.startswith("!platform_table_begin")) + 1
end = next(i for i, l in enumerate(raw) if l.startswith("!platform_table_end"))
ann = pd.read_csv(io.StringIO("\n".join(raw[start:end])), sep="\t", index_col=0, quoting=3, dtype=str)
sym = ann["Gene symbol"].reindex(ex.index).fillna("")
sym = sym.astype(str).str.split("///").str[0].str.strip()

# top-variance probes plus a set of famous genes
v = ex.var(axis=1)
famous = ["ESR1", "ERBB2", "MKI67", "AURKA", "TP53", "BRCA1", "BRCA2", "GAPDH", "ACTB", "PGR", "CCNB1", "TOP2A",
          "CDH1", "VIM", "KRT5", "KRT18", "MYC", "PTEN", "EGFR", "BCL2", "FOXA1", "GATA3", "CD8A", "PTPRC", "HBB", "ALB",
          "INS", "TTN", "RPL13A", "XIST", "RPS4Y1"]
keep = set(v.sort_values(ascending=False).index[:3000])
for g in famous:
    hits = v[sym == g]
    if len(hits): keep.add(hits.idxmax())
keep = [p for p in ex.index if p in keep]
X = ex.loc[keep].values  # probes x patients, log2

# quantise each probe to 0..255 by rank (ties by value order); only ordering matters for splits
R = np.zeros_like(X, dtype=np.uint8)
for i in range(X.shape[0]):
    r = pd.Series(X[i]).rank(method="first").values - 1
    R[i] = np.round(r / (X.shape[1] - 1) * 255).astype(np.uint8)

t = pd.to_numeric(cl["t.dmfs"]).values / 365.25
e = pd.to_numeric(cl["e.dmfs"]).values.astype(int)
dublin = json.load(open("dublin.json"))["daily"]["temperature_2m_max"]
assert len(dublin) == len(t) == 198

labels = [f"{sym[p]} ({p})" if sym[p] else p for p in keep]
pack = {
    "source": "GSE7390 (TRANSBIG; Desmedt et al. 2007, Clin Cancer Res), HG-U133A, 198 lymph-node-negative breast cancers. Outcome: distant-metastasis-free survival.",
    "n": int(len(t)), "events": int(e.sum()),
    "time_years": [round(float(x), 3) for x in t], "event": [int(x) for x in e],
    "clinical": {
        "age": [float(x) for x in pd.to_numeric(cl["age"])],
        "tumour size (cm)": [float(x) if x != "NA" else None for x in cl["size"]],
        "grade": [float(x) if x != "NA" else None for x in cl["grade"]],
        "ER status (1 = positive)": [float(x) for x in pd.to_numeric(cl["er"])],
    },
    "nonsense": {
        "Dublin Airport daily maximum temperature, 1 Jan to 17 Jul 1990 (°C); patient i gets day i": dublin,
    },
    "probe_labels": labels,
    "expr_u8_base64": base64.b64encode(R.tobytes()).decode(),
    "n_probes": int(R.shape[0]),
}
json.dump(pack, open("data.json", "w"))
np.save("R.npy", R); json.dump({"keep": keep, "labels": labels}, open("keep.json", "w"))
print("probes:", len(keep), "events:", int(e.sum()), "json MB:", round(len(json.dumps(pack)) / 1e6, 2))
print("famous present:", [g for g in famous if any(l.startswith(g + " ") for l in labels)])
