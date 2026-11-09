import matplotlib as mpl, matplotlib.pyplot as plt
mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9,
    "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e6e6",
    "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.dpi": 150, "savefig.dpi": 300,
    "savefig.bbox": "tight", "legend.frameon": False, "lines.linewidth": 1.6})
C = {"United States": "#1f4e79", "China": "#c0392b", "Europe": "#2e8b57", "Asia ex. China": "#e08e0b",
     "Other": "#8c8c8c", "Hong Kong": "#d98880", "Singapore": "#2874a6", "United Kingdom": "#5b8c5a",
     "India": "#af7ac5", "Japan": "#d4ac0d", "Israel": "#48c9b0", "Russia": "#6e2c00"}
IND = ["AI & deep tech", "Software & IT", "Healthcare & life sci.", "Fintech", "Consumer", "Industrial & other"]
IC = dict(zip(IND, ["#1f4e79", "#5dade2", "#27ae60", "#8e44ad", "#e67e22", "#95a5a6"]))
EUROPE = {"United Kingdom", "France", "Germany", "Spain", "Netherlands", "Switzerland", "Sweden", "Italy", "Belgium",
          "Ireland", "Finland", "Denmark", "Norway", "Poland", "Austria", "Estonia", "Portugal", "Luxembourg",
          "Czech Republic", "Lithuania", "Latvia", "Greece", "Hungary", "Romania", "Ukraine", "Iceland", "Bulgaria",
          "Croatia", "Slovenia", "Slovakia", "Cyprus", "Malta", "Serbia", "Liechtenstein", "Monaco"}
ASIA = {"Japan", "South Korea", "India", "Singapore", "Hong Kong", "Taiwan", "Indonesia", "Vietnam", "Malaysia",
        "Thailand", "Philippines", "Pakistan", "Bangladesh", "United Arab Emirates", "Saudi Arabia", "Israel", "Turkey",
        "Qatar", "Kazakhstan", "Sri Lanka", "Cambodia", "Myanmar", "Nepal", "Bahrain", "Kuwait", "Oman", "Jordan"}
def region(c):
    if c == "United States": return "United States"
    if c == "China": return "China"
    if c in EUROPE: return "Europe"
    if c in ASIA: return "Asia ex. China"
    return "Other"
ISO = {"United States": "US", "China": "CN", "United Kingdom": "GB", "South Korea": "KR", "Japan": "JP", "India": "IN",
       "France": "FR", "Germany": "DE", "Singapore": "SG", "Canada": "CA", "Israel": "IL", "Australia": "AU", "Spain": "ES",
       "Netherlands": "NL", "Switzerland": "CH", "Sweden": "SE", "Hong Kong": "HK", "Brazil": "BR", "Italy": "IT",
       "United Arab Emirates": "AE", "Belgium": "BE", "Ireland": "IE", "Finland": "FI", "Denmark": "DK", "Indonesia": "ID",
       "Norway": "NO", "Mexico": "MX", "Poland": "PL", "Cayman Islands": "KY", "New Zealand": "NZ", "Austria": "AT",
       "Turkey": "TR", "Russia": "RU", "Vietnam": "VN", "Taiwan": "TW", "British Virgin Islands": "VG", "Nigeria": "NG",
       "Estonia": "EE", "Portugal": "PT", "Luxembourg": "LU", "Malaysia": "MY", "Thailand": "TH", "Chile": "CL",
       "Argentina": "AR", "Colombia": "CO", "South Africa": "ZA", "Kenya": "KE", "Egypt": "EG", "Saudi Arabia": "SA",
       "Philippines": "PH", "Czech Republic": "CZ", "Lithuania": "LT", "Ukraine": "UA", "Greece": "GR", "Pakistan": "PK"}
def save(fig, name):
    fig.savefig(f"/home/claude/vcnet/figs/{name}.pdf"); fig.savefig(f"/home/claude/vcnet/figs/{name}.png", dpi=160)
    plt.close(fig)
