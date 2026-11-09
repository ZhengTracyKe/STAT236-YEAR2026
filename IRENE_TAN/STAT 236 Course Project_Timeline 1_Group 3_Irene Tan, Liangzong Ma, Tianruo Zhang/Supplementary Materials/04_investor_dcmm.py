"""Investor co-investment network: SCORE / Mixed-SCORE (DCMM) in rolling 3-year windows."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json, scipy.sparse as sp
from inet_lib import coinvest
from netlib import score_matrix, all_abs_eigs, block_P, modularity, mixed_score_plus, reg_laplacian
from style import region
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score as nmi
K = 6
wins = [(y, y + 2) for y in range(2010, 2023)]
TRACK = {"Sequoia Capital": None, "HongShan": None, "Sequoia Capital China": None, "IDG Capital": None, "GGV Capital": None,
         "Qiming Venture Partners": None, "Matrix Partners China": None, "MPC (Beijing)": None, "Lightspeed Venture Partners": None,
         "Lightspeed China Partners": None, "Tencent Holdings": None, "Tencent Investment": None, "SoftBank Investment Advisers": None,
         "Temasek Holdings": None, "Hillhouse Investment": None, "Qualcomm Ventures": None, "Intel Capital": None,
         "Vertex Ventures": None, "DCM": None, "Northern Light Venture Capital": None, "GSR Ventures": None, "Kleiner Perkins": None,
         "Andreessen Horowitz": None, "Accel": None, "500 Global": None, "Plug and Play Tech Center": None, "Coatue Management": None,
         "Tiger Global Management": None, "Alibaba Group": None, "Hony Capital": None, "Shunwei Capital": None, "ZhenFund": None,
         "Gaorong Ventures": None, "Source Code Capital": None, "Monolith Management": None, "Linear Capital": None}
rows, feats, comm_rows, eigs = [], [], [], []
for a, b in wins:
    A, C, att = coinvest((a, b))
    n = A.shape[0]
    ms = mixed_score_plus(A, K, seed=0)
    R, vals, Pi, lab = ms["R"], ms["vals"], ms["Pi"], ms["lab"]
    att["reg"] = att.cty.map(region); att["lab"] = lab
    isCN = (att.cty == "China").values; isUS = (att.cty == "United States").values
    # China community = cluster with the most China-HQ investors
    lab = Pi.argmax(1)
    cn_k = int(np.argmax(Pi[isCN].mean(0))) if isCN.sum() >= 10 else int(np.argmax([isCN[lab == k].sum() for k in range(K)]))
    us_k = int(np.argmax(Pi[isUS].mean(0)))
    P = block_P(A, Pi)
    # known-label (HQ) block connectivity, degree-corrected: B_kl/sqrt(B_kk B_ll)
    Z = np.column_stack([isUS, isCN, ~(isUS | isCN)]).astype(float)
    Bk = block_P(A, Z)
    deg = np.asarray(A.sum(1)).ravel()
    cn_edges = A[isCN].sum(); cn_to_non = A[isCN][:, ~isCN].sum()
    us_cn = A[isUS][:, isCN].sum()
    piCN = Pi[:, cn_k]
    bridge = (piCN > .2) & (piCN < .8)
    reg = att.reg.values
    feats.append(dict(window=f"{a}-{b}", mid=a + 1, n=n, edges=int(A.nnz // 2), n_cn=int(isCN.sum()), n_us=int(isUS.sum()),
                      lam=vals.tolist(), cn_comm_size=int((lab == cn_k).sum()),
                      cn_comm_purity=float(isCN[lab == cn_k].mean()), cn_in_cn_comm=float((lab[isCN] == cn_k).mean()),
                      P_cn_rest=float(np.mean([P[cn_k, l] for l in range(K) if l != cn_k])), P_cn_us=float(P[cn_k, us_k]),
                      Pknown_us_cn=float(Bk[0, 1]), Pknown_cn_other=float(Bk[1, 2]), Pknown_us_other=float(Bk[0, 2]),
                      ei_cn=float((cn_to_non - (cn_edges - cn_to_non)) / max(cn_edges, 1)),
                      us_cn_edge_share=float(us_cn / (A.sum() / 2)),
                      bridge_share=float(bridge.mean()), bridge_n=int(bridge.sum()),
                      bridge_nonCN=int((bridge & ~isCN).sum()),
                      piCN_mean_nonCN=float(piCN[~isCN].mean()), piCN_mean_US=float(piCN[isUS].mean()),
                      piCN_mean_CN=float(piCN[isCN].mean()) if isCN.any() else np.nan,
                      mod_region=float(modularity(A, pd.factorize(reg)[0])), mod_comm=float(modularity(A, lab)),
                      nmi_region=float(nmi(reg, lab)), nmi_cty=float(nmi(att.cty.values, lab))))
    eigs.append(all_abs_eigs(reg_laplacian(A), 15).tolist())
    for k in range(K):
        s = att[lab == k]
        comm_rows.append(dict(window=f"{a}-{b}", k=k, size=len(s), is_cn=k == cn_k, is_us=k == us_k,
                              top_cty=json.dumps(s.cty.value_counts(normalize=True).head(4).round(3).to_dict()),
                              top_inv=json.dumps(list(s.sort_values("rounds", ascending=False).name.head(6))),
                              P_row=json.dumps(np.round(P[k], 3).tolist())))
    att["piCN"] = piCN; att["window"] = f"{a}-{b}"; att["mid"] = a + 1; att["deg"] = deg
    att["piUS"] = Pi[:, us_k]
    rows.append(att.reset_index().rename(columns={"index": "InvestorID"}))
    print(a, b, n, "cn_k", cn_k, "purity %.2f" % feats[-1]["cn_comm_purity"], "P_cn_rest %.3f" % feats[-1]["P_cn_rest"],
          "Pknown_us_cn %.3f" % feats[-1]["Pknown_us_cn"], "bridge %.3f" % feats[-1]["bridge_share"], flush=True)
F = pd.DataFrame(feats); F.to_csv("out/investor_features.csv", index=False)
pd.DataFrame(comm_rows).to_csv("out/investor_communities.csv", index=False)
Rw = pd.concat(rows); Rw.to_parquet("out/investor_memberships.parquet")
json.dump({"eigs": eigs, "windows": [f"{a}-{b}" for a, b in wins]}, open("out/investor_scree.json", "w"))
