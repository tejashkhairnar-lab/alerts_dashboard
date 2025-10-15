import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


# Compatibility fix for pandas >= 2.0
if not hasattr(pd.Series, "iteritems"):
    pd.Series.iteritems = pd.Series.items

st.set_page_config(page_title="Alerts Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Load CSVs ---
df_display_alerts = pd.read_csv(os.path.join(BASE_DIR, "alerts_to_display.csv"))
df_display_alerts.columns = df_display_alerts.columns.str.strip()
df_display_alerts["Date Of Event"] = pd.to_datetime(df_display_alerts["Date Of Event"], errors='coerce')
df_display_alerts["Date Of Alert"] = pd.to_datetime(df_display_alerts["Date Of Alert"], errors='coerce')

alert_details_dfs = {
    412: pd.read_csv(os.path.join(BASE_DIR, "signal_412.csv")),
    601: pd.read_csv(os.path.join(BASE_DIR, "signal_601.csv")),
    950: pd.read_csv(os.path.join(BASE_DIR, "signal_950.csv"))
}

st.title("🔍 Alerts Dashboard - Clickable Drill-Down")

# --- Date range filter ---
col1, col2, col3 = st.columns([1,1,0.5])
with col1:
    from_date = st.date_input("From Date of Event")
with col2:
    to_date = st.date_input("To Date of Event")
with col3:
    apply_filter = st.button("Apply")

df_filtered = df_display_alerts.copy()
if apply_filter:
    if from_date:
        df_filtered = df_filtered[df_filtered["Date Of Event"] >= pd.to_datetime(from_date)]
    if to_date:
        df_filtered = df_filtered[df_filtered["Date Of Event"] <= pd.to_datetime(to_date)]

# --- Main table with clickable row ---
st.markdown("### Generated Alerts")
gb = GridOptionsBuilder.from_dataframe(df_filtered)
gb.configure_selection("single", use_checkbox=False)
gb.configure_pagination(enabled=True)
gridOptions = gb.build()

grid_response = AgGrid(
    df_filtered,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    height=300,
    theme='streamlit',
)

selected = grid_response["selected_rows"]

# --- Drill-down ---
if selected:
    row = selected[0]
    alert_id = row["Alert Id"]
    signal_code = row["Signal Code"]
    borrower_name = row["Borrower Name"]

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
