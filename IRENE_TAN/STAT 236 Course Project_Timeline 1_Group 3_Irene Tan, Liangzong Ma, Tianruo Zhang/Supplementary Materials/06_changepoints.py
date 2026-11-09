"""Data-driven change-point detection on quarterly network-feature series."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, ruptures as rpt, json
q = pd.read_csv("out/quarterly_features.csv")
q["log_us_cn_ties"] = np.log(q.us_cn_ties)
FEATS = {"cross_share": "Cross-border share of ties", "us_cn_aff": "US–China affinity (obs./exp.)",
         "cn_strength": "China's share of cross-border ties", "lam2": "λ₂ of normalised country network",
         "inv_P_us_cn": "Investor DCBM: P̂(US, China)", "inv_P_cn_other": "Investor DCBM: P̂(China, other)",
         "log_us_cn_ties": "log US–China ties"}
Q = q.dropna(subset=list(FEATS)).reset_index(drop=True)
Xz = ((Q[list(FEATS)] - Q[list(FEATS)].mean()) / Q[list(FEATS)].std()).values
n = len(Xz)
# --- multivariate: binary segmentation with Gaussian mean-shift cost, BIC-type selection
res = {}
algo = rpt.Binseg(model="l2", min_size=4, jump=1).fit(Xz)
costs = []
for k in range(0, 7):
    bk = algo.predict(n_bkps=k) if k else [n]
    c = algo.cost.sum_of_costs(bk); p = Xz.shape[1]
    ne = n / 4  # trailing 4-quarter windows overlap: effective sample size n/4
    bic = ne * p * np.log(c / (n * p)) + k * (p + 1) * np.log(ne)
    costs.append(dict(k=k, cost=c, bic=bic, bkps=[Q.q[b - 1] for b in bk[:-1]]))
C = pd.DataFrame(costs); print(C)
kbest = int(C.loc[C.bic.idxmin(), "k"])
pelt = rpt.Pelt(model="rbf", min_size=4).fit(Xz)
pen = np.log(n) * Xz.shape[1] * 0.25
pb = pelt.predict(pen=pen)
print("BIC k*", kbest, C.loc[C.bic.idxmin(), "bkps"], "| PELT-rbf", [Q.q[b - 1] for b in pb[:-1]])
# --- univariate: best single mean-shift break (sup-F) per feature with circular block bootstrap p-value
def supF(y, trim=.15):
    n = len(y); best = (-1, None)
    r0 = ((y - y.mean()) ** 2).sum()
    for k in range(int(trim * n), int((1 - trim) * n)):
        r1 = ((y[:k] - y[:k].mean()) ** 2).sum() + ((y[k:] - y[k:].mean()) ** 2).sum()
        F = (r0 - r1) / (r1 / (n - 2))
        if F > best[0]: best = (F, k)
    return best
rng = np.random.default_rng(0); uni = []
for f in FEATS:
    y = Q[f].values; F, k = supF(y)
    # null: demeaned AR(1)-like via block bootstrap of first differences re-integrated (stationary-in-differences null)
    dy = np.diff(y); B = 999; bl = 4; Fb = []
    for _ in range(B):
        idx = np.concatenate([np.arange(s, s + bl) % len(dy) for s in rng.integers(0, len(dy), len(dy) // bl + 1)])[:len(dy)]
        yb = np.concatenate([[0], np.cumsum(dy[idx] - dy.mean())])
        Fb.append(supF(yb)[0])
    pval = (np.sum(np.array(Fb) >= F) + 1) / (B + 1)
    uni.append(dict(feature=f, label=FEATS[f], break_q=Q.q[k], supF=F, p_boot=pval,
                    mean_before=y[:k].mean(), mean_after=y[k:].mean()))
U = pd.DataFrame(uni); print(U.round(3).to_string())
# --- bootstrap distribution of the first multivariate break location (resampling residuals within segments)
bk1 = algo.predict(n_bkps=kbest)
seg = np.zeros(n, int)
for j, b in enumerate(bk1[:-1]): seg[b:] = j + 1
mu = np.array([Xz[seg == s].mean(0) for s in range(seg.max() + 1)])[seg]; res_ = Xz - mu
locs = []
for _ in range(300):
    idx = np.concatenate([np.arange(s, s + 4) % n for s in rng.integers(0, n, n // 4 + 1)])[:n]
    Xb = mu + res_[idx]
    bb = rpt.Binseg(model="l2", min_size=4).fit(Xb).predict(n_bkps=kbest)
    locs.append([Q.q[b - 1] for b in bb[:-1]])
L = pd.DataFrame(locs)
ci = {j: L[j].value_counts(normalize=True).sort_index().round(3).to_dict() for j in L}
print("bootstrap break locations", ci)
json.dump({"bic": C.to_dict("records"), "kbest": kbest, "binseg": C.loc[C.bic.idxmin(), "bkps"],
           "pelt": [Q.q[b - 1] for b in pb[:-1]], "univariate": U.to_dict("records"), "boot": ci,
           "series": Q[["q"] + list(FEATS)].to_dict("records"), "labels": FEATS}, open("out/changepoints.json", "w"), default=str)
U.to_csv("out/changepoints_univariate.csv", index=False)

# --- attribution of the multivariate break: China-related vs China-free (global) feature groups
GROUPS = {"china": ["us_cn_aff", "cn_strength", "log_us_cn_ties", "inv_P_us_cn", "inv_P_cn_other"],
          "global_exCN": ["cross_share_exCN", "lam2_exCN", "inv_P_us_other"]}
q2 = pd.read_csv("out/quarterly_features.csv"); q2["log_us_cn_ties"] = np.log(q2.us_cn_ties)
grp = {}
for g, cols in GROUPS.items():
    Z = q2[cols].dropna(); qq = q2.loc[Z.index, "q"].values
    Zz = ((Z - Z.mean()) / Z.std()).values; nn = len(Zz); pp = Zz.shape[1]
    al = rpt.Binseg(model="l2", min_size=4).fit(Zz); out = []
    for k in range(0, 5):
        bk = al.predict(n_bkps=k) if k else [nn]
        c = al.cost.sum_of_costs(bk); ne = nn / 4
        out.append(dict(k=k, bic=ne * pp * np.log(c / (nn * pp)) + k * (pp + 1) * np.log(ne), bkps=[qq[b - 1] for b in bk[:-1]]))
    O = pd.DataFrame(out); kb = int(O.loc[O.bic.idxmin(), "k"])
    grp[g] = dict(table=O.to_dict("records"), kbest=kb, bkps=O.loc[O.bic.idxmin(), "bkps"], first=O.loc[1, "bkps"])
    print(g, "k*", kb, O.loc[O.bic.idxmin(), "bkps"], "| single break", O.loc[1, "bkps"])
J = json.load(open("out/changepoints.json")); J["groups"] = grp
J["series_all"] = q2.to_dict("records")
json.dump(J, open("out/changepoints.json", "w"), default=str)

# --- robustness: drop small-network investor series / start in 2013Q1
def seg(cols, start="2010Q1"):
    Z = q2[q2.q >= start][cols].dropna(); qq = q2.loc[Z.index, "q"].values
    Zz = ((Z - Z.mean()) / Z.std()).values; nn, pp = Zz.shape
    al = rpt.Binseg(model="l2", min_size=4).fit(Zz); o = []
    for k in range(5):
        bk = al.predict(n_bkps=k) if k else [nn]; c = al.cost.sum_of_costs(bk); ne = nn / 4
        o.append((k, ne * pp * np.log(c / (nn * pp)) + k * (pp + 1) * np.log(ne), [qq[b - 1] for b in bk[:-1]]))
    b = min(o, key=lambda r: r[1]); return dict(bic_bkps=b[2], single=o[1][2])
rob = {"China, country-level only": seg(["us_cn_aff", "cn_strength", "log_us_cn_ties"]),
       "China, all, from 2013Q1": seg(GROUPS["china"], "2013Q1"),
       "Global ex. China, country-level only": seg(["cross_share_exCN", "lam2_exCN"]),
       "Global ex. China, all, from 2013Q1": seg(GROUPS["global_exCN"], "2013Q1")}
print(rob)
J = json.load(open("out/changepoints.json")); J["robust"] = rob; json.dump(J, open("out/changepoints.json", "w"), default=str)
