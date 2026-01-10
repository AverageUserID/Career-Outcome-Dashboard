import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

st.title("Degree Conferred")
st.sidebar.markdown("### Data source")
st.sidebar.markdown(
    "- IPEDS Completions (CIP): [NCES IPEDS Data Center](https://nces.ed.gov/ipeds/use-the-data")
# -----------------------------
# Load data
# -----------------------------
DATA_PATH = Path(__file__).resolve().parent.parent / "DegreeConferred.csv"
df = pd.read_csv(DATA_PATH)

# -----------------------------
# Required columns
# -----------------------------
required = {"year", "cip", "level", "total"}
missing = required - set(df.columns)
if missing:
    st.error(f"DegreeConferred.csv is missing columns: {sorted(missing)}")
    st.stop()

has_pct = "pct_change" in df.columns

# -----------------------------
# Type hygiene / normalization
# -----------------------------
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["year"]).copy()
df["year"] = df["year"].astype(int)

df["cip"] = (
    df["cip"].astype(str)
      .str.strip()
      .str.strip("'\"")
      .str.replace(r"\.0+$", "", regex=True)
)

df["level"] = (
    df["level"].astype(str)
      .str.strip()
      .str.replace(r"\s+", " ", regex=True)
)

df["total"] = pd.to_numeric(df["total"], errors="coerce")
if has_pct:
    df["pct_change"] = pd.to_numeric(df["pct_change"], errors="coerce")

# -----------------------------
# Sidebar filters
# -----------------------------
with st.sidebar:
    st.header("Filters")

    cip_options = sorted(df["cip"].unique().tolist())
    selected_cips = st.multiselect(
        "CIP code(s)",
        options=cip_options,
        default=cip_options[:1]
    )

    # Detect DH selection
    dh_selected = ("30.52" in selected_cips)

    # Degree options
    level_options = sorted(df["level"].unique().tolist())
    if dh_selected:
        level_options = [lvl for lvl in level_options if lvl in ["B.A.", "M.A."]]

    selected_levels = st.multiselect(
        "Degree level(s)",
        options=level_options,
        default=level_options[:1]
    )

    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    year_range = st.slider(
        "Year range",
        year_min,
        year_max,
        (year_min, year_max),
        step=1
    )

    # Plot mode
    if dh_selected:
        metric_mode = "Counts"
        st.caption("Digital Humanities (CIP 30.52): counts only (no % change).")
    else:
        metric_mode = st.radio(
            "Plot",
            options=["Counts"] + (["% Change"] if has_pct else []),
            index=0
        )

    show_points = st.checkbox("Show markers", value=True)

# -----------------------------
# Filter data
# -----------------------------
start_year, end_year = year_range

f = df[
    (df["cip"].isin(selected_cips) if selected_cips else True) &
    (df["level"].isin(selected_levels) if selected_levels else True) &
    (df["year"].between(start_year, end_year))
].copy()

# -----------------------------
# Plot
# -----------------------------
st.subheader("Trend plot")

if f.empty:
    st.warning("No data for the selected filters.")
else:
    y_col = "total" if metric_mode == "Counts" else "pct_change"
    y_label = "Grand total" if metric_mode == "Counts" else "% change"

    f["series"] = f["cip"] + " | " + f["level"]
    f = f.sort_values(["series", "year"])

    fig, ax = plt.subplots(figsize=(10, 5))
    marker = "o" if show_points else None

    for series, g in f.groupby("series"):
        ax.plot(g["year"], g[y_col], marker=marker, label=series)

    ax.set_xlabel("Year")
    ax.set_ylabel(y_label)
    ax.set_xticks(sorted(f["year"].unique().tolist()))
    ax.grid(True, alpha=0.3)

    if metric_mode == "% Change":
        ax.axhline(0, linewidth=1, alpha=0.4)

    ax.legend(title="CIP | Degree", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

# -----------------------------
# Table
# -----------------------------
st.subheader("Filtered data")
st.dataframe(f)
