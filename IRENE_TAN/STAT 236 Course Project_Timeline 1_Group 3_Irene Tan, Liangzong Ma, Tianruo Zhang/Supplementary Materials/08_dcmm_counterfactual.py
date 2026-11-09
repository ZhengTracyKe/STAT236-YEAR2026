"""Model-based link prediction (Lec 11): a degree-corrected mixed-membership Poisson model fitted on the
pre-break period predicts each country pair's ties given each year's node activity; deficits = observed/predicted."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json
from cnet_lib import NODES, flows, class_network
from netlib import mixed_score_plus
from style import EUROPE
n = len(NODES); K = 3
A, _ = class_network(flows((2010, 2024)), sd=0.0)
Pi = mixed_score_plus(A, K, seed=1)["Pi"]
names = ["Atlantic core", "Asia-Pacific", "Emerging & periphery"]
order = [int(np.argmax(Pi[NODES.index(c)])) for c in ["United Kingdom", "Japan", "Brazil"]]; Pi = Pi[:, order]
Y = {t: flows((t, t)) for t in range(2010, 2025)}
off = ~np.eye(n, dtype=bool)
def ipf(Om, Yt, it=200):
    a = np.ones(n); b = np.ones(n); r = Yt.sum(1); c = Yt.sum(0)
    for _ in range(it):
        a = r / np.maximum((Om * b[None, :]).sum(1), 1e-12)
        b = c / np.maximum((Om * a[:, None]).sum(0), 1e-12)
    return a, b
def fit_P(years, it=60):
    P = np.ones((K, K))
    for _ in range(it):
        num = np.zeros((K, K)); den = np.zeros((K, K))
        for t in years:
            Om = Pi @ P @ Pi.T * off; a, b = ipf(Om, Y[t], 50); Yh = a[:, None] * b[None, :] * Om
            num += Pi.T @ (Y[t] * off) @ Pi; den += Pi.T @ Yh @ Pi
        P *= num / np.maximum(den, 1e-12)
        P /= P[0, 0]
    return P
P_pre = fit_P(range(2014, 2018))
Om = Pi @ P_pre @ Pi.T * off
rows = []
for t in range(2010, 2025):
    a, b = ipf(Om, Y[t]); Yh = a[:, None] * b[None, :] * Om
    for i in range(n):
        for j in range(n):
            if i != j: rows.append(dict(year=t, i=NODES[i], j=NODES[j], obs=Y[t][i, j], pred=Yh[i, j], a=a[i], b=b[j]))
D = pd.DataFrame(rows)
pre = D[D.year.between(2014, 2017)].groupby(["i", "j"])[["obs", "pred"]].sum()
base = (pre.obs / pre.pred).rename("base")
D = D.join(base, on=["i", "j"])
D["deficit"] = (D.obs / D.pred) / D.base            # 1 = on pre-period path
corr = np.corrcoef(np.log1p(D[D.year.between(2014, 2017)].obs), np.log1p(D[D.year.between(2014, 2017)].pred))[0, 1]
big = pre[pre.obs >= 80].index                       # pairs with >= 20 ties a year pre-break
Db = D.set_index(["i", "j"]).loc[big].reset_index()
dist = Db.groupby("year").deficit.describe(percentiles=[.1, .25, .5, .75, .9])
def pair(i, j): return D[(D.i == i) & (D.j == j)].set_index("year").deficit
WEST = EUROPE | {"United States", "Canada"}
ru = D[((D.i == "Russia") & D.j.isin(WEST)) | (D.i.isin(WEST) & (D.j == "Russia"))]
ru = ru.groupby("year")[["obs", "pred"]].sum(); ru_def = (ru.obs / ru.pred) / (ru.loc[2014:2017].obs.sum() / ru.loc[2014:2017].pred.sum())
res = {"P_pre": P_pre.round(4).tolist(), "names": names, "fit_corr_log": corr,
       "dist": dist.reset_index().to_dict("records"),
       "cn_us": pair("China", "United States").round(4).to_dict(), "us_cn": pair("United States", "China").round(4).to_dict(),
       "ru_west": ru_def.round(4).to_dict(), "n_pairs": len(big)}
json.dump(res, open("out/dcmm_counterfactual.json", "w"), default=float)
print("P_pre", P_pre.round(3)); print("fit corr (log)", round(corr, 3))
print(pd.DataFrame({"p10": dist["10%"], "median": dist["50%"], "p90": dist["90%"], "CN>US": pair("China", "United States"),
                    "US>CN": pair("United States", "China"), "RU-West": ru_def}).round(2))
# node activity parameters (degree heterogeneity theta_t): China and peers, relative to 2017
A_ = D.groupby(["year", "i"]).a.first().unstack(); B_ = D.groupby(["year", "j"]).b.first().unstack()
th = pd.DataFrame({c: np.sqrt(A_[c] * B_[c]) for c in NODES}); th = th.div(th.sum(1), axis=0)
th.to_csv("out/theta_t.csv")
print((th[["China", "United States", "Singapore", "Hong Kong", "India", "United Kingdom"]] * 100).round(2))
