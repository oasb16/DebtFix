# 📉 Credit Card Paydown Tracker (Streamlit + Google Sheets)

An interactive, secure debt reduction dashboard built in **Streamlit**, powered by real-time data from **Google Sheets** using a **Google Cloud service account**.

This app helps individuals on a structured credit recovery plan track credit card balances, visualize utilization, and plan their payoff across time.

https://debtfix.streamlit.app/

---

## ✅ Features

* 📊 Live sync from a Google Sheet
* 📈 Credit utilization and balance visualizations
* 🔐 Secure auth via Google service account
* 🌐 Deployable on Streamlit Cloud (Free Tier)
* 🧠 Built for first-time homebuyers, debt reducers, or credit optimizers

---

## 🛠️ Requirements

### Python Packages (via `requirements.txt`):

```
streamlit
pandas
gspread
oauth2client
matplotlib
```

---

## 🔑 Google Cloud Setup Instructions

To connect this Streamlit app to your Google Sheet, follow these steps exactly:

### 1. **Create a Google Cloud Project**

* Go to: [https://console.cloud.google.com/](https://console.cloud.google.com/)
* Project name: `creditcarddebt`

### 2. **Create a Service Account**

* IAM & Admin → Service Accounts → `Create Service Account`
* Example: `omkarsb@creditcarddebt.iam.gserviceaccount.com`

### 3. **Download the JSON Key**

* Click the account → `Manage Keys` → `Add Key` → `Create new JSON`

### 4. **Enable Sheets API**

* Enable API at:
  [https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=\<your\_project\_id>](https://console.developers.google.com/apis/api/sheets.googleapis.com/overview)

### 5. **Create Your Google Sheet**

Example format:

| Date       | Card | Balance | Limit |
| ---------- | ---- | ------- | ----- |
| 2025-05-10 | AMEX | 14516   | 15000 |

### 6. **Share Sheet With the Service Account**

* Share the sheet with:
  `your-service-account@<project>.iam.gserviceaccount.com`
* Give **Editor access**

---

## 🔒 Streamlit Cloud Setup

### 1. **Create `.streamlit/secrets.toml` file**

Convert the JSON key to TOML format:

```toml
[service_account_info]
type = "service_account"
project_id = "creditcarddebt"
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"""
client_email = "omkarsb@creditcarddebt.iam.gserviceaccount.com"
client_id = "..."
...
```

Paste the content directly into **Streamlit Cloud → App Settings → Secrets**.

### 2. **Push to GitHub**

Make sure your repo includes:

* `app.py`
* `requirements.txt`
* `.gitignore` (to exclude secrets locally)

### 3. **Deploy on [streamlit.io/cloud](https://streamlit.io/cloud)**

---

## 🧪 Troubleshooting

| Issue                          | Solution                                             |
| ------------------------------ | ---------------------------------------------------- |
| `PermissionError`              | Enable Sheets API + share sheet with service account |
| `ModuleNotFoundError: gspread` | Add to `requirements.txt`                            |
| Blank dashboard                | Verify sheet headers and values are present          |

---

## 🧠 Future Ideas

* Export to PDF or email monthly reports
* Include payoff timeline based on income
* Rent vs repay optimization

---

## 📎 Credits

Made with 💳 and 🧮 by \[Omkar S. Bhosle].

> "You don’t fix your finances overnight, but you *can* start now."
