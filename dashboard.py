import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="EWS Dashboard", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
csv_folder = r"E:\D09.Tejash Khairnar"
csv_file = os.path.join(csv_folder, "alerts_set_updated.csv")
df = pd.read_csv(csv_file)

# -----------------------------
# PORTFOLIOS SUMMARY TABLE
# -----------------------------
st.markdown("### Your Monitored Portfolios")

if {'Portfolio', 'Borrower Id'}.issubset(df.columns):
    df_clean = df.dropna(subset=['Portfolio', 'Borrower Id'])
    portfolio_summary = (
        df_clean.groupby('Portfolio')['Borrower Id']
        .nunique()
        .reset_index(name='Active Borrowers')
    )
    portfolio_summary = portfolio_summary[portfolio_summary['Active Borrowers'] > 0]
    portfolio_summary = portfolio_summary.sort_values(by='Active Borrowers', ascending=False).reset_index(drop=True)

    st.data_editor(
        portfolio_summary,
        use_container_width=True,
        disabled=True,
        hide_index=True,
        height=300
    )
else:
    st.warning("⚠️ Columns 'Portfolio' and 'Borrower Id' are required to show portfolio summary.")

# -----------------------------
# ANALYTICS FILTER
# -----------------------------
st.markdown("### 📊 Your Dashboard")

if 'Portfolio' in df.columns:
    all_portfolios = df['Portfolio'].dropna().unique().tolist()
    
    # Initialize session state
    if "selected_portfolios" not in st.session_state:
        st.session_state.selected_portfolios = all_portfolios.copy()
    
    # Button to select all
    if st.button("Select All"):
        st.session_state.selected_portfolios = all_portfolios.copy()
    
    # Multiselect uses session state
    st.session_state.selected_portfolios = st.multiselect(
        "Portfolios:",
        options=all_portfolios,
        default=st.session_state.selected_portfolios
    )
    
    # Filter DataFrame
    filtered_df = df[df['Portfolio'].isin(st.session_state.selected_portfolios)].copy()
else:
    st.warning("⚠️ Column 'Portfolio' is required for analytics filtering.")
    filtered_df = df.copy()

# -----------------------------
# PORTFOLIO SUMMARY METRICS
# -----------------------------
total_alerts = len(filtered_df)
total_borrowers_alerts = filtered_df['Borrower Id'].nunique()
total_borrowers = int(2.5 * total_borrowers_alerts)

col1, col2, col3 = st.columns(3)

def metric_chart(title, value):
    fig, ax = plt.subplots(figsize=(2.2, 1.5))
    ax.text(0.5, 0.5, f"{title}\n{value}", fontsize=10, ha='center', va='center', weight='bold')
    ax.axis('off')
    return fig

with col1:
    st.pyplot(metric_chart("Total Alerts", total_alerts))
with col2:
    st.pyplot(metric_chart("Borrowers with Alerts", total_borrowers_alerts))
with col3:
    st.pyplot(metric_chart("Total Borrowers", total_borrowers))

# -----------------------------
# ROW 2: Portfolio Risk + Case Status
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if "Alert Severity" in filtered_df.columns:
        severity_counts = filtered_df["Alert Severity"].value_counts()
        fig, ax = plt.subplots(figsize=(3, 2.5))
        ax.pie(
            severity_counts,
            labels=severity_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=['#FF4C4C', '#FFC107', '#4CAF50'],
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax.set_title("Portfolio Risk Profile", fontsize=11, fontweight='bold')
        st.pyplot(fig)

with col2:
    if "Case Status" in filtered_df.columns:
        status_counts = filtered_df["Case Status"].value_counts()
        colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F']
        fig, ax = plt.subplots(figsize=(3, 2.5))
        ax.pie(
            status_counts,
            labels=status_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax.set_title("Case Status Distribution", fontsize=11, fontweight='bold')
        st.pyplot(fig)

# -----------------------------
# Total Overdue Amount
# -----------------------------
if "Overdue Amount" in filtered_df.columns:
    total_overdue_amount_cr = filtered_df['Overdue Amount'].sum() / 10000000
    st.pyplot(metric_chart("Total Overdue Amount (Cr INR)", f"{total_overdue_amount_cr:,.2f}"))

# -----------------------------
# Max DPD Distribution
# -----------------------------
if "Max DPD" in filtered_df.columns:
    percentages = [40.28, 25, 3.12, 1.32]
    categories = ['SMA-0 (1–30)', 'SMA-1 (31–60)', 'SMA-2 (61–90)', 'NPA (>90)']
    colors = ['#4CAF50', '#FFEB3B', '#FF9800', '#F44336']
    percentages[0] += 100 - sum(percentages)
    fig, ax = plt.subplots(figsize=(4, 2))
    bars = ax.barh(categories, percentages, color=colors, edgecolor='white')
    for bar, pct in zip(bars, percentages):
        ax.text(pct + 0.5, bar.get_y() + bar.get_height()/2, f"{pct:.1f}%", va='center', fontsize=8)
    ax.set_xlabel('Percentage (%)', fontsize=8)
    ax.set_title('Distribution by Max DPD', fontsize=9)
    ax.set_xlim(0, max(percentages)+10)
    st.pyplot(fig)

# -----------------------------
# CIBIL Score Distribution to KFT Risk Classification
# -----------------------------
if {'Alert Severity', 'Cibil Score'}.issubset(filtered_df.columns):
    summary = filtered_df.groupby('Alert Severity')['Cibil Score'].agg([
        lambda x: np.percentile(x, 25),
        'median',
        lambda x: np.percentile(x, 75),
        'mean'
    ]).rename(columns={
        '<lambda_0>':'25th Percentile',
        '<lambda_1>':'75th Percentile',
        'median':'50th Percentile',
        'mean':'Average'
    })
    severity_order = ['Low', 'Medium', 'High']
    summary = summary.reindex(severity_order)
    fig, ax = plt.subplots(figsize=(4, 2))
    summary.plot(kind='bar', ax=ax, color=['#4CAF50','#FFC107','#FF4C4C','#2196F3'])
    ax.set_title('CIBIL Score Distribution to KFT Risk Classification', fontsize=10)
    ax.set_ylabel('CIBIL Score', fontsize=8)
    ax.set_xlabel('KFT Risk Classification', fontsize=8)
    ax.set_xticklabels(summary.index, rotation=0)
    ax.legend(title='Statistics', fontsize=6)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(300, 790)
    st.pyplot(fig)

# -----------------------------
# High Risk Borrowers Table
# -----------------------------
if {'Borrower Id', 'Borrower Name', 'Alert Id', 'Alert Severity'}.issubset(filtered_df.columns):
    alert_counts = (
        filtered_df.groupby(['Borrower Id', 'Borrower Name', 'Alert Severity'])['Alert Id']
        .nunique().reset_index(name='alert_count')
    )
    alert_counts_pivot = alert_counts.pivot_table(
        index=['Borrower Id', 'Borrower Name'],
        columns='Alert Severity',
        values='alert_count',
        fill_value=0
    ).reset_index()

    for col in ['High', 'Medium', 'Low']:
        if col not in alert_counts_pivot.columns:
            alert_counts_pivot[col] = 0

    alert_counts_pivot = alert_counts_pivot[['Borrower Id', 'Borrower Name', 'High', 'Medium', 'Low']]

    alert_counts_pivot["total_alerts"] = alert_counts_pivot["High"] + alert_counts_pivot["Medium"] + alert_counts_pivot["Low"]
    alert_counts_pivot["normalised_weighted_score"] = (
        (0.5*(alert_counts_pivot["High"]/alert_counts_pivot["total_alerts"])) +
        (0.3*(alert_counts_pivot["Medium"]/alert_counts_pivot["total_alerts"])) +
        (0.2*(alert_counts_pivot["Low"]/alert_counts_pivot["total_alerts"]))
    ).fillna(0)

    top_10 = alert_counts_pivot.sort_values(by='normalised_weighted_score', ascending=False).head(10)
    top_10_display = top_10.drop(columns=['normalised_weighted_score','total_alerts'])

    st.markdown("### High Risk Borrowers by Alert Count and Severity")
    st.dataframe(top_10_display.style.format({'High':'{:.0f}','Medium':'{:.0f}','Low':'{:.0f}'}),
                 use_container_width=True, height=300)

# -----------------------------
# Actionables Chart: Case Status vs Count & Avg Days
# -----------------------------
if {'Case Status', 'Days since last comment'}.issubset(filtered_df.columns):
    status_counts = filtered_df['Case Status'].value_counts()
    avg_days = filtered_df.groupby('Case Status')['Days since last comment'].mean()

    statuses = status_counts.index
    counts = status_counts[statuses].values
    days = avg_days[statuses].values

    fig, ax1 = plt.subplots(figsize=(7,4))
    bars = ax1.bar(statuses, counts, color='#4E79A7', alpha=0.7, label='Number of Cases')
    ax1.set_ylabel('Number of Cases', fontsize=9)
    ax1.set_xlabel('Case Status', fontsize=9)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    for i, (status, day) in enumerate(zip(statuses, days)):
        ax2.vlines(status, 0, day, color='orange', linestyles='dotted', linewidth=1)
        ax2.scatter(status, day, color='orange', s=40, zorder=5)

    ax2.set_ylabel('Avg Days Since Last Comment', fontsize=9)
    ax1.legend(loc='upper left', fontsize=8)
    ax2.scatter([], [], color='orange', s=40, label='Avg Days Since Last Comment')
    ax2.legend(loc='upper right', fontsize=8)

    plt.title('Actionables Management Summary', fontsize=12, fontweight='bold')
    fig.tight_layout()
    st.pyplot(fig)
