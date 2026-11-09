"""Investor-level bridging: neighbourhood membership in the co-investment network across rolling windows."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json
from inet_lib import coinvest
from style import region
wins = [(y, y + 2) for y in range(2010, 2023)]
rows = []
for a, b in wins:
    A, C, att = coinvest((a, b))
    isCN = (att.cty == "China").values.astype(float); isUS = (att.cty == "United States").values.astype(float)
    deg = np.asarray(A.sum(1)).ravel()
    att["deg"] = deg; att["cn_nb"] = A @ isCN / np.maximum(deg, 1); att["us_nb"] = A @ isUS / np.maximum(deg, 1)
    att["window"] = f"{a}-{b}"; att["mid"] = a + 1
    rows.append(att.reset_index().rename(columns={"index": "InvestorID"}))
    print(a, b, len(att), flush=True)
R = pd.concat(rows, ignore_index=True); R["reg"] = R.cty.map(region)
R.to_parquet("out/investor_neighbourhood.parquet")
# bridges: investors whose co-investors are >=20% China-HQ and >=20% US-HQ
R["bridge"] = (R.cn_nb >= .2) & (R.us_nb >= .2)
R["bridge_nonCN"] = R.bridge & (R.cty != "China")
S = R.groupby("mid").agg(n=("InvestorID", "size"), bridges=("bridge", "sum"), bridges_nonCN=("bridge_nonCN", "sum"))
S["bridge_share"] = S.bridges / S.n
G = R[R.reg != "China"].groupby(["mid", "reg"]).cn_nb.mean().unstack()
H = R[R.cty == "China"].groupby("mid").us_nb.mean()
print(S); print(G.round(3)); print(H.round(3))
# investor fixed-effects DiD: non-China investors present before (2015-17) and after; outcome = China co-investor share
from pyfixest import feols
pre_ids = set(R[(R.mid == 2016) & (R.reg != "China")].InvestorID)
panel = R[R.InvestorID.isin(pre_ids) & R.mid.isin([2016, 2020, 2023])].copy()
exp0 = panel[panel.mid == 2016].set_index("InvestorID").cn_nb
panel["exposed"] = panel.InvestorID.map(exp0 >= .1).astype(int)
panel["p1"] = panel.exposed * (panel.mid == 2020); panel["p2"] = panel.exposed * (panel.mid == 2023)
m = feols("cn_nb ~ p1 + p2 | InvestorID + mid", data=panel, vcov={"CRV1": "InvestorID"})
print(m.tidy().round(4))
panel["us_hq"] = (panel.cty == "United States").astype(int)
panel["u1"] = panel.us_hq * (panel.mid == 2020); panel["u2"] = panel.us_hq * (panel.mid == 2023)
m2 = feols("cn_nb ~ u1 + u2 | InvestorID + mid", data=panel[panel.exposed == 1], vcov={"CRV1": "InvestorID"})
print(m2.tidy().round(4))
FIRMS = ["Sequoia Capital", "HSG (Hong Kong)", "IDG Capital", "GGV Capital", "Qiming Venture Partners", "MPC (Beijing)",
         "Lightspeed Venture Partners", "Tencent Holdings", "SoftBank Investment Advisers", "Temasek Holdings",
         "Hillhouse Investment", "Kleiner Perkins", "Andreessen Horowitz", "Tiger Global Management", "Coatue Management",
         "Intel Capital", "Qualcomm Ventures", "GSR Ventures", "DCM", "Vertex Ventures", "Northern Light Venture Capital",
         "Matrix Partners", "Granite Asia", "Lightspeed China Partners", "500 Global", "ZhenFund", "Shunwei Capital"]
F = R[R.name.isin(FIRMS)][["name", "cty", "mid", "rounds", "cn_nb", "us_nb", "cn_share", "us_share"]]
print(F.pivot(index="name", columns="mid", values="cn_nb").round(2).to_string())
json.dump({"bridges": S.reset_index().to_dict("records"), "cn_nb_by_region": G.reset_index().to_dict("records"),
           "us_nb_cn_investors": H.to_dict(), "did_exposed": m.tidy().reset_index().to_dict("records"),
           "did_us_vs_other_exposed": m2.tidy().reset_index().to_dict("records"), "n_panel": int(panel.InvestorID.nunique()),
           "n_exposed": int(panel[panel.mid == 2016].exposed.sum()),
           "firms": F.to_dict("records")}, open("out/investor_level.json", "w"), default=float)
