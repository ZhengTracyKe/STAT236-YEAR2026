import pandas as pd, numpy as np
OFFSHORE = {"Cayman Islands", "British Virgin Islands", "Seychelles", "Bermuda", "Panama"}
e = pd.read_parquet("/home/claude/vcnet/data/edges.parquet"); X_ = e[e.cross]
_s = X_.groupby("inv_cty").size().add(X_.groupby("st_cty").size(), fill_value=0)
NODES = [c for c in _s[_s >= 1000].sort_values(ascending=False).index if c not in OFFSHORE]
def flows(years=None, quarters=None, industry=None):
    z = X_
    if years is not None: z = z[z.year.between(*years)]
    if quarters is not None: z = z[z.q.between(*quarters)]
    if industry is not None: z = z[z.industry.isin(industry if isinstance(industry, (list, set)) else [industry])]
    z = z[z.inv_cty.isin(NODES) & z.st_cty.isin(NODES)]
    M = pd.crosstab(z.inv_cty, z.st_cty).reindex(index=NODES, columns=NODES, fill_value=0)
    return M.values.astype(float)
def class_network(X, sd=1.0):
    """Lec 10 trade-network recipe: Y=(X+X')/2, Z = D^-1/2 Y D^-1/2, edge if Z > mean + sd*SD."""
    Y = (X + X.T) / 2; np.fill_diagonal(Y, 0)
    u = Y.sum(1); u[u == 0] = 1
    Z = Y / np.sqrt(np.outer(u, u))
    off = Z[~np.eye(len(Z), dtype=bool)]
    A = (Z > off.mean() + sd * off.std()).astype(float); np.fill_diagonal(A, 0)
    return A, Z
