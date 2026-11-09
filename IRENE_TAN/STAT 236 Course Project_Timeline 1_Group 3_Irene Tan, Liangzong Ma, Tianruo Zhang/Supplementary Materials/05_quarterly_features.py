"""Quarterly (trailing four-quarter) network-feature series for change-point detection."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd
from cnet_lib import NODES
from style import region
from inet_lib import coinvest
from netlib import block_P
e = pd.read_parquet("data/edges.parquet")
qs = sorted(e.q.unique()); qs = [q for q in qs if "2010Q1" <= q <= "2024Q4"]
REG = pd.Series({c: region(c) for c in NODES})
def wmat(z):
    z = z[z.inv_cty.isin(NODES) & z.st_cty.isin(NODES)]
    M = pd.crosstab(z.inv_cty, z.st_cty).reindex(index=NODES, columns=NODES, fill_value=0).values.astype(float)
    np.fill_diagonal(M, 0); return M
rows, prevW = [], {}
for t in range(3, len(qs)):
    lo, hi = qs[t - 3], qs[t]
    z = e[(e.q >= lo) & (e.q <= hi)]
    x = z[z.cross]
    N = len(x)
    cu = ((x.inv_cty == "China") & (x.st_cty == "United States")).sum(); uc = ((x.inv_cty == "United States") & (x.st_cty == "China")).sum()
    o = x.inv_cty.value_counts(); i_ = x.st_cty.value_counts()
    aff = (cu + uc) * N / (o.get("China", 0) * i_.get("United States", 0) + o.get("United States", 0) * i_.get("China", 0))
    s = o.add(i_, fill_value=0); cn_share = s.get("China", 0) / s.sum()
    W = wmat(x); S = W + W.T
    d = S.sum(1); d[d == 0] = 1
    Nrm = S / np.sqrt(np.outer(d, d)); ev = np.sort(np.linalg.eigvalsh(Nrm))[::-1]
    # weighted modularity of the region partition
    lab = REG.values; m2 = S.sum(); Q = sum(S[np.ix_(lab == r, lab == r)].sum() / m2 - (S[lab == r].sum() / m2) ** 2 for r in np.unique(lab))
    keep = np.array([c != "China" for c in NODES])
    S2 = S[np.ix_(keep, keep)]; d2 = S2.sum(1); d2[d2 == 0] = 1
    ev2 = np.sort(np.linalg.eigvalsh(S2 / np.sqrt(np.outer(d2, d2))))[::-1]
    zx = z[(z.inv_cty != "China") & (z.st_cty != "China")]
    cross_ex = zx.cross.mean()
    v = np.log1p(S[np.triu_indices(len(NODES), 1)])
    dist = np.nan
    if t - 4 in prevW: w0 = prevW[t - 4]; dist = 1 - v @ w0 / (np.linalg.norm(v) * np.linalg.norm(w0))
    prevW[t] = v
    # investor co-investment network, known (HQ) blocs, degree-corrected block connectivity
    A, C, att = coinvest(quarters=(lo, hi), min_rounds=5)
    isCN = (att.cty == "China").values; isUS = (att.cty == "United States").values
    Z = np.column_stack([isUS, isCN, ~(isUS | isCN)]).astype(float); Bk = block_P(A, Z)
    rows.append(dict(q=hi, cross_share=x.shape[0] / len(z), cross_share_exCN=cross_ex, lam2_exCN=ev2[1], us_cn_aff=aff, cn_strength=cn_share,
                     us_cn_ties=int(cu + uc), lam2=ev[1], lam3=ev[2], mod_region=Q, yoy_dist=dist,
                     inv_P_us_cn=Bk[0, 1], inv_P_cn_other=Bk[1, 2], inv_P_us_other=Bk[0, 2], inv_n=A.shape[0]))
    print(hi, round(aff, 3), round(Bk[0, 1], 3), flush=True)
pd.DataFrame(rows).to_csv("out/quarterly_features.csv", index=False)
