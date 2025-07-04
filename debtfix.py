import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import boto3
import decimal
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="Omkar's ∞ Biweekly Paydown Engine", layout="wide")
st.title("💥 Omkar's ∞ Paydown Interface")

# --- AWS DYNAMODB SETUP ---
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)
table = dynamodb.Table("debtfix_cards")

# --- CONVERSION FIX FOR DYNAMODB ---
def to_decimal(val):
    if isinstance(val, (float, int, np.floating, np.integer)):
        return decimal.Decimal(str(round(val, 8)))
    return val

def from_decimal(val):
    return float(val) if isinstance(val, decimal.Decimal) else val

# --- CARD FORM ---
with st.expander("➕ Add New Credit Card / Loan", expanded=False):
    with st.form("card_form", clear_on_submit=False):
        card_name = st.text_input("Card Name")
        balance = st.number_input("Current Balance", min_value=0.0, step=100.0)
        limit = st.number_input("Credit Limit (0 if N/A)", min_value=0.0, step=100.0)
        apr = st.number_input("APR (%)", min_value=0.0, step=0.01)
        card_type = st.selectbox("Type", ["Credit", "Loan"])
        submit = st.form_submit_button("💾 Add Card")

        if submit and card_name.strip():
            try:
                item = {
                    "Name": card_name.strip(),
                    "Balance": to_decimal(balance),
                    "Limit": to_decimal(limit),
                    "APR": to_decimal(apr),
                    "Type": card_type
                }
                table.put_item(Item=item)
                st.success(f"✅ {card_name} saved to DynamoDB.")
            except Exception as e:
                st.error("❌ Failed to save card.")
                st.exception(e)

# --- LOAD CARDS FROM DB ---
try:
    response = table.scan()
    items = response.get("Items", [])
    if not items:
        st.warning("🟡 No cards found in the database.")
        initial_data = pd.DataFrame(columns=["Name", "Balance", "Limit", "APR", "Type"])
    else:
        initial_data = pd.DataFrame(items)
        for col in ["Balance", "Limit", "APR"]:
            if col in initial_data.columns:
                initial_data[col] = initial_data[col].apply(from_decimal)
        
except Exception as e:
    st.error("❌ Error loading data from DynamoDB.")
    st.exception(e)
    initial_data = pd.DataFrame(columns=["Name", "Balance", "Limit", "APR", "Type"])

# --- Payment Logging & Interest Tracking ---

def log_payment(card_name, amount, pay_date):
    """
    Log a payment, reduce balance in DynamoDB, and update interest tracking.
    """
    # Fetch latest item
    response = table.get_item(Key={"Name": card_name})
    item = response.get("Item")
    if not item:
        st.error(f"Card {card_name} not found.")
        return

    balance = float(item.get("Balance", 0))
    apr = float(item.get("APR", 0))
    last_date = item.get("LastPaymentDate", datetime.now().isoformat())
    last_date = datetime.fromisoformat(last_date) if isinstance(last_date, str) else last_date

    # Interest accrued since last payment
    days_elapsed = (pay_date - last_date.date()).days
    daily_rate = apr / 100 / 365
    interest_accrued = balance * daily_rate * max(days_elapsed, 0)

    # Update balance
    new_balance = max(balance - amount, 0)

    # Update DB
    table.update_item(
        Key={"Name": card_name},
        UpdateExpression="""
            SET Balance = :b, 
                LastPaymentDate = :d, 
                InterestPaid = if_not_exists(InterestPaid, :zero) + :int_paid,
                InterestAccrued = if_not_exists(InterestAccrued, :zero) + :int_acc
        """,
        ExpressionAttributeValues={
            ":b": decimal.Decimal(str(round(new_balance, 2))),
            ":d": pay_date.isoformat(),
            ":int_paid": decimal.Decimal("0"),  # All payments apply to principal in this model
            ":int_acc": decimal.Decimal(str(round(interest_accrued, 2))),
            ":zero": decimal.Decimal("0")
        }
    )
    st.success(f"✅ {card_name}: ${amount:,.2f} payment logged. +${interest_accrued:.2f} interest accrued.")

# --- Add Live Interest & Payment Form for Each Card ---
st.subheader("🔁 Card Payment Manager + Interest Burn")

for idx, row in initial_data.iterrows():
    card_name = row["Name"]
    balance = row["Balance"]
    apr = row["APR"]

    with st.expander(f"💳 {card_name} – ${balance:,.2f} @ {apr:.2f}% APR"):
        # Live interest rate (burn rate)
        daily_rate = apr / 100 / 365
        daily_interest = balance * daily_rate
        st.markdown(f"📉 **Daily Interest Burn Rate:** `${daily_interest:.2f}`/day")

        # Payment form
        with st.form(f"form_{card_name}", clear_on_submit=True):
            amount = st.number_input("Payment Amount", min_value=0.01, key=f"amt_{card_name}")
            pay_date = st.date_input("Payment Date", value=datetime.today(), key=f"dt_{card_name}")
            submit = st.form_submit_button("💾 Log Payment")
            if submit:
                log_payment(card_name, amount, pay_date)

# --- SIDEBAR CONFIG ---
st.sidebar.header("💼 Income & Fixed Expenses")
paycheck = st.sidebar.number_input("Biweekly Take-home Pay ($)", value=2000.00)
rent = st.sidebar.number_input("Monthly Rent", value=750.0)
utilities = st.sidebar.number_input("Monthly Utilities", value=60.0)
other_fixed = st.sidebar.number_input("Other Monthly Fixed Expenses", value=0.0)
strategy = st.sidebar.selectbox("Repayment Strategy", ["Avalanche (Highest APR)", "Snowball (Lowest Balance)"])
biweeks = st.sidebar.slider("Simulation Length (biweekly)", min_value=1, max_value=52, value=12)

# --- EXPENSE PROCESSING ---
biweekly_expense = (rent + utilities + other_fixed) / 2
free_cash = paycheck - biweekly_expense

# --- DEBT TABLE DISPLAY ---
st.subheader("📄 Current Credit Card & Loan Data")
debt_df = st.data_editor(initial_data.copy(), use_container_width=True, num_rows="dynamic")

# --- STRATEGY LOGIC ---
df = debt_df.copy()
df["Balance"] = df["Balance"].astype(float)
df["APR"] = df["APR"].astype(float)

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
start_date = datetime(2025, 6, 9)
biweekly_dates = [start_date + timedelta(weeks=2 * i) for i in range(len(timeline_df))]
timeline_df["Date"] = biweekly_dates
timeline_df = timeline_df[["Date"] + [col for col in timeline_df.columns if col != "Date"]]

# --- METRICS SECTION ---
original_total = df["Balance"].sum()
remaining_balance = remaining["Balance"].sum()
total_paid = original_total - remaining_balance
weighted_apr = (df["Balance"] * df["APR"]).sum() / original_total if original_total > 0 else 0

st.subheader("📊 Totals & Live Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Original Debt", f"${original_total:,.2f}")
col2.metric("Total Paid", f"${total_paid:,.2f}")
col3.metric("Remaining", f"${remaining_balance:,.2f}")
col4.metric("Weighted APR", f"{weighted_apr:.2f}%")

# --- BIWEEKLY PAYMENTS TABLE ---
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
                       file_name="Omkar_Biweekly_Strategy.csv")

st.markdown("---")
st.caption("Omkar's ∞ Debt System – Recurse, Reduce, Rise.")
