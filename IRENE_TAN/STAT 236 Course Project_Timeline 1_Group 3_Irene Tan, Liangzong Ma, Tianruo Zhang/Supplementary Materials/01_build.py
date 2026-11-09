"""Build the analysis panel: investor->startup participations in completed VC rounds, 2010-2024,
with investor/startup HQ countries and startup industry groups."""
import pandas as pd, numpy as np
PQ = "/mnt/user-data/uploads/PitchBook/analysis/parquet/"
p = pd.read_parquet("/home/claude/tw/part.parquet")          # built by build.py (same rules as test #1)
c = pd.read_parquet(PQ + "Company.parquet", columns=["CompanyID", "Verticals", "YearFounded"])
p = p.merge(c, on="CompanyID", how="left")
p["Verticals"] = p.Verticals.fillna("")
g, v, s = p.PrimaryIndustryGroup, p.Verticals, p.PrimaryIndustrySector
crit = g.isin(["Semiconductors", "Computer Hardware", "Communications and Networking"]) | \
       v.str.contains("Artificial Intelligence|Quantum Computing|Robotics|Autonomous", regex=True)
health = s.eq("Healthcare")
fin = s.eq("Financial Services") | v.str.contains("FinTech")
cons = s.eq("Consumer Products and Services (B2C)") | v.str.contains("EdTech") | g.eq("Media")
soft = g.isin(["Software", "IT Services"])
p["industry"] = np.select([crit, health, fin, cons, soft],
                          ["AI & deep tech", "Healthcare & life sci.", "Fintech", "Consumer", "Software & IT"],
                          "Industrial & other")
p = p.dropna(subset=["inv_cty", "st_cty"])
p["cross"] = (p.inv_cty != p.st_cty)
# country sample: 40 most active countries (as investor HQ + startup HQ, all years)
act = p.groupby("inv_cty").size().add(p.groupby("st_cty").size(), fill_value=0).sort_values(ascending=False)
top = list(act.index[:40])
pd.Series(top).to_csv("data/countries_top40.csv", index=False, header=["country"])
keep = ["DealID", "InvestorID", "InvestorName", "PrimaryInvestorType", "inv_cty", "CompanyID", "CompanyName",
        "st_cty", "DealDate", "year", "q", "DealType", "DealSize", "amount", "lead", "industry",
        "PrimaryIndustryGroup", "cross"]
p[keep].to_parquet("data/participations.parquet")
print(len(p), "participations;", p.DealID.nunique(), "rounds;", p.InvestorID.nunique(), "investors;",
      p.CompanyID.nunique(), "startups")
print("cross-border share", p.cross.mean().round(3))
print(p.industry.value_counts(normalize=True).round(3))
print(top)
