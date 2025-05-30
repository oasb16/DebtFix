import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="ScarDebt Interactive", layout="wide")
st.title("💥 ScarOS ∞ Paydown Interface")

st.sidebar.header("💼 Income & Expenses")
paycheck = st.sidebar.number_input("Biweekly Take-home Pay ($)", value=3116.18)
rent = st.sidebar.number_input("Monthly Rent", value=750)
utilities = st.sidebar.number_input("Utilities", value=60)
other_fixed = st.sidebar.number_input("Other Fixed Expenses", value=0)
strategy = st.sidebar.selectbox("Repayment Strategy", ["Avalanche (Highest APR)", "Snowball (Lowest Balance)"])
months = st.sidebar.slider("Simulation Length (months)", min_value=6, max_value=36, value=24)

# Editable debt table
st.subheader("💳 Credit Card & Loan Inputs")

initial_data = pd.DataFrame([
    {"Name": "AMEX", "Balance": 8000, "Limit": 10000, "APR": 25.99, "Type": "Credit"},
    {"Name": "CITI", "Balance": 5000, "Limit": 6000, "APR": 19.99, "Type": "Credit"},
    {"Name": "Chase", "Balance": 9000, "Limit": 11000, "APR": 23.49, "Type": "Credit"},
    {"Name": "Personal Loan", "Balance": 11000, "Limit": 0, "APR": 14.5, "Type": "Loan"},
])

edited_df = st.data_editor(initial_data, num_rows="dynamic", use_container_width=True)

# Core logic
monthly_income = paycheck * 2
free_cash = monthly_income - (rent + utilities + other_fixed)

df = edited_df.copy()
if strategy == "Avalanche (Highest APR)":
    df = df.sort_values("APR", ascending=False)
else:
    df = df.sort_values("Balance", ascending=True)

timeline = []
remaining = df[["Name", "Balance", "APR", "Type"]].copy()

for month in range(months):
    month_row = {"Month": month + 1}
    available = free_cash
    for i, row in remaining.iterrows():
        if row["Balance"] <= 0:
            month_row[row["Name"]] = 0
            continue

        min_pay = max(row["Balance"] * 0.02, 25)
        pay = min(available, min_pay + (available - min_pay) * 0.6)
        interest = row["Balance"] * (row["APR"] / 100 / 12)
        principal = pay - interest
        new_balance = row["Balance"] - principal

        remaining.at[i, "Balance"] = max(new_balance, 0)
        month_row[row["Name"]] = round(pay, 2)
        available -= pay

    timeline.append(month_row)
    if remaining["Balance"].sum() <= 0:
        break

timeline_df = pd.DataFrame(timeline)

st.subheader("📅 Monthly Paydown Timeline")
st.dataframe(timeline_df, use_container_width=True)

# Visuals
st.subheader("📊 Visual Summary")

summary_chart = timeline_df.drop(columns=["Month"]).sum().sort_values(ascending=False)
fig1, ax1 = plt.subplots()
summary_chart.plot(kind="bar", ax=ax1)
ax1.set_title("Total Paid per Debt")
ax1.set_ylabel("Total ($)")
st.pyplot(fig1)

balance_remaining = remaining[["Name", "Balance"]].set_index("Name")
fig2, ax2 = plt.subplots()
balance_remaining.plot(kind="bar", ax=ax2, color="tomato")
ax2.set_title("Remaining Balances After Simulation")
ax2.set_ylabel("Balance ($)")
st.pyplot(fig2)

# Export
st.markdown("---")
st.download_button("📥 Download Timeline as CSV", data=timeline_df.to_csv(index=False), file_name="scar_paydown_timeline.csv")
