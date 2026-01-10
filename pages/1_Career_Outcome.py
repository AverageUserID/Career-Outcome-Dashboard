import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ✅ Sets the browser tab + sidebar app name
st.set_page_config(page_title="Career Outcome", layout="wide")
st.sidebar.markdown("### Data source")
st.sidebar.markdown(
    "- Career outcomes / salary:: [https://www.naceweb.org/job-market/graduate-outcomes/first-destination/class-of-2024/first-destinations-for-the-college-class-of-2024-interactive-dashboard/")
# -----------------------------
# Load data
# -----------------------------
from pathlib import Path
DATA_PATH = Path(__file__).resolve().parent.parent / "outcome_data.csv"
df = pd.read_csv(DATA_PATH)

metrics = [
    "Total Graduate",
    "Mean Starting Salary",
    "Career Outcome Rate",
    "Employed Overall",
    "Standard Employment Full-time",
    "Continuing Education",
    "Seeking Employment",
    "Seeking Continuing Education",
    "Temp/Contract Employee",
]
pct_cols = metrics[2:]

# -----------------------------
# Type hygiene + NORMALIZATION (this fixes CIP 16 showing no data)
# -----------------------------
# year robust
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["year"]).copy()
df["year"] = df["year"].astype(int)

df["CIP"] = df["CIP"].astype(str).str.strip().str.strip("'\"")
df["CIP"] = df["CIP"].str.replace(r"\.0$", "", regex=True)

df["Degree Level"] = (
    df["Degree Level"].astype(str)
      .str.strip()
      .str.replace(r"\s+", " ", regex=True)
)

# numeric metrics
for c in metrics:
    df[c] = pd.to_numeric(df[c], errors="coerce")

st.title("Career Outcome")  # title inside the page

# -----------------------------
# Controls (sidebar)
# -----------------------------
with st.sidebar:
    cip_map = {
        "Teacher Education and Professional Development, Specific Subject Areas (13.13)": "13.13",
        "Foreign Languages, Literatures, and Linguistics (16)": "16",
    }
    cip_label = st.selectbox("CIP", list(cip_map.keys()))
    cip = cip_map[cip_label]

    degree = st.selectbox("Degree Level", sorted(df["Degree Level"].unique()))

    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    year_range = st.slider("Year Range", year_min, year_max, (max(year_min, 2019), year_max), step=1)

    metric = st.selectbox("Metric", metrics)

# -----------------------------
# Filter
# -----------------------------
start_year, end_year = year_range
filtered = (
    df[(df["CIP"] == str(cip)) &
       (df["Degree Level"] == str(degree)) &
       (df["year"].between(start_year, end_year))]
    .sort_values("year")
    .copy()
)

# -----------------------------
# Plot
# -----------------------------
st.subheader("Trend")

if filtered.empty or filtered[metric].dropna().empty:
    st.warning("No data for this selection.")

    # ✅ Debug helper (remove later): shows what CIPs Streamlit actually sees
    with st.expander("Debug: available CIPs / Degrees"):
        st.write("Unique CIPs in file:", sorted(df["CIP"].unique().tolist()))
        st.write("Unique Degree Levels in file:", sorted(df["Degree Level"].unique().tolist()))
else:
    y = filtered[metric].dropna()

    # Handle % scaling (0–1 vs 0–100)
    if metric in pct_cols and y.max() <= 1.5:
        filtered[metric] = filtered[metric] * 100
        y = filtered[metric].dropna()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(filtered["year"], filtered[metric], marker="o")
    ax.set_xlabel("Year")
    ax.set_xticks(filtered["year"].tolist())

    if metric in pct_cols:
        ax.set_ylabel(f"{metric} (%)")

        ymin, ymax = float(y.min()), float(y.max())
        pad = max(2, 0.10 * (ymax - ymin))
        ymin = max(0, ymin - pad)
        ymax = min(100, ymax + pad)

        if ymax - ymin < 8:
            mid = (ymin + ymax) / 2
            ymin = max(0, mid - 4)
            ymax = min(100, mid + 4)

        ax.set_ylim(ymin, ymax)

    elif metric == "Mean Starting Salary":
        ax.set_ylabel("Mean Starting Salary ($)")
    else:
        ax.set_ylabel(metric)

    ax.grid(True, alpha=0.3)
    st.pyplot(fig, use_container_width=True)

# -----------------------------
# Table
# -----------------------------
st.subheader("Filtered Data")
st.dataframe(filtered)
