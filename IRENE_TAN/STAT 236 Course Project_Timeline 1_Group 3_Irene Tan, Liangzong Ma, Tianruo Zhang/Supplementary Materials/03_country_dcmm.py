"""Country-level DCMM: the 'VC triangle' (Mixed-SCORE with SCORE+ normalisation, K=3) and 5-year rolling trajectories."""
import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json
from cnet_lib import flows, class_network, NODES
from netlib import mixed_score_plus, all_abs_eigs, match_columns, block_P, modularity, reg_laplacian
K = 3
X = flows((2010, 2024)); A, Z = class_network(X, sd=0.0)
names = ["Atlantic core", "Asia-Pacific", "Emerging & periphery"]; anch = ["United Kingdom", "Japan", "Brazil"]
ref = mixed_score_plus(A, K, seed=1)
order = [int(np.argmax(ref["Pi"][NODES.index(c)])) for c in anch]; assert len(set(order)) == 3
Pi0 = ref["Pi"][:, order]
res = {"nodes": NODES, "names": names, "eig_A": all_abs_eigs(A, 12).tolist(), "eig_L": all_abs_eigs(reg_laplacian(A), 12).tolist(),
       "Pi_full": Pi0.round(4).tolist(), "A_full": A.astype(int).tolist(), "strength_full": (X + X.T).sum(1).tolist(),
       "P_full": block_P(A, Pi0).round(3).tolist(), "edges_full": int(A.sum() / 2)}
wins = [(y, y + 4) for y in range(2010, 2021)]
traj, Ps = [], []
for a, b in wins:
    Xt = flows((a, b)); At, _ = class_network(Xt, sd=0.0); keep = At.sum(1) > 0
    r = mixed_score_plus(At[np.ix_(keep, keep)], K, seed=1)
    Pi = np.full((len(NODES), K), np.nan); perm = match_columns(Pi0[keep], r["Pi"]); Pi[keep] = r["Pi"][:, perm]
    Ps.append(block_P(At[np.ix_(keep, keep)], Pi[keep]).round(4).tolist())
    for i, c in enumerate(NODES):
        if keep[i]: traj.append(dict(window=f"{a}-{b}", mid=a + 2, country=c, **{names[k]: round(float(Pi[i, k]), 4) for k in range(K)},
                                     strength=float((Xt + Xt.T)[i].sum())))
T = pd.DataFrame(traj); T.to_csv("out/country_traj.csv", index=False)
res["windows"] = [f"{a}-{b}" for a, b in wins]; res["P_t"] = Ps; res["traj"] = traj
json.dump(res, open("out/country_dcmm.json", "w"))
print("edges", res["edges_full"], "eigA", np.round(res["eig_A"][:6], 2), "eigL", np.round(res["eig_L"][:6], 3))
print("P_full", np.round(res["P_full"], 3))
for c in ["United States", "China", "Hong Kong", "Singapore", "India", "Israel", "Russia", "United Arab Emirates", "Japan"]:
    print(c, Pi0[NODES.index(c)].round(2), "->", T[(T.country == c)].iloc[[0, -1]][names].round(2).values.tolist())
print("P_t Atl-Asia", [round(p[0][1], 3) for p in Ps])
