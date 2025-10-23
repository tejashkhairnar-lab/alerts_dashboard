import streamlit as st
import pandas as pd
import os

# -----------------------------
# LOAD DATA
# -----------------------------
csv_folder = r"E:\D09.Tejash Khairnar"
signal_412_path = os.path.join(csv_folder, "signal_412.csv")
collections_df = pd.read_csv(signal_412_path)
collections_df['Reported Date'] = collections_df['Date Of Event']

signal_901_path = os.path.join(csv_folder, "signal_901.csv")
auditors_report_df = pd.read_csv(signal_901_path)
auditors_report_df['Reported Date'] = auditors_report_df['Date Of Event']

signal_733_path = os.path.join(csv_folder, "signal_733.csv")
bureau_loans_df = pd.read_csv(signal_733_path)
bureau_loans_df['Reported Date'] = bureau_loans_df['Date Of Event']

signal_107_path = os.path.join(csv_folder, "signal_107.csv")
bureau_enq_df = pd.read_csv(signal_107_path)
bureau_enq_df['Reported Date'] = bureau_enq_df['Date Of Event']

alerts_path = os.path.join(csv_folder, "alerts_to_display.csv")
alerts_df = pd.read_csv(alerts_path)

# -----------------------------
# FRONTEND FILTERS
# -----------------------------
signal_codes = [code for code in alerts_df['Signal Code'].dropna().unique() if code in [733,107,412, 901, ]]
selected_signal_code = st.sidebar.selectbox("Select Signal Code", signal_codes)

# --- Reset session states if signal code changes ---
if 'last_selected_signal_code' not in st.session_state:
    st.session_state.last_selected_signal_code = selected_signal_code
elif st.session_state.last_selected_signal_code != selected_signal_code:
    st.session_state.variable_rules = {}
    st.session_state.final_rules = []
    for key in list(st.session_state.keys()):
        if key.startswith(('rule_', 'var_', 'op_', 'val_', 'log_', 'save_', 'name_', 'workflow_', 'alert_sev_', 'pre_op_')):
            del st.session_state[key]
    st.session_state.last_selected_signal_code = selected_signal_code
    st.experimental_rerun()

# --- Multi selection: Portfolio ---
portfolios = alerts_df['Portfolio'].dropna().unique()
selected_portfolios = st.sidebar.multiselect("Select Portfolio(s)", portfolios, default=list(portfolios))

# --- Filter alerts_df based on selections ---
filtered_alerts = alerts_df[
    (alerts_df['Signal Code'] == selected_signal_code) &
    (alerts_df['Portfolio'].isin(selected_portfolios))
]

# -----------------------------
# SELECT SPECIFIC COLUMNS & SYSTEM VARIABLES
# -----------------------------
system_variables_df = pd.DataFrame()  # default empty

if selected_signal_code == 412:
    base_cols = [
        'Product Type','Cibil Score','Region','Portfolio','No Of Attempts Email',
        'No Of Attempts Phone','Latest Completed Month Year','Overdue Amount',
        'Max Dpd','Reported Date','Date Of Event'
    ]
    selected_columns = [c for c in base_cols if c in collections_df.columns]
    extra_cols = ['Assessment Period', 'Latest Reported Date']
    for col in extra_cols:
        if col not in collections_df.columns:
            collections_df[col] = None
    selected_columns.extend(extra_cols)
    Collections = collections_df[selected_columns]
    dfs = [('Collections', Collections)]
elif selected_signal_code == 901:
    base_cols = [
        'Product Type','Cibil Score','Region','Portfolio','Financial Year',
        'Disclosure Section','Remarks','Overdue Amount','Max Dpd',
        'Reported Date','Date Of Event'
    ]
    selected_columns = [c for c in base_cols if c in auditors_report_df.columns]
    extra_cols = ['Assessment Period', 'Latest Reported Date']
    for col in extra_cols:
        if col not in auditors_report_df.columns:
            auditors_report_df[col] = None
    selected_columns.extend(extra_cols)
    Auditors_Report = auditors_report_df[selected_columns]
    dfs = [('Auditors_Report', Auditors_Report)]
elif selected_signal_code == 733:
    base_cols = [
        'Product Type','Cibil Score','Region','Portfolio','Report Date', 'Max Internal Dpd',
        'Max External Dpd', 'Report Extract Date', 'Assessment Period', 'Date Of Event'
    ]
    selected_columns = [c for c in base_cols if c in bureau_loans_df.columns]
    extra_cols = ['Latest Report Extract Date', 'DPD', 'Institute','Loan Type']
    for col in extra_cols:
        if col not in bureau_loans_df.columns:
            bureau_loans_df[col] = None
    selected_columns.extend(extra_cols)
    bureau_loans = bureau_loans_df[selected_columns]
    dfs = [('bureau_loans', bureau_loans)]
elif selected_signal_code == 107:
    base_cols = [
        'Product Type','Cibil Score','Region','Portfolio','Report Date', 'Enquiry Product Type',
         'Report Extract Date', 'Assessment Period', 'Date Of Event'
    ]
    selected_columns = [c for c in base_cols if c in bureau_enq_df.columns]
    extra_cols = ['Latest Report Extract Date', 'DPD', 'Institute','Loan Type','Enquiry Date']
    for col in extra_cols:
        if col not in bureau_enq_df.columns:
            bureau_enq_df[col] = None
    selected_columns.extend(extra_cols)
    bureau_enquiries = bureau_enq_df[selected_columns]
    dfs = [('bureau_enquiries', bureau_enquiries)]
else:
    dfs = []
    st.info(f"System variables creation skipped because selected Signal Code is {selected_signal_code}")

# Build system variables dataframe
system_vars_list = []
for df_name, df in dfs:
    for col in df.columns:
        system_vars_list.append({
            'system_variable': f"{col} FROM {df_name} TABLE",
            'column_name': col,
            'table_name': df_name
        })
system_variables_df = pd.DataFrame(system_vars_list)

# --- Operators and join options ---
operators = ['', '>', '<', '>=', '<=', '==', '+', '-', '*', '/', 'is.in', '~is.in', 'AND', 'OR','ON','WHERE', 'CONTAINS', 'MAX OF', 'SELECT']
join_options = ['', 'AND', 'OR']
pre_operators = ['', 'MAX', 'MIN', '-','SUM','COUNT', 'COUNT UNIQUE']

# --- Session States ---
if 'variable_rules' not in st.session_state:
    st.session_state.variable_rules = {}
if 'final_rules' not in st.session_state:
    st.session_state.final_rules = []
if 'rule_1' not in st.session_state:
    st.session_state.rule_1 = ""

# --- Helpers ---
def expand_rule(rule_str):
    expanded = rule_str
    for var_name, rule_def in st.session_state.variable_rules.items():
        expanded = expanded.replace(var_name, f"({rule_def})")
    return expanded

def describe_rule(rule_str):
    """Keep computed variable names as-is for human-readable description."""
    return rule_str

# --- Rule Builder Block ---
def build_rule_block(block_id):
    st.markdown(f"### 🧩 Rules Builder")

    available_vars = list(system_variables_df['system_variable']) + list(st.session_state.variable_rules.keys())
    pre_selected_operator = st.selectbox(f"Select Pre Operator", pre_operators, key=f"pre_op_{block_id}")
    selected_variable = st.selectbox(f"Select Variable", available_vars, key=f"var_{block_id}")
    selected_operator = st.selectbox(f"Select Operator", operators, key=f"op_{block_id}")
    input_value = st.text_input(f"Enter Value", key=f"val_{block_id}")
    logical_operator = st.selectbox(f"Join With", join_options, key=f"log_{block_id}")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(f"Add to Rule", key=f"add_{block_id}"):
            if f'rule_{block_id}' not in st.session_state:
                st.session_state[f'rule_{block_id}'] = ""
            # Build the rule piece
            if selected_operator == '':
                new_piece = f"{selected_variable}"
            else:
                if selected_operator in ['==', 'is.in', 'not_is.in']:
                    value_str = str([v.strip() for v in input_value.split(',')]) if ',' in input_value else f"'{input_value}'"
                else:
                    value_str = input_value
                new_piece = f"{selected_variable} {selected_operator} {value_str}"

            # Always prepend Pre Operator if selected
            if pre_selected_operator:
                new_piece = f"{pre_selected_operator} {new_piece}"

            # Combine with existing rule
            if st.session_state[f'rule_{block_id}']:
                st.session_state[f'rule_{block_id}'] += f" {logical_operator} " + new_piece if logical_operator else " " + new_piece
            else:
                st.session_state[f'rule_{block_id}'] = new_piece

    with col2:
        if st.button(f"Reset Rule", key=f"reset_{block_id}"):
            st.session_state[f'rule_{block_id}'] = ""
            st.success(f"Rule {block_id} has been reset.")

    # Current rule display
    current_rule = st.session_state.get(f'rule_{block_id}', "")
    st.markdown(f"#### Current Rule ({block_id})")
    st.code(current_rule if current_rule else "Please define..")

    save_option = st.radio(f"Save Rule As", ["Final Rule", "Variable Rule"], key=f"save_{block_id}")
    rule_name_input = st.text_input(f"Enter Rule Name", key=f"name_{block_id}")
    workflow_option = st.selectbox("Select Actionable Workflow", ["Critical", "High", "Medium", "Low"], key=f"workflow_{block_id}")
    alert_severity_option = st.selectbox("Select Alert Severity", ["High", "Medium", "Low"], key=f"alert_sev_{block_id}")

    if st.button(f"💾 Save Rule", key=f"save_btn_{block_id}"):
        if not current_rule.strip():
            st.error("No rule to save!")
        else:
            expanded_rule = expand_rule(current_rule)
            described_rule = describe_rule(current_rule)  # human-readable description

            if save_option == "Final Rule":
                st.session_state.final_rules.append({
                    'rule': expanded_rule,
                    'rule_described': described_rule,
                    'actionable_workflow': workflow_option,
                    'alert_severity': alert_severity_option
                })
                st.success(f"✅ Saved as Final Rule: {expanded_rule}")
            elif save_option == "Variable Rule":
                if not rule_name_input.strip():
                    st.error("Please enter a name for the variable rule!")
                else:
                    st.session_state.variable_rules[rule_name_input] = current_rule
                    st.success(f"✅ Saved as Variable Rule: {rule_name_input} = {current_rule}")

        st.session_state[f'rule_{block_id}'] = ""
        st.experimental_rerun()

# --- Main App ---
st.title("Configuration")

if selected_signal_code in alerts_df['Signal Code'].values:
    signal_name = alerts_df.loc[alerts_df['Signal Code'] == selected_signal_code, 'Signal Name'].iloc[0]
    st.subheader(f"Signal Code: {selected_signal_code}")
    st.subheader(f"Signal Name: {signal_name}")
else:
    st.subheader(f"Signal Code: {selected_signal_code} | Signal Name: Not Found")

st.markdown('<h5 style="color:black;">Computed Variables</h5>', unsafe_allow_html=True)
st.write(st.session_state.variable_rules)

st.markdown('<h5 style="color:black;">Final Rule</h5>', unsafe_allow_html=True)
if st.session_state.final_rules:
    st.json(st.session_state.final_rules)
else:
    st.write("No final rules saved yet.")

build_rule_block(block_id=1)
