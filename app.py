import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# --- Load CSV ---
df_display_alerts = pd.read_csv("alerts_to_display.csv")
df_display_alerts.columns = df_display_alerts.columns.str.strip()

# Ensure datetime columns
df_display_alerts["Date Of Event"] = pd.to_datetime(df_display_alerts["Date Of Event"], errors='coerce')
df_display_alerts["Date Of Alert"] = pd.to_datetime(df_display_alerts["Date Of Alert"], errors='coerce')

# Example alert_details_dfs dictionary
alert_details_dfs = {
    412: pd.read_csv("signal_412.csv"),
    601: pd.read_csv("signal_601.csv"),
    950: pd.read_csv("signal_950.csv")
}

# --- Streamlit UI ---
st.title("Alerts")

#st.markdown("### Filter Alerts by Date of Event")

# --- Date Range Inputs and Apply Button in same row ---
col1, col2, col3 = st.columns([1,1,0.5])  # adjust width ratio if needed
with col1:
    from_date = st.date_input("From Date of Event", value=None)
with col2:
    to_date = st.date_input("To Date of Event", value=None)
with col3:
    apply_filter = st.button("Apply")

# --- Apply Button ---

if apply_filter:
    df_filtered = df_display_alerts.copy()
    if from_date:
        df_filtered = df_filtered[df_filtered["Date Of Event"] >= pd.to_datetime(from_date)]
    if to_date:
        df_filtered = df_filtered[df_filtered["Date Of Event"] <= pd.to_datetime(to_date)]
else:
    df_filtered = df_display_alerts.copy()  # show all by default

st.markdown("### Generated Alerts")


gb = GridOptionsBuilder.from_dataframe(df_filtered)
gb.configure_selection("single", use_checkbox=False)
gb.configure_pagination(enabled=True)
gb.configure_grid_options(domLayout='normal')
gridOptions = gb.build()

# Show grid and capture user selection
grid_response = AgGrid(
    df_filtered,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    height=300,
    theme='material',
)

selected = grid_response["selected_rows"]

# --- Drill-down section ---
if selected:
    selected_row = selected[0]
    
    alert_id = selected_row.get("Alert Id", None)
    signal_code = selected_row.get("Signal Code", None)
    borrower_name = selected_row.get("Borrower Name", None)
    signal_code = selected_row.get("Signal Code", None)

    if alert_id is None or signal_code is None:
        st.error("Selected row does not have valid Alert Id or Signal Code.")
    else:
        st.markdown(f"### 🔽 Alert Details |  **{borrower_name}** (Signal Code {signal_code})")
        
        df_signal = alert_details_dfs.get(signal_code)
        
        if df_signal is not None:
            drill_df = df_signal[df_signal["Alert Id"] == alert_id]
            
            if not drill_df.empty:
                # Transpose for vertical display
                st.dataframe(
                    drill_df.T.rename(columns={drill_df.index[0]: ""}),
                    use_container_width=True
                )
            else:
                st.info("No matching details found for this Alert ID in the signal dataset.")
        else:
            st.warning(f"No details found for Signal Code {signal_code}.")
else:
    st.info("Click any row above to see drill-down details below 👆")
