import sys; sys.path.insert(0, "code")
import numpy as np, pandas as pd, json, matplotlib.pyplot as plt, matplotlib as mpl
from style import C, IC, IND, region, ISO, save
CD = json.load(open("out/country_dcmm.json")); ER = json.load(open("out/eras.json"))
CP = json.load(open("out/changepoints.json")); DC = json.load(open("out/dcmm_counterfactual.json"))
IL = json.load(open("out/investor_level.json")); SC = json.load(open("out/investor_scree.json"))
RC = {"United States": "#1f4e79", "China": "#c0392b", "Europe": "#2e8b57", "Asia ex. China": "#e08e0b", "Other": "#7f7f7f"}
# ---------------- Fig 8: scree plots
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.4))
axs[0].plot(range(1, 13), CD["eig_A"], "o-", ms=3, color="#1f4e79"); axs[0].set_title("(a) Country network, |λ| of A")
axs[1].plot(range(1, 15), ER["pre"]["lam"], "o-", ms=3, color="#1f4e79", label="2015–17")
axs[1].plot(range(1, 15), ER["post"]["lam"], "s-", ms=3, color="#c0392b", label="2022–24")
axs[1].axvline(ER["pre"]["K"], color="#1f4e79", ls=":", lw=1); axs[1].axvline(ER["post"]["K"], color="#c0392b", ls=":", lw=1)
axs[1].set_title("(b) Investor network, |λ| of $L_\\tau$"); axs[1].legend()
r_pre = np.array(ER["pre"]["lam"][:11]); r_post = np.array(ER["post"]["lam"][:11])
axs[2].plot(range(1, 11), r_pre[:-1] / r_pre[1:], "o-", ms=3, color="#1f4e79", label="2015–17")
axs[2].plot(range(1, 11), r_post[:-1] / r_post[1:], "s-", ms=3, color="#c0392b", label="2022–24")
axs[2].set_title("(c) Eigen-ratio $|λ_k|/|λ_{k+1}|$"); axs[2].set_xlabel("k")
for a in axs[:2]: a.set_xlabel("index k")
fig.tight_layout(); save(fig, "fig08_scree")
# ---------------- Fig 9: VC triangle (full period)
Pi = np.array(CD["Pi_full"]); nodes = CD["nodes"]; S = np.array(CD["strength_full"])
def tern(p): return p[..., 1] + p[..., 2] / 2, p[..., 2] * np.sqrt(3) / 2
x, y = tern(Pi)
fig, ax = plt.subplots(figsize=(6.0, 5.2))
tri = np.array([[0, 0], [1, 0], [.5, np.sqrt(3) / 2], [0, 0]]); ax.plot(tri[:, 0], tri[:, 1], color="#999", lw=1)
for c, xx, yy, s in zip(nodes, x, y, S):
    ax.scatter(xx, yy, s=12 + 600 * np.sqrt(s / S.max()), color=RC[region(c)], alpha=.75, edgecolor="white", lw=.6, zorder=3)
from adjustText import adjust_text
texts = [ax.text(xx, yy, ISO.get(c, c[:2]), fontsize=6.5, zorder=4) for c, xx, yy in zip(nodes, x, y) if c in set(nodes[:36])]
adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color="#888", lw=.4), expand=(1.3, 1.5))
for (vx, vy), t, ha in [((0, 0), "Atlantic core", "left"), ((1, 0), "Asia-Pacific", "right"), ((.5, .866), "Emerging & periphery", "center")]:
    ax.text(vx, vy + (-.06 if vy == 0 else .03), t, ha=ha, fontsize=9, fontweight="bold")
ax.set_xlim(-.08, 1.08); ax.set_ylim(-.1, .95); ax.axis("off"); ax.set_aspect("equal")
hs = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in RC.items()]
ax.legend(handles=hs, loc="upper left", fontsize=7.5)
save(fig, "fig09_triangle")
# ---------------- Fig 10: country membership trajectories (5-year windows), small multiples
T = pd.DataFrame(CD["traj"]); names = CD["names"]
sel = ["China", "Hong Kong", "Singapore", "India", "Israel", "United Arab Emirates", "Russia", "United States"]
vc = ["#1f4e79", "#e08e0b", "#7f7f7f"]
fig, axs = plt.subplots(2, 4, figsize=(7.6, 3.6), sharex=True, sharey=True)
for ax, c in zip(axs.ravel(), sel):
    s_ = T[T.country == c].sort_values("mid")
    ax.stackplot(s_.mid, s_[names].T.values * 100, colors=vc, alpha=.9, labels=names)
    ax.set_title(c, fontsize=8.5); ax.set_ylim(0, 100); ax.set_xlim(2012, 2022); ax.set_xticks([2012, 2017, 2022])
for a_ in axs[:, 0]: a_.set_ylabel("$\\hat\\pi_i$ (%)")
fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="lower center", ncol=3, bbox_to_anchor=(.5, -.04))
fig.tight_layout(rect=(0, .05, 1, 1)); save(fig, "fig10_trajectories")
# ---------------- Fig 11: investor co-investment network, two eras
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.8))
for ax, era, t in [(axs[0], "pre", "(a) 2015–2017"), (axs[1], "post", "(b) 2022–2024")]:
    E = ER[era]; nd = pd.DataFrame(E["nodes"]).set_index("id")
    rng = np.random.default_rng(0); ed = E["edges"]; ed = [ed[i] for i in rng.choice(len(ed), min(len(ed), 6000), replace=False)]
    segs = [[(nd.x[u], nd.y[u]), (nd.x[v], nd.y[v])] for u, v in ed]
    ax.add_collection(mpl.collections.LineCollection(segs, colors="#bbbbbb", linewidths=.15, alpha=.35, zorder=1))
    cc = [RC[region(c)] if isinstance(c, str) else "#7f7f7f" for c in nd.cty]
    ax.scatter(nd.x, nd.y, s=2 + 18 * np.sqrt(nd.deg / nd.deg.max()), c=cc, alpha=.85, lw=0, zorder=2)
    ax.set_title(t + f": n={E['n']:,}, K={E['K']}"); ax.axis("off")
hs = [plt.Line2D([], [], marker="o", ls="", color=v, label=k + " HQ") for k, v in RC.items()]
fig.legend(handles=hs, loc="lower center", ncol=5, bbox_to_anchor=(.5, -.02)); fig.tight_layout()
save(fig, "fig11_network")
# ---------------- Fig 12: China-pole membership distribution
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5))
bins = np.linspace(0, 1, 21)
for ax, key, t in [(axs[0], "piCN_US", "(a) US-HQ investors"), (axs[1], "piCN_CN", "(b) China-HQ investors")]:
    for era, col, lab in [("pre", "#1f4e79", "2015–17"), ("post", "#c0392b", "2022–24")]:
        v = np.array(ER[era][key]); ax.hist(v, bins=bins, weights=np.ones(len(v)) / len(v) * 100, histtype="step", lw=1.6, color=col, label=lab)
    ax.set_title(t); ax.set_xlabel("Mixed-SCORE weight on China community $\\hat\\pi_i(\\mathrm{CN})$"); ax.set_ylabel("% of investors")
    ax.set_yscale("log")
axs[0].legend(); fig.tight_layout(); save(fig, "fig12_pi_china")
# ---------------- Fig 13: change-point panel
Q = pd.DataFrame(CP["series_all"]); Q["t"] = [int(s[:4]) + (int(s[-1]) - .5) / 4 for s in Q.q]
panels = [("us_cn_aff", "US–China affinity (obs./exp.)"), ("cn_strength", "China's share of cross-border ties"),
          ("inv_P_cn_other", "Investor DCBM $\\hat P$(China, other)"), ("inv_P_us_cn", "Investor DCBM $\\hat P$(US, China)"),
          ("cross_share_exCN", "Cross-border share, ex. China"), ("lam2_exCN", "$\\lambda_2$ normalised network, ex. China")]
br_cn = CP["groups"]["china"]["bkps"]; br_gl = CP["groups"]["global_exCN"]["bkps"]
def qt(s): return int(s[:4]) + (int(s[-1]) - .5) / 4
fig, axs = plt.subplots(2, 3, figsize=(7.6, 4.2), sharex=True)
for ax, (f, t) in zip(axs.ravel(), panels):
    ax.plot(Q.t, Q[f], color="#1f4e79" if "exCN" not in f else "#2e8b57", lw=1.3); ax.set_title(t, fontsize=8.5)
    for b in br_cn: ax.axvline(qt(b), color="#c0392b", ls="--", lw=1)
    for b in br_gl: ax.axvline(qt(b), color="#2e8b57", ls=":", lw=1.2)
    ax.set_xticks(range(2011, 2025, 3))
fig.legend(handles=[plt.Line2D([], [], color="#c0392b", ls="--", label="Breaks, China-related features (" + ", ".join(br_cn) + ")"),
                    plt.Line2D([], [], color="#2e8b57", ls=":", label="Breaks, global features ex. China (" + ", ".join(br_gl) + ")")],
           loc="lower center", ncol=2, bbox_to_anchor=(.5, -.04))
fig.tight_layout(rect=(0, .04, 1, 1)); save(fig, "fig13_changepoints")
# ---------------- Fig 14: event study
es = pd.read_csv("out/es_pooled.csv")
fig, ax = plt.subplots(figsize=(6.2, 2.8))
for g, col, lab, off in [("uscn", "#c0392b", "US–China (both directions)", -.12), ("ruw", "#6e2c00", "Russia–West (both directions)", .12)]:
    s = es[es.group == g].sort_values("year"); s = pd.concat([s, pd.DataFrame([dict(group=g, year=2017, Estimate=0, **{"Std. Error": 0})])]).sort_values("year")
    ax.errorbar(s.year + off, s.Estimate, yerr=1.96 * s["Std. Error"], fmt="o-", ms=3, color=col, capsize=0, lw=1.2, label=lab)
ax.axhline(0, color="k", lw=.7); ax.axvline(2018.5, color="#c0392b", ls="--", lw=.8); ax.axvline(2021.5, color="#999", ls=":", lw=.8)
ax.set_ylabel("log points vs. 2017"); ax.set_xticks(range(2010, 2025, 2)); ax.legend(loc="lower left")
save(fig, "fig14_eventstudy")
# ---------------- Fig 15: DCMM decomposition: theta_t and pair deficits
th = pd.read_csv("out/theta_t.csv", index_col=0)
dist = pd.DataFrame(DC["dist"]).set_index("year")
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
for c, col in [("China", "#c0392b"), ("Hong Kong", "#d98880"), ("Singapore", "#2874a6"), ("India", "#af7ac5")]:
    axs[0].plot(th.index, th[c] * 100, "o-", ms=2.5, color=col, label=c)
axs[0].set_title("(a) Degree parameter $\\hat\\theta_{i,t}$ (share, %)"); axs[0].legend(); axs[0].axvline(2018.5, color="#c0392b", ls="--", lw=.8)
axs[1].fill_between(dist.index, dist["10%"], dist["90%"], color="#dddddd", label="Other pairs, 10–90th pct.")
axs[1].plot(dist.index, dist["50%"], color="#888", lw=1, label="Other pairs, median")
for k, col, lab in [("cn_us", "#c0392b", "China → US"), ("us_cn", "#1f4e79", "US → China"), ("ru_west", "#6e2c00", "Russia ↔ West")]:
    s = pd.Series(DC[k]); s.index = s.index.astype(int); axs[1].plot(s.index, s.values, "o-", ms=2.5, color=col, label=lab)
axs[1].axhline(1, color="k", lw=.6); axs[1].set_title("(b) Observed / predicted ties (pre-period = 1)"); axs[1].legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(.5, -.12), ncol=3)
for a in axs: a.set_xticks(range(2010, 2025, 4))
fig.tight_layout(); save(fig, "fig15_dcmm_decomp")
# ---------------- Fig 16: industry triple differences
ti = pd.read_csv("out/industry_did.csv")
lab = {"ai": "AI & deep tech", "consumer": "Consumer", "fintech": "Fintech", "healthcare": "Healthcare & life sci.", "industrial": "Industrial & other", "software": "Software & IT"}
ti["ind"] = ti.term.str.split("_").str[0].map(lab); ti["per"] = ti.term.str.split("_").str[1].map({"p1": "2019–21", "p2": "2022–24"})
fig, ax = plt.subplots(figsize=(5.4, 2.9)); order = [k for k in IND]
for per, col, off in [("2019–21", "#e08e0b", -.15), ("2022–24", "#c0392b", .15)]:
    s = ti[ti.per == per].set_index("ind").reindex(order)
    yy = np.arange(len(order)) + off
    ax.errorbar(s.Estimate, yy, xerr=1.96 * s["Std. Error"], fmt="o", ms=4, color=col, capsize=0, label=per)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.axvline(0, color="k", lw=.7); ax.invert_yaxis()
ax.set_xlabel("US–China × industry × period (PPML, log points vs. 2010–17)"); ax.legend()
save(fig, "fig16_industry_did")
# ---------------- Fig 17: bridges and named firms
B = pd.DataFrame(IL["bridges"]); G = pd.DataFrame(IL["cn_nb_by_region"]).set_index("mid")
F = pd.DataFrame(IL["firms"])
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.8))
axs[0].plot(B.mid, B.bridge_share * 100, "o-", ms=3, color="#1f4e79", label="Bridge investors (% of nodes)")
ax2 = axs[0].twinx(); ax2.plot(G.index, G["United States"] * 100, "s--", ms=3, color="#c0392b", label="US investors' China co-investor share (%)")
ax2.grid(False); ax2.spines["right"].set_visible(True)
h1, l1 = axs[0].get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); axs[0].legend(h1 + h2, l1 + l2, fontsize=6.5, loc="upper center", bbox_to_anchor=(.5, -.2), ncol=1)
axs[0].set_title("(a) US–China bridges (3-yr windows)"); axs[0].set_xlabel("window mid-year")
sel = {"Tencent Holdings": "#c0392b", "Temasek Holdings": "#2874a6", "Coatue Management": "#1f4e79", "Tiger Global Management": "#5dade2",
       "GSR Ventures": "#e08e0b", "IDG Capital": "#8e44ad", "SoftBank Investment Advisers": "#27ae60"}
for n_, col in sel.items():
    s = F[F.name == n_].sort_values("mid"); axs[1].plot(s.mid, s.cn_nb * 100, "o-", ms=2.5, color=col, label=n_.replace(" Management", "").replace(" Holdings", "").replace(" Investment Advisers", " VF"))
axs[1].set_title("(b) Share of co-investors HQ'd in China (%)"); axs[1].legend(fontsize=6.5, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2)); axs[1].set_xlabel("window mid-year")
fig.tight_layout(); save(fig, "fig17_bridges")
print("figs done")
