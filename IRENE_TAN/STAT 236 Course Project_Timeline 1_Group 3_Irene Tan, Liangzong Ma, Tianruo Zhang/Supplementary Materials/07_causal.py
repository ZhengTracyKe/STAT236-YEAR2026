"""Attribution of the detected break: gravity event studies, permutation inference, industry triple differences."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, pyfixest as pf, json, warnings; warnings.filterwarnings("ignore")
from cnet_lib import NODES
from style import EUROPE
e = pd.read_parquet("data/edges.parquet")
e = e[e.inv_cty.isin(NODES) & e.st_cty.isin(NODES)]
yrs = range(2010, 2025)
g = e.groupby(["inv_cty", "st_cty", "year"]).size().rename("n")
idx = pd.MultiIndex.from_product([NODES, NODES, yrs], names=["inv_cty", "st_cty", "year"])
g = g.reindex(idx, fill_value=0).reset_index()
g["dyad"] = g.inv_cty + ">" + g.st_cty; g["it"] = g.inv_cty + g.year.astype(str); g["jt"] = g.st_cty + g.year.astype(str)
USCN = g.dyad.isin(["United States>China", "China>United States"])
WEST = EUROPE | {"United States", "Canada"}
RUW = ((g.inv_cty == "Russia") & g.st_cty.isin(WEST)) | (g.inv_cty.isin(WEST) & (g.st_cty == "Russia"))
out = {}
# (a) pooled event studies: US-China (both directions) and Russia-West, reference year 2017
terms = []
for lab, m in [("uscn", USCN), ("ruw", RUW)]:
    for t in yrs:
        if t == 2017: continue
        c = f"{lab}_{t}"; g[c] = (m & (g.year == t)).astype(int); terms.append(c)
mod = pf.fepois(f"n ~ {'+'.join(terms)} | dyad + it + jt", data=g, vcov={"CRV1": "dyad"})
tb = mod.tidy().reset_index().rename(columns={"Coefficient": "term"})
tb["group"] = tb.term.str.split("_").str[0]; tb["year"] = tb.term.str.split("_").str[1].astype(int)
tb = tb[["group", "year", "Estimate", "Std. Error", "Pr(>|t|)"]]; tb.to_csv("out/es_pooled.csv", index=False)
print(tb.pivot(index="year", columns="group", values="Estimate").round(2))
out["es"] = tb.to_dict("records")
# (b) DiD windows and permutation inference across all cross-border dyads (post = 2019-21 / 2022-24; pre = 2014-17)
h = g[(g.year.between(2014, 2017)) | (g.year >= 2019)].copy()
pre = h[h.year <= 2017].groupby("dyad").n.mean()
cand = [d for d in pre[pre >= 20].index if d.split(">")[0] != d.split(">")[1]]
def did(dmask, post):
    hh = h[(h.year <= 2017) | h.year.between(*post)].copy()
    hh["T"] = (dmask.loc[hh.index] & hh.year.between(*post)).astype(int)
    m = pf.fepois("n ~ T | dyad + it + jt", data=hh, vcov="iid"); return float(m.coef().iloc[0])
perm = []
for post in [(2019, 2021), (2022, 2024)]:
    for d in cand:
        perm.append(dict(post=f"{post[0]}-{post[1]}", dyad=d, b=did(h.dyad == d, post)))
P = pd.DataFrame(perm); P.to_csv("out/permutation.csv", index=False)
for post, s in P.groupby("post"):
    s = s.sort_values("b").reset_index(drop=True)
    for d in ["China>United States", "United States>China"]:
        r = int(s.index[s.dyad == d][0]) + 1
        print(post, d, "b=%.3f" % s.loc[r - 1, "b"], "rank", r, "of", len(s))
    print("  lowest:", list(zip(s.dyad.head(6), s.b.head(6).round(2))))
out["perm_n"] = len(cand)
# (c) industry triple differences for US-China pairs
gi = e.groupby(["inv_cty", "st_cty", "industry", "year"]).size().rename("n")
IND = sorted(e.industry.unique())
idx = pd.MultiIndex.from_product([NODES, NODES, IND, yrs], names=["inv_cty", "st_cty", "industry", "year"])
gi = gi.reindex(idx, fill_value=0).reset_index()
gi = gi[gi.inv_cty != gi.st_cty]
gi = gi[(gi.year <= 2017) | (gi.year >= 2019)]
gi["pi"] = gi.inv_cty + ">" + gi.st_cty + "|" + gi.industry
gi["iit"] = gi.inv_cty + gi.industry + gi.year.astype(str); gi["jit"] = gi.st_cty + gi.industry + gi.year.astype(str)
m = gi.inv_cty.isin(["United States", "China"]) & gi.st_cty.isin(["United States", "China"])
terms = []
for k in IND:
    s = k.split()[0].replace("&", "").lower()
    for lab, (a, b) in [("p1", (2019, 2021)), ("p2", (2022, 2024))]:
        c = f"{s}_{lab}"; gi[c] = (m & (gi.industry == k) & gi.year.between(a, b)).astype(int); terms.append(c)
mi = pf.fepois(f"n ~ {'+'.join(terms)} | pi + iit + jit", data=gi, vcov={"CRV1": "pi"})
ti = mi.tidy().reset_index().rename(columns={"Coefficient": "term"}); print(ti.round(3))
ti.to_csv("out/industry_did.csv", index=False)
json.dump(out, open("out/causal.json", "w"), default=float)
