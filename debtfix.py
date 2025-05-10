import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
from datetime import datetime

# -- SETUP --
st.set_page_config(page_title="Credit Paydown Tracker", layout="wide")
st.title("📉 Credit Card Paydown Tracker")

# -- LOAD SECRETS FROM .streamlit/secrets.toml --
service_account_info = st.secrets["service_account_info"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# -- GOOGLE SHEETS AUTH --
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# -- SPREADSHEET URL --
SHEET_URL = "https://docs.google.com/spreadsheets/d/1QnnLFcFbyILXV7KvialsAgg1ZnvlohULXaRsJojADh0/edit"
worksheet = client.open_by_url(SHEET_URL).sheet1

# -- LOAD DATA --
data = worksheet.get_all_records()
df = pd.DataFrame(data)
df["Date"] = pd.to_datetime(df["Date"])

# -- CURRENT BALANCES & UTILIZATION --
latest = df.sort_values("Date").groupby("Card").tail(1)
latest["Utilization %"] = (latest["Balance"] / latest["Limit"] * 100).round(1)

st.subheader("📊 Current Credit Usage")
st.dataframe(latest.set_index("Card")[["Balance", "Limit", "Utilization %"]])

# -- BAR CHART: UTILIZATION --
fig, ax = plt.subplots()
latest.set_index("Card")["Utilization %"].plot(kind='bar', ax=ax, color='tomato')
ax.axhline(30, color='orange', linestyle='--', label='Fair (30%)')
ax.axhline(10, color='green', linestyle='--', label='Good (10%)')
ax.set_ylabel("Utilization %")
ax.set_title("Credit Utilization by Card")
ax.legend()
st.pyplot(fig)

# -- LINE CHART: HISTORICAL BALANCES --
st.subheader("📈 Balance Trends Over Time")
pivot = df.pivot(index="Date", columns="Card", values="Balance")
st.line_chart(pivot)

# -- FOOTER --
st.markdown("---")
st.caption("Built securely with Streamlit & Google Sheets — No scraping, no violations.")
