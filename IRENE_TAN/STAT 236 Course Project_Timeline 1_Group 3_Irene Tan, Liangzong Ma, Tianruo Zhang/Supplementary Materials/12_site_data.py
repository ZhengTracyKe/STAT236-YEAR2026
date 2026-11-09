"""Bundle results into one JSON for the interactive site."""
import sys; sys.path.insert(0, "code")
import json, numpy as np, pandas as pd
from cnet_lib import NODES
from style import region, ISO
LL = {"United States": (-98, 39), "United Kingdom": (-2, 54), "Singapore": (103.8, 1.35), "China": (104, 35), "Germany": (10, 51),
      "Canada": (-106, 56), "India": (78, 22), "Hong Kong": (114.2, 22.3), "France": (2.3, 46.5), "Israel": (34.9, 31.5),
      "Switzerland": (8.2, 46.8), "Japan": (138, 36.5), "Netherlands": (5.3, 52.2), "United Arab Emirates": (54, 24),
      "South Korea": (127.8, 36.3), "Australia": (134, -25), "Spain": (-3.7, 40.3), "Sweden": (16, 62), "Brazil": (-51, -10),
      "Indonesia": (113, -2), "Mexico": (-102, 23.6), "Luxembourg": (6.1, 49.8), "Belgium": (4.5, 50.6), "Vietnam": (106, 16),
      "Ireland": (-8, 53.3), "Denmark": (10, 56), "Finland": (26, 64), "Taiwan": (121, 23.7), "Italy": (12.5, 42.8),
      "Estonia": (25, 58.7), "Nigeria": (8, 9.5), "Austria": (14.5, 47.5), "Norway": (9, 61), "Turkey": (35, 39),
      "Malaysia": (102, 4), "Kenya": (38, 0.2), "Russia": (60, 58), "Portugal": (-8.2, 39.6), "Saudi Arabia": (45, 24),
      "Colombia": (-74, 4.5), "Poland": (19.4, 52), "South Africa": (24, -29), "Philippines": (122, 12.5), "Argentina": (-64, -34),
      "New Zealand": (174, -41), "Thailand": (101, 15), "Chile": (-71, -33), "Czech Republic": (15.5, 49.8), "Egypt": (30, 26.8),
      "Cyprus": (33.2, 35), "Lithuania": (24, 55.3)}
assert all(c in LL for c in NODES)
S = {}
# ---- countries
cd = json.load(open("out/country_dcmm.json"))
S["countries"] = [dict(name=c, iso=ISO.get(c, c[:2]), region=region(c), lon=LL[c][0], lat=LL[c][1],
                       pi=[round(v, 3) for v in cd["Pi_full"][i]], s=int(cd["strength_full"][i])) for i, c in enumerate(NODES)]
S["triangle"] = {"names": cd["names"], "windows": cd["windows"], "P": cd["P_full"],
                 "traj": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in cd["traj"]]}
# ---- yearly flows for the map: all pairs among NODES with >=5 ties
e = pd.read_parquet("data/edges.parquet"); x = e[e.cross & e.inv_cty.isin(NODES) & e.st_cty.isin(NODES)]
f = x.groupby(["year", "inv_cty", "st_cty"]).size().rename("n").reset_index()
idx = {c: i for i, c in enumerate(NODES)}
S["flows"] = {int(y): [[idx[r.inv_cty], idx[r.st_cty], int(r.n)] for r in g[g.n >= 5].itertuples()] for y, g in f.groupby("year")}
tot = e[e.cross].groupby("year").size(); S["cross_total"] = {int(k): int(v) for k, v in tot.items()}
D = json.load(open("out/descriptives.json"))
S["yearly"] = D["yearly"]; S["composition"] = D["composition"]; S["uschina"] = D["uschina"]
S["ind_cb"] = D["ind_cb"]; S["cb_mix"] = pd.read_csv("out/fig04_cb_mix.csv").to_dict("records"); S["uschina_mix"] = D["uschina_mix"]; S["rca"] = D["rca"]
# ---- investor networks (eras)
er = json.load(open("out/eras.json"))
rng = np.random.default_rng(1)
for k in er:
    E = er[k]; ed = E["edges"]; m = min(len(ed), 9000); ed = [ed[i] for i in rng.choice(len(ed), m, replace=False)]
    ids = {n["id"]: j for j, n in enumerate(E["nodes"])}
    S["net_" + k] = dict(window=E["window"], n=E["n"], m=E["m"], K=E["K"],
                         nodes=[[round(n["x"], 4), round(n["y"], 4), n["c"], region(n["cty"]) if isinstance(n["cty"], str) else "Other",
                                 n["name"], n["cty"], n["deg"], n["piCN"]] for n in E["nodes"]],
                         edges=[[ids[u], ids[v]] for u, v in ed], comms=E["comms"], cn_k=E["cn_k"])
# ---- change points
cp = json.load(open("out/changepoints.json"))
cols = ["q", "us_cn_aff", "cn_strength", "log_us_cn_ties", "inv_P_us_cn", "inv_P_cn_other", "cross_share_exCN", "lam2_exCN", "inv_P_us_other", "cross_share", "lam2"]
qs = pd.DataFrame(cp["series_all"]); qs["log_us_cn_ties"] = np.log(qs.us_cn_ties)
S["cp"] = {"series": qs[cols].round(4).to_dict("list"), "china": cp["groups"]["china"]["bkps"], "global": cp["groups"]["global_exCN"]["bkps"],
           "all": cp["binseg"], "pelt": cp["pelt"], "boot": cp["boot"], "robust": cp["robust"]}
# ---- causal
es = pd.read_csv("out/es_pooled.csv"); S["es"] = es.round(4).to_dict("records")
dc = json.load(open("out/dcmm_counterfactual.json")); th = pd.read_csv("out/theta_t.csv", index_col=0)
S["dcmm"] = {"dist": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in dc["dist"]],
             "cn_us": dc["cn_us"], "us_cn": dc["us_cn"], "ru_west": dc["ru_west"],
             "theta": {c: (th[c] * 100).round(3).tolist() for c in ["China", "United States", "Singapore", "Hong Kong", "India", "United Kingdom", "Japan", "Israel", "Germany"]},
             "years": th.index.tolist()}
ti = pd.read_csv("out/industry_did.csv"); S["ind_did"] = ti[["term", "Estimate", "Std. Error", "Pr(>|t|)"]].round(4).to_dict("records")
P = pd.read_csv("out/permutation.csv"); S["perm"] = P.round(4).to_dict("records")
il = json.load(open("out/investor_level.json"))
S["bridges"] = il["bridges"]; S["cn_nb_region"] = il["cn_nb_by_region"]
F = pd.DataFrame(il["firms"]); S["firms"] = {n: g.sort_values("mid")[["mid", "cn_nb", "us_nb", "cty", "rounds"]].round(3).values.tolist() for n, g in F.groupby("name")}
json.dump(S, open("site/data.json", "w"), separators=(",", ":"), default=float)
import os; print(os.path.getsize("site/data.json") / 1e6, "MB")
