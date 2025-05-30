import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="ScarOS ∞ Biweekly Paydown Engine", layout="wide")
st.title("💥 ScarOS ∞ Paydown Interface")

# --- SIDEBAR CONFIG ---
st.sidebar.header("💼 Income & Fixed Expenses")
paycheck = st.sidebar.number_input("Biweekly Take-home Pay ($)", value=3116.18)
rent = st.sidebar.number_input("Monthly Rent", value=750.0)
utilities = st.sidebar.number_input("Monthly Utilities", value=60.0)
other_fixed = st.sidebar.number_input("Other Monthly Fixed Expenses", value=0.0)
strategy = st.sidebar.selectbox("Repayment Strategy", ["Avalanche (Highest APR)", "Snowball (Lowest Balance)"])
biweeks = st.sidebar.slider("Simulation Length (biweekly)", min_value=1, max_value=52, value=12)

# --- EXPENSE PROCESSING ---
biweekly_expense = (rent + utilities + other_fixed) / 2
free_cash = paycheck - biweekly_expense

# --- DEBT TABLE (Preloaded) ---
st.subheader("📄 Credit Card & Loan Inputs (Edit Me)")
initial_data = pd.DataFrame([
    {"Name": "AMEX", "Balance": 14860.0, "Limit": 15000.0, "APR": 25.99, "Type": "Credit"},
    {"Name": "CITI", "Balance": 649.0, "Limit": 2500.0, "APR": 0.0, "Type": "Credit"},
    {"Name": "Bilt", "Balance": 5424.0, "Limit": 6000.0, "APR": 23.49, "Type": "Credit"},
    {"Name": "Personal Loan", "Balance": 11000.0, "Limit": 0.0, "APR": 0.0, "Type": "Loan"},
    {"Name": "Venmo", "Balance": 4036.0, "Limit": 4400.0, "APR": 23.49, "Type": "Credit"},
])
debt_df = st.data_editor(initial_data, use_container_width=True, num_rows="dynamic")

# --- STRATEGY LOGIC ---
df = debt_df.copy()
if strategy == "Avalanche (Highest APR)":
    df = df.sort_values("APR", ascending=False)
else:
    df = df.sort_values("Balance", ascending=True)

# --- DEBT SIMULATION ---
timeline = []
remaining = df[["Name", "Balance", "APR"]].copy()

for period in range(biweeks):
    row_entry = {"Biweek": period + 1}
    available = free_cash

    for i, row in remaining.iterrows():
        if row["Balance"] <= 0:
            row_entry[row["Name"]] = 0
            continue

        min_pay = max(row["Balance"] * 0.02, 25)
        interest = row["Balance"] * (row["APR"] / 100 / 26)
        target_pay = min(available, min_pay + (available - min_pay) * 0.6)
        principal = max(target_pay - interest, 0)
        pay = min(row["Balance"], principal + interest)

        new_balance = row["Balance"] - principal
        remaining.at[i, "Balance"] = max(new_balance, 0)
        row_entry[row["Name"]] = round(pay, 2)
        available -= pay

    timeline.append(row_entry)
    if remaining["Balance"].sum() <= 0:
        break

timeline_df = pd.DataFrame(timeline)

# --- ADD BIWEEKLY DATES ---
start_date = datetime(2025, 5, 28)
biweekly_dates = [start_date + timedelta(weeks=2 * i) for i in range(len(timeline_df))]
timeline_df["Date"] = biweekly_dates
timeline_df = timeline_df[["Date"] + [col for col in timeline_df.columns if col != "Date"]]

# --- METRICS SECTION ---
original_total = debt_df["Balance"].sum()
remaining_balance = remaining["Balance"].sum()
total_paid = original_total - remaining_balance
weighted_apr = (debt_df["Balance"] * debt_df["APR"]).sum() / original_total

st.subheader("📊 Totals & Live Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Original Debt", f"${original_total:,.2f}")
col2.metric("Total Paid", f"${total_paid:,.2f}")
col3.metric("Remaining", f"${remaining_balance:,.2f}")
col4.metric("Weighted APR", f"{weighted_apr:.2f}%")

# --- NUMBERS TABLE ---
st.subheader("📄 Biweekly Payments Table")

if not timeline_df.empty:
    st.dataframe(timeline_df.set_index("Date"), use_container_width=True)

    payment_totals = timeline_df.drop(columns=["Date", "Biweek"]).sum().reset_index()
    payment_totals.columns = ["Debt", "Total Paid"]
    payment_totals["Total Paid"] = payment_totals["Total Paid"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(payment_totals.set_index("Debt"), use_container_width=True)
else:
    st.info("⚠️ No payment simulation data yet. Adjust your inputs to begin.")

# --- CHARTS ---
if not timeline_df.empty:
    st.subheader("📈 Biweekly Payments Timeline")
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    timeline_df.set_index("Date").drop(columns=["Biweek"]).plot(kind="bar", stacked=True, ax=ax1, width=1.0)
    ax1.set_ylabel("Payment ($)")
    ax1.set_title("Biweekly Payments Across Debts")
    st.pyplot(fig1)

    st.subheader("📉 Remaining Debt Balances")
    fig2, ax2 = plt.subplots()
    remaining.set_index("Name")["Balance"].plot(kind="bar", ax=ax2, color="crimson")
    ax2.set_ylabel("Balance ($)")
    ax2.set_title("Remaining Balances After Simulation")
    st.pyplot(fig2)

# --- DOWNLOAD ---
if not timeline_df.empty:
    st.download_button("📥 Download Pay Plan CSV", data=timeline_df.to_csv(index=False),
                       file_name="ScarOS_Biweekly_Accelerator.csv")

st.markdown("---")
st.caption("ScarOS ∞ Debt System – Recurse, Reduce, Rise.")
