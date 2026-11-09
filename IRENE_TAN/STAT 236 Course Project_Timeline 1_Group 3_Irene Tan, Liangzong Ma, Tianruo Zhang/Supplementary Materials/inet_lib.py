import pandas as pd, numpy as np, scipy.sparse as sp, scipy.sparse.csgraph as cg
P_ = pd.read_parquet("/home/claude/vcnet/data/participations.parquet",
                     columns=["DealID", "InvestorID", "InvestorName", "inv_cty", "st_cty", "year", "q", "cross", "industry"])
NAME = P_.drop_duplicates("InvestorID").set_index("InvestorID")[["InvestorName", "inv_cty"]]
def coinvest(years=None, quarters=None, min_rounds=10, min_co=2, giant=True):
    z = P_
    if years is not None: z = z[z.year.between(*years)]
    if quarters is not None: z = z[z.q.between(*quarters)]
    z = z.drop_duplicates(["DealID", "InvestorID"])
    act = z.groupby("InvestorID").DealID.nunique()
    nodes = act[act >= min_rounds].index
    zz = z[z.InvestorID.isin(nodes)]
    idx = pd.Series(np.arange(len(nodes)), index=nodes); d = pd.Series(np.arange(zz.DealID.nunique()), index=zz.DealID.unique())
    B = sp.csr_matrix((np.ones(len(zz)), (idx[zz.InvestorID].values, d[zz.DealID].values)), shape=(len(nodes), len(d)))
    C = (B @ B.T).tocsr(); C.setdiag(0); C.eliminate_zeros()
    A = (C >= min_co).astype(float).tocsr()
    nodes = np.array(nodes)
    if giant:
        nc, lab = cg.connected_components(A); g = np.argmax(np.bincount(lab)); keep = lab == g
        A = A[keep][:, keep]; nodes = nodes[keep]; C = C[keep][:, keep]
    # investor attributes in window
    zi = z[z.InvestorID.isin(nodes)]
    att = pd.DataFrame(index=nodes)
    att["cty"] = NAME.inv_cty.reindex(nodes).values; att["name"] = NAME.InvestorName.reindex(nodes).values
    att["rounds"] = zi.groupby("InvestorID").DealID.nunique().reindex(nodes).values
    att["cb_share"] = zi.groupby("InvestorID").cross.mean().reindex(nodes).values
    att["cn_share"] = (zi.st_cty == "China").groupby(zi.InvestorID).mean().reindex(nodes).values
    att["us_share"] = (zi.st_cty == "United States").groupby(zi.InvestorID).mean().reindex(nodes).values
    return A, C, att

def coinvest_sub(years, startup_cty=("United States", "China"), min_rounds=10, min_co=2):
    """Co-investment network restricted to rounds of startups in `startup_cty` (the US-China 'Pacific' arena)."""
    global P_
    full = P_
    try:
        P_ = full[full.st_cty.isin(startup_cty)]
        return coinvest(years=years, min_rounds=min_rounds, min_co=min_co)
    finally:
        P_ = full
