import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import matplotlib.pyplot as plt

st.set_page_config(page_title="ALERTS", layout="wide")

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Load Data ---
df_display_alerts = pd.read_csv(os.path.join(BASE_DIR, "alerts_to_display.csv"))
df_display_alerts.columns = df_display_alerts.columns.str.strip()

# Ensure datetime columns
df_display_alerts["Date Of Event"] = pd.to_datetime(df_display_alerts["Date Of Event"], errors='coerce')
df_display_alerts["Date Of Alert"] = pd.to_datetime(df_display_alerts["Date Of Alert"], errors='coerce')

alert_details_dfs = {
    412: pd.read_csv(os.path.join(BASE_DIR, "signal_412.csv")),
    601: pd.read_csv(os.path.join(BASE_DIR, "signal_601.csv")),
    950: pd.read_csv(os.path.join(BASE_DIR, "signal_950.csv")),
    901: pd.read_csv(os.path.join(BASE_DIR, "signal_901.csv")),
    107: pd.read_csv(os.path.join(BASE_DIR, "signal_107.csv")),
    733: pd.read_csv(os.path.join(BASE_DIR, "signal_733.csv")),
}

# --- Default Dates ---
max_alert_date = df_display_alerts["Date Of Alert"].max()
default_from_alert = max_alert_date - pd.DateOffset(years=1)
max_event_date = df_display_alerts["Date Of Event"].max()
default_from_event = max_event_date - pd.DateOffset(years=1)

# --- Session State ---
if "df_filtered" not in st.session_state:
    st.session_state.df_filtered = df_display_alerts.copy()

# --- Sidebar Filters ---
st.title("ALERTS")
col1, col2, col3, col4 = st.columns(4)

# Convert Streamlit date_input to pandas Timestamps
from_date_event = pd.to_datetime(col1.date_input("From Date of Event", value=default_from_event))
to_date_event = pd.to_datetime(col2.date_input("To Date of Event", value=max_event_date))
from_date_alert = pd.to_datetime(col3.date_input("From Date of Alert", value=default_from_alert))
to_date_alert = pd.to_datetime(col4.date_input("To Date of Alert", value=max_alert_date))

# --- Portfolio Filter ---
portfolios = df_display_alerts["Portfolio"].dropna().unique().tolist()
selected_portfolios = st.multiselect("Portfolios", options=portfolios, default=portfolios)

# --- Signal Code Filter ---
signal_input = st.text_input("Signal Code (comma-separated, blank = all):", value="")
if signal_input.strip() == "":
    selected_signals = df_display_alerts["Signal Code"].dropna().unique().tolist()
else:
    try:
        selected_signals = [int(x.strip()) for x in signal_input.split(",") if x.strip()]
    except ValueError:
        st.error("Only numeric signal codes allowed.")
        selected_signals = df_display_alerts["Signal Code"].dropna().unique().tolist()

# --- Borrower ID Filter ---
borrower_input = st.text_input("Borrower ID (comma-separated, blank = all):", value="")
if borrower_input.strip() == "":
    selected_borrowers = df_display_alerts["Borrower Id"].dropna().unique().tolist()
else:
    selected_borrowers = [str(x).strip() for x in borrower_input.split(",") if x.strip()]

# --- Apply Filters ---
if st.button("Apply"):
    df_filtered = df_display_alerts.copy()
    df_filtered = df_filtered[
        (df_filtered["Date Of Event"].between(from_date_event, to_date_event)) &
        (df_filtered["Date Of Alert"].between(from_date_alert, to_date_alert)) &
        (df_filtered["Portfolio"].isin(selected_portfolios)) &
        (df_filtered["Signal Code"].isin(selected_signals)) &
        (df_filtered["Borrower Id"].astype(str).isin(selected_borrowers))
    ]
    st.session_state.df_filtered = df_filtered.copy()
    st.success(f"✅ Filters applied! Showing {len(df_filtered)} alerts.")

# --- Display Table ---
df_filtered = st.session_state.df_filtered.copy()
if df_filtered.empty:
    st.warning("No alerts found for the selected filters.")
else:
    gb = GridOptionsBuilder.from_dataframe(df_filtered)
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False)
    gridOptions = gb.build()
    gridOptions['paginationPageSize'] = 10

    grid_response = AgGrid(
        df_filtered,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=300,
        theme="material",
    )

    selected = grid_response["selected_rows"]
    if selected:
        row = selected[0]
        alert_id = row.get("Alert Id")
        signal_code = row.get("Signal Code")
        borrower_name = row.get("Borrower Name")
        st.markdown(f"### 🔽 Alert Details for **{borrower_name}** (Signal {signal_code})")
        df_signal = alert_details_dfs.get(signal_code)
        if df_signal is not None:
            drill_df = df_signal[df_signal["Alert Id"] == alert_id]
            if not drill_df.empty:
                st.dataframe(drill_df.T.rename(columns={drill_df.index[0]: ""}), use_container_width=True)
            else:
                st.info("No matching details found for this Alert ID in the signal dataset.")
        else:
            st.warning(f"No details found for Signal Code {signal_code}.")
    else:
        st.info("Click any row above to see drill-down details below 👆")

# --- Analytics Section ---
st.markdown("---")
if st.button("View Analytics"):
    df_filtered = st.session_state.df_filtered.copy()

    if df_filtered.empty:
        st.warning("No data to visualize.")
        st.stop()

    st.subheader("📊 Analytics Dashboard")

    # --- Total Alerts ---
    total_alerts = len(df_filtered)
    fig1, ax1 = plt.subplots(figsize=(3, 2))
    ax1.text(0.5, 0.5, f'Total Alerts\n{total_alerts}', fontsize=16, ha='center', va='center', weight='bold')
    ax1.axis('off')
    st.pyplot(fig1)

    # --- Prepare last 6 months data ---
    df_filtered["Date Of Alert"] = pd.to_datetime(df_filtered["Date Of Alert"])
    end_date = df_filtered["Date Of Alert"].max()
    start_date = end_date - pd.DateOffset(months=6)
    df_recent = df_filtered[(df_filtered["Date Of Alert"] >= start_date) & (df_filtered["Date Of Alert"] <= end_date)]

    # --- Alerts by Severity (Line Chart) ---
    severity_monthly = df_recent.groupby([df_recent['Date Of Alert'].dt.to_period('M'), 'Alert Severity']).size().unstack(fill_value=0)
    severity_monthly.index = severity_monthly.index.to_timestamp().strftime('%Y-%m')

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    for severity, color in zip(['Low', 'Medium', 'High'], ['#4CAF50', '#FFC107', '#F44336']):
        if severity in severity_monthly.columns:
            ax2.plot(severity_monthly.index, severity_monthly[severity], marker='o', linewidth=2, color=color, label=severity)
    ax2.set_title('Last 6 Months Alerts by Severity')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Number of Alerts')
    ax2.legend(title="Severity")
    ax2.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig2)

    # --- Alerts by Portfolio (Bar Chart per Portfolio) ---
    portfolio_counts = df_recent['Portfolio'].value_counts().sort_values(ascending=False)

    fig3, ax3 = plt.subplots(figsize=(12, 5))
    ax3.bar(portfolio_counts.index, portfolio_counts.values, color=plt.cm.tab20.colors)
    ax3.set_title('Total Alerts in Last 6 Months by Portfolio', fontsize=14)
    ax3.set_xlabel('Portfolio')
    ax3.set_ylabel('Number of Alerts')
    ax3.set_xticklabels(portfolio_counts.index, rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig3)

    # --- Optional CIBIL Score Analytics ---
    if "Cibil Score" in df_filtered.columns:
        st.subheader("CIBIL Score Distribution by Severity")
        summary = df_filtered.groupby("Alert Severity")["Cibil Score"].describe()[["mean", "min", "max"]]
        st.dataframe(summary.style.format("{:.1f}"))
