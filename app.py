import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Set page configuration
st.set_page_config(page_title="Daily Accounting Tracker", layout="wide")

# 1. Initialize Session State to store data across reruns smoothly
if "accounting_data" not in st.session_state:
    # We will store data as a dictionary: { "YYYY-MM": pd.DataFrame }
    st.session_state.accounting_data = {}

current_year = datetime.now().year

# Helper function to generate an empty DataFrame for a given month
def create_empty_month_df(year, month):
    num_days = calendar.monthrange(year, month)[1]
    data = {
        "Day": [f"Day {i}" for i in range(1, num_days + 1)],
        "Sales Entries (Comma Separated)": ["0.0" for _ in range(num_days)],
        "Returns": [0.0 for _ in range(num_days)],
        "Total Sales": [0.0 for _ in range(num_days)],
        "Net Culmination": [0.0 for _ in range(num_days)]
    }
    return pd.DataFrame(data)

# Pre-populate all months for the current year if not already done
for m in range(1, 13):
    month_key = f"{current_year}-{m:02d}"
    if month_key not in st.session_state.accounting_data:
        st.session_state.accounting_data[month_key] = create_empty_month_df(current_year, m)


# 2. Calculation Logic for Overview Dashboard
total_global_sales = 0.0
total_global_returns = 0.0
monthly_totals = {}

for m in range(1, 13):
    month_key = f"{current_year}-{m:02d}"
    df = st.session_state.accounting_data[month_key]
    
    m_sales = df["Total Sales"].sum()
    m_returns = df["Returns"].sum()
    
    monthly_totals[month_key] = {
        "Sales": m_sales,
        "Returns": m_returns,
        "Net": m_sales - m_returns
    }
    
    total_global_sales += m_sales
    total_global_returns += m_returns

global_net = total_global_sales - total_global_returns


# 3. App Layout & Navigation Tabs
st.title("📊 Daily Accounting & Sales Tracker")
st.write(f"Tracking Fiscal Year: **{current_year}**")

# Create Tabs: First is Overall Overview, followed by Month-wise breakdowns
month_names = list(calendar.month_name)[1:]
tab_titles = ["Overall Overview"] + month_names
tabs = st.tabs(tab_titles)

# --- TAB 1: OVERALL OVERVIEW (DASHBOARD) ---
with tabs[0]:
    st.header("📈 Financial Dashboard")
    
    # Top Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${total_global_sales:,.2f}")
    col2.metric("Total Returns", f"${total_global_returns:,.2f}", delta_color="inverse")
    col3.metric("Net Culmination", f"${global_net:,.2f}")
    
    st.markdown("---")
    st.subheader("Month-wise Summary")
    
    # Build Overview Summary Table
    overview_rows = []
    for m_idx, m_name in enumerate(month_names, start=1):
        m_key = f"{current_year}-{m_idx:02d}"
        overview_rows.append({
            "Month": m_name,
            "Sales": monthly_totals[m_key]["Sales"],
            "Returns": monthly_totals[m_key]["Returns"],
            "Net Culmination": monthly_totals[m_key]["Net"]
        })
    overview_df = pd.DataFrame(overview_rows)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)


# --- TABS 2-13: MONTHLY BREAKDOWNS & DATA ENTRY ---
for m_idx, m_name in enumerate(month_names, start=1):
    month_key = f"{current_year}-{m_idx:02d}"
    
    with tabs[m_idx]:
        st.header(f"📅 Data Entry: {m_name} {current_year}")
        
        # Display monthly scorecard metrics
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Month Sales", f"${monthly_totals[month_key]['Sales']:,.2f}")
        m_col2.metric("Month Returns", f"${monthly_totals[month_key]['Returns']:,.2f}")
        m_col3.metric("Month Net", f"${monthly_totals[month_key]['Net']:,.2f}")
        
        st.info("💡 **How to add multiple entries:** Type multiple entries separated by commas (e.g., `100, 250.50, 45`) in the Sales column. Type your returns deduction in the single Returns box.")
        
        # Fetch current month's copy for editing
        current_df = st.session_state.accounting_data[month_key].copy()
        
        # Editable data frame table
        edited_df = st.data_editor(
            current_df,
            column_config={
                "Day": st.column_config.TextColumn("Day", disabled=True),
                "Sales Entries (Comma Separated)": st.column_config.TextColumn("Sales Entries (+ / Credits)"),
                "Returns": st.column_config.NumberColumn("Returns (Deductions)", min_value=0.0, format="$%.2f"),
                "Total Sales": st.column_config.NumberColumn("Calculated Total Sales", disabled=True, format="$%.2f"),
                "Net Culmination": st.column_config.NumberColumn("Calculated Net", disabled=True, format="$%.2f"),
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{month_key}"
        )
        
        # Dedicated Submit Button per month to calculate values and push to dashboard
        if st.button(f"Submit & Recalculate {m_name} Data", key=f"btn_{month_key}"):
            for idx, row in edited_df.iterrows():
                raw_sales_str = str(row["Sales Entries (Comma Separated)"])
                
                # Split comma separated string, strip spaces, convert to floats, and total them
                try:
                    sales_list = [float(x.strip()) for x in raw_sales_str.split(",") if x.strip() != ""]
                    total_sales = sum(sales_list)
                except ValueError:
                    st.error(f"Error parsing values on **Day {idx+1}**. Please make sure you only input numbers and commas.")
                    total_sales = 0.0
                
                edited_df.at[idx, "Total Sales"] = total_sales
                edited_df.at[idx, "Net Culmination"] = total_sales - float(row["Returns"])
            
            # Save the clean data frame back into the session state memory
            st.session_state.accounting_data[month_key] = edited_df
            st.success(f"Successfully updated and submitted calculations for {m_name}!")
            st.rerun()
