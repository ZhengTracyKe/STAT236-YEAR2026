import pandas as pd, numpy as np
PQ="../parquet/"  # run from analysis/tradewar_cn_us
VC_TYPES={"Seed Round","Early Stage VC","Later Stage VC"}
d=pd.read_parquet(PQ+"Deal.parquet",columns=["CompanyID","DealID","DealDate","DealSize","DealStatus","DealType","DealClass"])
d["DealDate"]=pd.to_datetime(d.DealDate,format="%m/%d/%Y",errors="coerce")
d["DealSize"]=pd.to_numeric(d.DealSize,errors="coerce")
r=d[(d.DealStatus=="Completed")&d.DealType.isin(VC_TYPES)&d.DealDate.dt.year.between(2010,2024)].copy()
print("rounds",len(r))
di=pd.read_parquet(PQ+"DealInvestorRelation.parquet",columns=["DealID","InvestorID","InvestorStatus","IsLeadInvestor","InvestorInvestmentAmount"])
di=di[di.DealID.isin(set(r.DealID))&~di.InvestorStatus.isin({"Failed Investor","Acquirer"})]
inv=pd.read_parquet(PQ+"Investor.parquet",columns=["InvestorID","InvestorName","PrimaryInvestorType","HQCountry"]).rename(columns={"HQCountry":"inv_cty"})
p=di.merge(inv,on="InvestorID",how="left")
n_all=p.groupby("DealID").InvestorID.nunique()
p=p[p.PrimaryInvestorType!="Angel (individual)"]
p=p.merge(r[["DealID","CompanyID","DealDate","DealSize","DealType"]],on="DealID")
amt=pd.to_numeric(p.InvestorInvestmentAmount,errors="coerce")
split=p.DealSize/p.DealID.map(n_all)
ok=(amt>0)&((amt<=1.05*p.DealSize)|(p.DealSize.isna()&(amt<1000)))
p["amount"]=amt.where(ok).fillna(split)
p["lead"]=p.IsLeadInvestor=="Yes"
c=pd.read_parquet(PQ+"Company.parquet",columns=["CompanyID","CompanyName","PrimaryIndustrySector","PrimaryIndustryGroup","HQCountry"]).rename(columns={"HQCountry":"st_cty"})
p=p.merge(c,on="CompanyID",how="left")
p["year"]=p.DealDate.dt.year; p["q"]=p.DealDate.dt.to_period("Q").astype(str)
p=p.drop(columns=["InvestorInvestmentAmount","InvestorStatus","IsLeadInvestor"])
print("participations",len(p), "missing inv cty",p.inv_cty.isna().mean(), "missing st cty",p.st_cty.isna().mean())
p.to_parquet("part.parquet")
# yearly edges investor-startup
e=p.groupby(["year","InvestorID","CompanyID"],as_index=False).agg(inv_cty=("inv_cty","first"),st_cty=("st_cty","first"),amount=("amount",lambda x:x.sum(min_count=1)),lead=("lead","max"),sector=("PrimaryIndustrySector","first"),itype=("PrimaryInvestorType","first"),q=("q","min"))
e.to_parquet("edges.parquet"); print("edges",len(e))
print(e.groupby("year").size())
