import sys; sys.path.insert(0, "code")
import pandas as pd, numpy as np, matplotlib.pyplot as plt, json
from style import C, IND, IC, region, ISO, save
p = pd.read_parquet("data/participations.parquet")
# edge = investor-startup-year (collapse multiple rounds within a year)
e = (p.groupby(["year", "InvestorID", "CompanyID"], as_index=False)
       .agg(inv_cty=("inv_cty", "first"), st_cty=("st_cty", "first"), industry=("industry", "first"),
            amount=("amount", lambda x: x.sum(min_count=1)), q=("q", "min"), itype=("PrimaryInvestorType", "first")))
e["cross"] = e.inv_cty != e.st_cty
e["ri"] = e.inv_cty.map(region); e["rs"] = e.st_cty.map(region)
e.to_parquet("data/edges.parquet")
out = {}
# ---------- Table 1: summary by period
per = pd.cut(e.year, [2009, 2013, 2017, 2021, 2024], labels=["2010-13", "2014-17", "2018-21", "2022-24"])
t1 = e.assign(per=per).groupby("per", observed=True).agg(
    ties=("CompanyID", "size"), investors=("InvestorID", "nunique"), startups=("CompanyID", "nunique"),
    cross_share=("cross", "mean"), inv_countries=("inv_cty", "nunique"), st_countries=("st_cty", "nunique"))
r = p.assign(per=pd.cut(p.year, [2009, 2013, 2017, 2021, 2024], labels=t1.index)).groupby("per", observed=True).DealID.nunique()
t1.insert(0, "rounds", r); print(t1); t1.to_csv("out/table1_summary.csv")
# ---------- Fig 1: activity and cross-border share
y = e.groupby("year").agg(ties=("CompanyID", "size"), cross=("cross", "sum"))
y["share"] = y.cross / y.ties
fig, ax = plt.subplots(figsize=(6.4, 2.8))
ax.bar(y.index, y.ties / 1e3, color="#c9d6e3", label="All investor→startup ties")
ax.bar(y.index, y.cross / 1e3, color="#1f4e79", label="Cross-border ties")
ax.set_ylabel("Ties (thousands)"); ax.set_xticks(range(2010, 2025, 2))
ax2 = ax.twinx(); ax2.plot(y.index, y.share * 100, color="#c0392b", marker="o", ms=3, label="Cross-border share (right)")
ax2.set_ylabel("Cross-border share (%)", color="#c0392b"); ax2.grid(False); ax2.spines["right"].set_visible(True)
ax2.set_ylim(15, 40)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left")
save(fig, "fig01_activity")
out["yearly"] = y.reset_index().to_dict("records")
# ---------- Fig 2: composition of cross-border ties by region pair
x = e[e.cross].copy()
def pair(r):
    a, b = r.ri, r.rs
    if "China" in (a, b) and "United States" in (a, b): return "US–China"
    if "China" in (a, b): return "China–other"
    if a == "United States": return "US → rest of world"
    if b == "United States": return "Rest of world → US"
    if a == b == "Europe": return "Within Europe"
    if a == b == "Asia ex. China": return "Within Asia ex. China"
    return "Other cross-border"
x["pair"] = [pair(r) for r in x[["ri", "rs"]].itertuples()]
comp = pd.crosstab(x.year, x.pair, normalize="index")
order = ["Rest of world → US", "US → rest of world", "Within Europe", "Within Asia ex. China", "US–China", "China–other", "Other cross-border"]
comp = comp[order]
cols = ["#1f4e79", "#5dade2", "#2e8b57", "#e08e0b", "#c0392b", "#f1948a", "#bdbdbd"]
fig, ax = plt.subplots(figsize=(6.4, 3))
ax.stackplot(comp.index, (comp.T * 100).values, labels=order, colors=cols, alpha=.92)
ax.set_ylim(0, 100); ax.set_xlim(2010, 2024); ax.set_ylabel("Share of cross-border ties (%)")
ax.legend(loc="center left", bbox_to_anchor=(1.0, .5)); ax.set_xticks(range(2010, 2025, 2))
save(fig, "fig02_composition"); comp.to_csv("out/fig02_composition.csv")
out["composition"] = comp.reset_index().to_dict("records")
# ---------- Fig 3: US-China ties in both directions, counts and dollars (index 2017 = 100)
def dyad(i, j):
    d = e[(e.inv_cty == i) & (e.st_cty == j)].groupby("year").agg(n=("CompanyID", "size"), usd=("amount", "sum"))
    return d
uc, cu = dyad("United States", "China"), dyad("China", "United States")
allx = x.groupby("year").size()
fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.6))
axs[0].plot(cu.index, cu.n, color=C["China"], marker="o", ms=3, label="China → US")
axs[0].plot(uc.index, uc.n, color=C["United States"], marker="s", ms=3, label="US → China")
axs[0].set_title("(a) Investor→startup ties"); axs[0].legend(); axs[0].set_xticks(range(2010, 2025, 4))
for d, col, lab in [(cu, C["China"], "China → US"), (uc, C["United States"], "US → China")]:
    axs[1].plot(d.index, d.n / allx.reindex(d.index) * 100, color=col, marker="o", ms=3, label=lab)
axs[1].set_title("(b) Share of all cross-border ties (%)"); axs[1].set_xticks(range(2010, 2025, 4))
for a in axs: a.axvspan(2021.5, 2024.5, color="#f2f2f2", zorder=0)
save(fig, "fig03_uschina")
out["uschina"] = {"cn_us": cu.reset_index().to_dict("records"), "us_cn": uc.reset_index().to_dict("records")}
# ---------- Fig 4: industry trends: cross-border share by industry, industry mix of US-China ties
ind_cb = e.groupby(["year", "industry"]).cross.mean().unstack()[IND]
uc_all = e[((e.inv_cty == "United States") & (e.st_cty == "China")) | ((e.inv_cty == "China") & (e.st_cty == "United States"))]
mix = pd.crosstab(uc_all.year, uc_all.industry, normalize="index")[IND]
cbmix = pd.crosstab(x.year, x.industry, normalize="index")[IND]
fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.8))
for k in IND: axs[0].plot(ind_cb.index, ind_cb[k] * 100, color=IC[k], label=k)
axs[0].set_title("(a) Cross-border share (%)"); axs[0].set_xticks(range(2010, 2025, 4))
axs[1].stackplot(cbmix.index, (cbmix.T * 100).values, colors=[IC[k] for k in IND])
axs[1].set_title("(b) Mix of all cross-border ties"); axs[1].set_ylim(0, 100); axs[1].set_xlim(2010, 2024); axs[1].set_xticks(range(2010, 2025, 4))
axs[2].stackplot(mix.index, (mix.T * 100).values, colors=[IC[k] for k in IND], labels=IND)
axs[2].set_title("(c) Mix of US–China ties"); axs[2].set_ylim(0, 100); axs[2].set_xlim(2010, 2024); axs[2].set_xticks(range(2010, 2025, 4))
fig.legend(*axs[2].get_legend_handles_labels(), loc="lower center", ncol=6, bbox_to_anchor=(.5, -.1))
fig.tight_layout(w_pad=1.5); save(fig, "fig04_industry")
ind_cb.to_csv("out/fig04_ind_cbshare.csv"); mix.to_csv("out/fig04_uschina_mix.csv"); cbmix.to_csv("out/fig04_cb_mix.csv")
out["ind_cb"] = ind_cb.reset_index().to_dict("records"); out["uschina_mix"] = mix.reset_index().to_dict("records")
# ---------- Fig 5: country x industry RCA of inbound foreign ties (2016-24)
top = pd.read_csv("data/countries_top40.csv").country.tolist()
top = [c for c in top if c not in ("Cayman Islands", "British Virgin Islands")][:24]
xi = x[x.st_cty.isin(top) & x.year.between(2016, 2024)]
ct = pd.crosstab(xi.st_cty, xi.industry)[IND]
rca = (ct.div(ct.sum(1), axis=0)) / (ct.sum(0) / ct.values.sum())
rca = rca.loc[ct.sum(1).sort_values(ascending=False).index]
fig, ax = plt.subplots(figsize=(5.2, 5.6))
im = ax.imshow(np.log2(rca.values), cmap="RdBu_r", vmin=-1.5, vmax=1.5, aspect="auto")
ax.set_xticks(range(len(IND))); ax.set_xticklabels(IND, rotation=35, ha="right")
ax.set_yticks(range(len(rca))); ax.set_yticklabels(rca.index); ax.grid(False)
for i in range(rca.shape[0]):
    for j in range(rca.shape[1]): ax.text(j, i, f"{rca.values[i, j]:.1f}", ha="center", va="center", fontsize=6.5, color="white" if abs(np.log2(rca.values[i, j])) > 0.9 else "black")
cb = fig.colorbar(im, ax=ax, shrink=.6); cb.set_label("log$_2$ RCA of inbound foreign VC ties")
save(fig, "fig05_rca"); rca.to_csv("out/fig05_rca.csv")
out["rca"] = {"rows": list(rca.index), "cols": IND, "values": rca.round(3).values.tolist()}
# ---------- Fig 6: country cross-border inflow/outflow change, 2015-17 vs 2022-24
tops = top[:20]
def flows(a, b):
    z = x[x.year.between(a, b)]
    return z.groupby("inv_cty").size().reindex(tops).fillna(0) / (b - a + 1), z.groupby("st_cty").size().reindex(tops).fillna(0) / (b - a + 1)
o1, i1 = flows(2015, 2017); o2, i2 = flows(2022, 2024)
f6 = pd.DataFrame({"out_1517": o1, "in_1517": i1, "out_2224": o2, "in_2224": i2})
f6["out_g"] = np.log(f6.out_2224 / f6.out_1517); f6["in_g"] = np.log(f6.in_2224 / f6.in_1517)
f6 = f6.sort_values("in_g")
fig, ax = plt.subplots(figsize=(5.2, 4.4))
yy = np.arange(len(f6))
ax.barh(yy - .18, f6.in_g, height=.36, color="#1f4e79", label="Inbound (foreign investors in country's startups)")
ax.barh(yy + .18, f6.out_g, height=.36, color="#e08e0b", label="Outbound (country's investors abroad)")
ax.set_yticks(yy); ax.set_yticklabels(f6.index); ax.axvline(0, color="k", lw=.8)
ax.set_xlabel("log change in annual cross-border ties, 2022–24 vs. 2015–17"); ax.legend(loc="lower right")
save(fig, "fig06_country_change"); f6.to_csv("out/fig06_country_change.csv")
out["country_change"] = f6.reset_index().rename(columns={"index": "country"}).round(3).to_dict("records")
# ---------- Fig 7: degree heterogeneity
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.4))
w = e[e.year.between(2016, 2018)]
for a, s, t in [(axs[0], w.groupby("InvestorID").size(), "(a) Investor out-degree"),
                (axs[1], w.groupby("CompanyID").size(), "(b) Startup in-degree"),
                (axs[2], w[w.cross].groupby("inv_cty").size().add(w[w.cross].groupby("st_cty").size(), fill_value=0), "(c) Country cross-border strength")]:
    v = np.sort(s.values)[::-1]; ccdf = np.arange(1, len(v) + 1) / len(v)
    a.loglog(v, ccdf, ".", ms=2, color="#1f4e79"); a.set_title(t); a.set_xlabel("degree $d$"); a.set_ylabel("P(D ≥ d)")
fig.tight_layout(); save(fig, "fig07_degrees")
json.dump(out, open("out/descriptives.json", "w"), default=float)
print(y.round(3)); print(comp.round(3).loc[[2010, 2017, 2018, 2021, 2024]]); print(f6.round(2))
