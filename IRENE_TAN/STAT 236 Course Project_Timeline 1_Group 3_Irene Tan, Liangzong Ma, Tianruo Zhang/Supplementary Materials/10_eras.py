"""Benchmark eras: investor communities (Mixed-SCORE with SCORE+ normalisation), K by eigen-gap, layouts for plots."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json, networkx as nx
from inet_lib import coinvest, P_
from netlib import mixed_score_plus, reg_laplacian, all_abs_eigs, block_P, modularity
from style import region, IND
from sklearn.metrics import normalized_mutual_info_score as nmi
ERAS = {"pre": (2015, 2017), "post": (2022, 2024)}
out = {}
for era, (a, b) in ERAS.items():
    A, C, att = coinvest((a, b))
    lam = all_abs_eigs(reg_laplacian(A), 14)
    ratios = lam[3:10] / lam[4:11]; K = int(np.argmax(ratios) + 4)
    ms = mixed_score_plus(A, K, seed=0); Pi = ms["Pi"]; lab = Pi.argmax(1)
    isCN = att.cty.eq("China").values
    cn_k = int(np.argmax([isCN[lab == k].sum() for k in range(K)]))
    P = block_P(A, Pi)
    z = P_[P_.year.between(a, b) & P_.InvestorID.isin(att.index)]
    indmix = pd.crosstab(z.InvestorID, z.industry, normalize="index").reindex(att.index).fillna(0)
    deg = np.asarray(A.sum(1)).ravel(); att["deg"] = deg; att["lab"] = lab; att["piCN"] = Pi[:, cn_k]
    comms = []
    for k in range(K):
        s = att[lab == k]; im = indmix.loc[s.index].mean()
        cc = s.cty.value_counts(normalize=True)
        comms.append(dict(k=k, size=int(len(s)), china=k == cn_k, top_cty=cc.head(3).round(3).to_dict(),
                          top_inv=list(s.sort_values("deg", ascending=False).name.head(5)), industry=im.round(3).to_dict(),
                          within=float(A[np.ix_(lab == k, lab == k)].sum() / max(A[lab == k].sum(), 1))))
    # layout of the top-degree core for plotting
    top = np.argsort(-deg)[:1600]
    G = nx.from_scipy_sparse_array(A[top][:, top])
    giant = max(nx.connected_components(G), key=len); G = G.subgraph(giant)
    pos = nx.spring_layout(G, k=0.6 / np.sqrt(len(G)), iterations=80, seed=3)
    nodes = [dict(id=int(top[u]), x=float(pos[u][0]), y=float(pos[u][1]), c=int(lab[top[u]]), cty=att.cty.iloc[top[u]],
                  name=att.name.iloc[top[u]], deg=int(deg[top[u]]), piCN=round(float(Pi[top[u], cn_k]), 3)) for u in G.nodes]
    edges = [(int(top[u]), int(top[v])) for u, v in G.edges]
    out[era] = dict(window=f"{a}-{b}", n=int(A.shape[0]), m=int(A.nnz // 2), K=K, lam=lam.tolist(), cn_k=cn_k,
                    P=P.round(3).tolist(), comms=comms, nmi_cty=float(nmi(att.cty, lab)),
                    nmi_reg=float(nmi(att.cty.map(region), lab)), mod=float(modularity(A, lab)),
                    piCN_nonCN=att.loc[~isCN, "piCN"].round(3).tolist(), piCN_US=att.loc[att.cty.eq("United States"), "piCN"].round(3).tolist(),
                    piCN_CN=att.loc[isCN, "piCN"].round(3).tolist(), nodes=nodes, edges=edges)
    print(era, a, b, "n", A.shape[0], "K", K, "lam", np.round(lam[:10], 3), "cn purity", round(isCN[lab == cn_k].mean(), 3),
          "P(cn, others)", np.round(np.delete(P[cn_k], cn_k), 3), flush=True)
    for c in comms: print("   ", c["k"], c["size"], c["top_cty"], c["top_inv"][:3], "within %.2f" % c["within"])
json.dump(out, open("out/eras.json", "w"))
