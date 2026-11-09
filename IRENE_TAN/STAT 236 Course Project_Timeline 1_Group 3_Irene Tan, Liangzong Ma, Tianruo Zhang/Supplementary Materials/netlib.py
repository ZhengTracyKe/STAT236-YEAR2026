"""Spectral community tools following STAT 236 Lec 9-10: SCORE, Mixed-SCORE (DCMM), vertex hunting."""
import numpy as np, itertools
import scipy.sparse as sp, scipy.sparse.linalg as sla
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans

def leading_eigs(A, K):
    """K leading eigenpairs of symmetric A by |eigenvalue|; first eigenvector made positive."""
    if sp.issparse(A) and A.shape[0] > 300:
        vals, vecs = sla.eigsh(A.astype(float), k=K, which="LM")
    else:
        A = A.toarray() if sp.issparse(A) else A
        vals, vecs = np.linalg.eigh(A)
    o = np.argsort(-np.abs(vals))[:K]
    vals, vecs = vals[o], vecs[:, o]
    if vecs[:, 0].sum() < 0: vecs[:, 0] *= -1
    return vals, vecs

def all_abs_eigs(A, m=20):
    if sp.issparse(A) and A.shape[0] > 300:
        vals = sla.eigsh(A.astype(float), k=min(m, A.shape[0] - 2), which="LM", return_eigenvectors=False)
    else:
        A = A.toarray() if sp.issparse(A) else A
        vals = np.linalg.eigvalsh(A)
    return np.sort(np.abs(vals))[::-1][:m]

def score_matrix(A, K, thresh=None):
    vals, vecs = leading_eigs(A, K)
    x1 = vecs[:, 0].copy(); x1[x1 <= 1e-12] = 1e-12
    R = vecs[:, 1:] / x1[:, None]
    T = np.log(A.shape[0]) if thresh is None else thresh
    return np.clip(R, -T, T), vals, vecs

def score(A, K, seed=0):
    R, vals, vecs = score_matrix(A, K)
    lab = KMeans(K, n_init=20, random_state=seed).fit_predict(R)
    return lab, R, vals

def simplex_volume(V):
    K = V.shape[0]
    M = np.vstack([np.ones(K), V.T])            # (K) x K when d=K-1
    return abs(np.linalg.det(M))

def vertex_hunt(R, K, L=None, seed=0):
    """Sketched vertex search: k-means denoising into L centers, then the K centers spanning the
    largest-volume simplex (N-FINDR criterion on the sketched points)."""
    n = R.shape[0]
    L = L or min(10 * K, max(K + 1, n // 3))
    cent = KMeans(L, n_init=10, random_state=seed).fit(R).cluster_centers_
    from math import comb
    if comb(L, K) > 150000:
        return spa(cent, K)
    best, bestv = None, -1
    for comb in itertools.combinations(range(L), K):
        v = simplex_volume(cent[list(comb)])
        if v > bestv: best, bestv = comb, v
    return cent[list(best)]

def barycentric(R, V):
    K = V.shape[0]
    M = np.vstack([np.ones(K), V.T])
    W = np.linalg.lstsq(M, np.vstack([np.ones(R.shape[0]), R.T]), rcond=None)[0].T
    W = np.clip(W, 0, None); W = W / W.sum(1, keepdims=True)
    return W

def mixed_score(A, K, seed=0, L=None):
    R, vals, vecs = score_matrix(A, K)
    V = vertex_hunt(R, K, L=L, seed=seed)
    W = barycentric(R, V)
    b1 = np.array([(vals[0] + V[k] @ np.diag(vals[1:]) @ V[k]) for k in range(K)])
    b1 = np.where(b1 > 0, b1, np.nan) ** -0.5
    b1 = np.nan_to_num(b1, nan=np.nanmean(b1))
    Pi = W / b1[None, :]; Pi = Pi / Pi.sum(1, keepdims=True)
    return dict(Pi=Pi, R=R, V=V, W=W, vals=vals, b1=b1)

def match_columns(Pi_ref, Pi):
    """Permute columns of Pi to best match Pi_ref (Hungarian on correlation over common rows)."""
    K = Pi.shape[1]
    C = np.array([[np.corrcoef(Pi_ref[:, a], Pi[:, b])[0, 1] for b in range(K)] for a in range(K)])
    r, c = linear_sum_assignment(-np.nan_to_num(C))
    return c

def block_P(A, Pi, theta=None):
    """Moment estimate of the DCMM block matrix: B = Pi' A Pi (expected-edge mass between communities),
    normalised to unit diagonal, P_kl = B_kl / sqrt(B_kk B_ll)."""
    A = A.toarray() if sp.issparse(A) else A
    B = Pi.T @ A @ Pi
    d = np.sqrt(np.clip(np.diag(B), 1e-12, None))
    return B / np.outer(d, d)

def modularity(A, lab):
    A = A.toarray() if sp.issparse(A) else A
    m2 = A.sum(); k = A.sum(1)
    Q = 0.0
    for c in np.unique(lab):
        idx = lab == c
        Q += A[np.ix_(idx, idx)].sum() / m2 - (k[idx].sum() / m2) ** 2
    return Q

def spa(X, K):
    """Successive projection algorithm (Araujo et al. 2001) on rows of [1, X]."""
    Y = np.hstack([np.ones((X.shape[0], 1)), X]).astype(float)
    idx = []
    for _ in range(K):
        j = int(np.argmax((Y ** 2).sum(1))); idx.append(j)
        u = Y[j] / np.linalg.norm(Y[j]); Y = Y - np.outer(Y @ u, u)
    return X[idx]

def reg_laplacian(A):
    """SCORE+ pre-PCA normalisation (Lec 9): L = H^-1/2 A H^-1/2, H = D + mean(d) I."""
    d = np.asarray(A.sum(1)).ravel(); h = 1 / np.sqrt(d + d.mean())
    return (sp.diags(h) @ A @ sp.diags(h)) if sp.issparse(A) else (A * np.outer(h, h))

def svs_vertices(R, K, seed=0):
    """Sketched vertex search (Lec 10): KNN denoising, k-means sketch (L=10K), SPA on sketch."""
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=max(5, len(R) // 50)).fit(R); _, ix = nn.kneighbors(R)
    Rd = R[ix].mean(1)
    cent = KMeans(min(10 * K, len(R) // 3), n_init=5, random_state=seed).fit(Rd).cluster_centers_
    return spa(cent, K)

def mixed_score_plus(A, K, seed=0):
    M = reg_laplacian(A)
    R, vals, vecs = score_matrix(M, K)
    V = svs_vertices(R, K, seed)
    W = barycentric(R, V)
    b1 = np.array([vals[0] + V[k] @ np.diag(vals[1:]) @ V[k] for k in range(K)])
    b1 = np.where(b1 > 0, b1, np.nan) ** -0.5; b1 = np.nan_to_num(b1, nan=np.nanmean(b1))
    Pi = W / b1; Pi = Pi / Pi.sum(1, keepdims=True)
    lab = KMeans(K, n_init=20, random_state=seed).fit_predict(R)
    return dict(Pi=Pi, R=R, V=V, vals=vals, lab=lab)
