import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
import plotly.express as px
import joblib
import os
import numpy as np
import logging
import time 
import base64
import altair as alt

# Page config
st.set_page_config(page_title="Live Expense Dashboard", layout="wide")

# logging 
logging.basicConfig(
    filename="dashboard.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_bg():
    with open("assets/background.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

bg = load_bg()

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# Fade-In Content
st.markdown('<div class="fade-in">', unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align: center;'>💳 Smart Personal Expense Tracker</h1>",
    unsafe_allow_html=True
)

with st.spinner("Loading dashboard..."):
    time.sleep(1)

with st.spinner("Fetching transactions..."):
    time.sleep(2)

# MySQL connection     
def get_data():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="live_data_project"
        )
        df = pd.read_sql("""
            SELECT 
            t.transaction_id,
            t.quantity,
            t.price,t.total,t.transaction_time,t.product_id,
            c.Category_name AS Category
            FROM transactions t
            LEFT JOIN Category c
            ON t.category_id = c.category_id 

        """, conn)
        conn.close()

        df["transaction_time"] = pd.to_datetime(df["transaction_time"], errors="coerce")
        #st.write("DEBUG datetime conversion:", df["transaction_time"].dtype)
        df = df.dropna(subset=["transaction_time"]).reset_index(drop=True)

        df["month"] = df["transaction_time"].dt.to_period("M").astype(str)
        df["day"] = df["transaction_time"].dt.date
        
        logging.info("Data fetched successfully")
        return df

    except Exception as e:
        logging.error(f"Database error: {e}")
        st.error("❌ Unable to fetch data from database")
        return pd.DataFrame()

# Load data FIRST
df = get_data()
if df.empty:
    st.warning("No data available. Using placeholder data.")
    df = pd.DataFrame({
        "transaction_time": pd.date_range(start=datetime.today(), periods=1, freq='D'),
        "price": [0]
    })



# Convert datetime safely
#df["transaction_time"] = pd.to_datetime(df["transaction_time"])

# Load trained ML model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "transaction_model.pkl")  # adjust path if needed

model = joblib.load(MODEL_PATH)

# Get last transaction hour and day for reference
last_txn_time = df["transaction_time"].max()

# Prepare forecast dataframe for next 7 days (daily)
forecast_dates = [last_txn_time + pd.Timedelta(days=i) for i in range(1, 8)]
forecast_data = []

for dt in forecast_dates:
    quantity = 1  # assume default
    price = df["price"].mean()  # average transaction
    hour = int(df['transaction_time'].dt.hour.mean())

    dayofweek = dt.weekday()
    
    X_forecast = pd.DataFrame([[quantity, price, hour, dayofweek]],
                              columns=["quantity","price","transaction_hour","transaction_dayofweek"])
    predicted_total = round(float(model.predict(X_forecast)[0]), 2)
    
    forecast_data.append({"date": dt.date(), "predicted_total": predicted_total})
    
forecast_df = pd.DataFrame(forecast_data)


# EXPENSE-ONLY DATA

expense_df = df[df["price"] < 0].copy()
expense_df["amount"] = expense_df["price"].abs()

# KPI Calculations
total_income = df[df["price"] > 0]["price"].sum()
total_expense = df[df["price"] < 0]["price"].sum()
net_balance = total_income + total_expense
total_txns = len(df)

# KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total Income", f"₹ {total_income:,.2f}")
col2.metric("💸 Total Expense", f"₹ {abs(total_expense):,.2f}")
col3.metric("⚖️ Net Balance", f"₹ {net_balance:,.2f}")
col4.metric("🔢 Transactions", total_txns)

st.divider()

#  SMART ALERTS 
st.subheader("🚨 Smart Alerts")

# Daily spending alert
today = pd.Timestamp.today().date()
today_spend = df[
    (df["transaction_time"].dt.date == today) & (df["price"] < 0)
]["price"].abs().sum()

DAILY_LIMIT = 1000  

if today_spend > DAILY_LIMIT:
    st.error(f"⚠️ Overspending Alert! Today's expense ₹{today_spend:.2f}")
else:
    st.success(f"✅ Today's spending is under control (₹{today_spend:.2f})")

#Define a function to determine the activity

def financial_activity(total_income, total_expense, net_balance):
    if net_balance < 0:
        return "🔴 Overspending"
    elif total_expense > (0.7 * total_income):
        return "🟠 High Spending"
    elif total_expense > 0:
        return "🟢 Moderate Spending"
    else:
        return "💰 Good Savings"

# Calculate financial activity
activity = financial_activity(total_income, total_expense, net_balance)

# Show activity
st.subheader("📌 Financial Activity")
st.info(f"Current status: **{activity}**")

# Daily Trend
st.subheader("📈 Daily Transaction Trend")

daily = (
    df.groupby(df["transaction_time"].dt.date)["price"]
    .sum()
    .reset_index()
)

fig_daily = px.line(
    daily,
    x="transaction_time",
    y="price",
    markers=True
)

fig_daily.update_layout(
    plot_bgcolor="rgba(15,23,42,0.55)",   # glass navy
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    xaxis_title="Date",
    yaxis_title="Net Amount (₹)",
    height=450
)

fig_daily.update_traces(
    line=dict(width=3, color="#00bfff"),  
    marker=dict(size=6)
)

st.plotly_chart(fig_daily, use_container_width=True, key="daily_trend")

#Monthly Expense Trend 

st.subheader("📆 Monthly Expense Trend")

#df["month"] = df["transaction_time"].dt.to_period("M").astype(str)
monthly = df.groupby("month")["price"].sum().reset_index()

# Create Plotly bar chart with glass effect
fig_monthly = px.bar(
    monthly,
    x="month",
    y="price",
    text="price",
    color_discrete_sequence=["#00bfff"]  # light blue bars 
)

fig_monthly.update_layout(
    plot_bgcolor='rgba(0,0,0,0.2)',   # semi-transparent for glass effect
    paper_bgcolor='rgba(0,0,0,0.0)',  # fully transparent background
    font=dict(color='white'),         # text in white
    yaxis_title="Amount (₹)",
    xaxis_title="Month",
    height=450
)

# Display chart with a unique key
st.plotly_chart(fig_monthly, use_container_width=True, key="monthly_expense_trend")

#Hourly Spending Pattern 

st.subheader("⏰ Hourly Spending Pattern")

df["hour"] = df["transaction_time"].dt.hour
hourly = df.groupby("hour")["price"].sum().reset_index()

# Altair glass-effect chart
hourly_chart = (
    alt.Chart(hourly)
    .mark_line(point=True)
    .encode(
        x=alt.X("hour:O", title="Hour of Day"),
        y=alt.Y("price:Q", title="Total Spending"),
        tooltip=["hour", "price"]
    )
    .properties(
        height=400,
        background="rgba(0,0,0,0.2)"  # glass effect
    )
    .configure_view(
        strokeOpacity=0
    )
    .configure_axis(
        grid=True,
        gridOpacity=0.2
    )
)

st.altair_chart(hourly_chart, use_container_width=True)

from st_aggrid import AgGrid, GridOptionsBuilder
#Top 10 Highest Transactions

st.subheader("🔥 Top 10 Transactions")
df["transaction_time_str"] = df["transaction_time"].dt.strftime("%Y-%m-%d %H:%M:%S")


if "category" not in df.columns or df["category"].dtype == object:
    def assign_category(price):
        if price > 0:
            return "Income"
        elif price < 0 and abs(price) <= 500:
            return "Food"
        elif price < 0 and abs(price) > 500:
            return "Travel"
        else:
            return "Others"
    df["category"] = df["price"].apply(assign_category)

top_txn = df.sort_values("price", ascending=False).head(10)

# Glass-like container using Streamlit layout

gb = GridOptionsBuilder.from_dataframe(top_txn[["transaction_time_str", "price", "category", "quantity", "total"]])
gb.configure_default_column(resizable=True, filter=True)
grid_options = gb.build()

AgGrid(
    top_txn,
    gridOptions=grid_options,
    theme="balham",  # clean base
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    height=500
)

#Cumulative Balance Over Time

st.subheader("📈 Cumulative Balance")

df_sorted = df.sort_values("transaction_time")
df_sorted["cumulative_balance"] = df_sorted["price"].cumsum()

chart = (
    alt.Chart(df_sorted)
    .mark_line(point=False)
    .encode(
        x=alt.X("transaction_time:T", title="Date"),
        y=alt.Y("cumulative_balance:Q", title="Cumulative Balance"),
        tooltip=["transaction_time", "cumulative_balance"]
    )
    .properties(
        height=400,
        background="rgba(0,0,0,0)"  # glass effect
    )
    .configure_view(
        strokeOpacity=0
    )
    .configure_axis(
        grid=True,
        gridOpacity=0.2
    )
)

st.altair_chart(chart, use_container_width=True)

# Expense vs Income

pie_df = pd.DataFrame({
    "Type": ["Income", "Expense"],
    "Amount": [total_income, abs(total_expense)]
})

st.subheader("🥧 Income vs Expense")
fig, ax = plt.subplots(figsize=(3,3), facecolor='none')
  
ax.set_facecolor((0,0,0,0.1))             # slightly transparent dark 
ax.pie(
    pie_df["Amount"],
    labels=pie_df["Type"],
    autopct="%1.1f%%",
    startangle=90,
    labeldistance=0.40,
    pctdistance=0.60,
    textprops={'color':'white'}  # white labels
)
ax.axis("equal")

_, mid, _ = st.columns([1,2,1])
with mid:
    st.pyplot(fig, use_container_width=False)

#Category-wise Expense Chart

#bar chart 
all_categories = ["Shopping", "Food","Travel","Electronics", "Others"]
expense_df = df[df["price"] < 0].copy()
expense_df["amount"] = expense_df["price"].abs()

category_summary = (
    expense_df
    .groupby("category")["amount"]
    .sum()
    .reindex(all_categories, fill_value=0)
    .reset_index()
)

st.subheader("📊 Category-wise Expense Amount")
fig_bar = px.bar(
    category_summary,
    x="category",
    y="amount",
    text="amount",
    color="category",
    color_discrete_sequence=["#00bfff", "#ff4500", "#32cd32", "#ffa500"] 
)

fig_bar.update_layout(
    plot_bgcolor='rgba(0,0,50,0.2)',    # semi-transparent dark overlay
    paper_bgcolor='rgba(0,0,0,0.0)',    # fully transparent outside
    font=dict(color='white'),
    yaxis_title="Amount (₹)",
    xaxis_title="Category",
    height=450
)
st.plotly_chart(fig_bar, width="stretch")

# pie chart 
st.subheader("🥧 Category-wise Spending Distribution")

fig_pie = px.pie(
    category_summary,
    names="category",
    values="amount",
    hole=0.5
)
# Make it circular
fig_pie.update_traces(textinfo='label+percent', 
                    pull=[0.05]*len(category_summary))
fig_pie.update_layout(
    plot_bgcolor='rgba(0,0,0,0.2)',   # semi-transparent
    paper_bgcolor='rgba(0,0,0,0.0)',
    font=dict(color='white')
)
st.plotly_chart(fig_pie, width='stretch')


# Pivot for heatmap
all_categories = df['category'].astype(str)
heatmap_df = df[df["price"] < 0].copy()

heatmap_df["date"] = heatmap_df["transaction_time"].dt.date

heatmap_data = heatmap_df.pivot_table(
    index="date",
    columns="category",
    values="price",
    aggfunc="sum"
).abs()

st.subheader("🔥 Category vs Time Heatmap")
fig_heatmap = px.imshow(
    heatmap_data.T,
    labels=dict(x="Date", y="Category", color="Amount"),
    aspect="auto",
    color_continuous_scale="Viridis"
)
fig_heatmap.update_layout(
    plot_bgcolor='rgba(0,0,0,0.2)',
    paper_bgcolor='rgba(0,0,0,0.0)',
    font=dict(color='white')
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# BUDGET TRACKING 
st.subheader("📉 Monthly Budget Tracking")

df["month"] = df["transaction_time"].dt.strftime("%Y-%m")
current_month = datetime.today().strftime("%Y-%m")
monthly_expense = df[
    (df["price"] < 0) &
    (df["month"] == current_month)
].copy()

#if monthly_expense.empty:
  #  st.warning(f"No expense data available for {current_month}")
#else:
   # monthly_expense["amount"] = monthly_expense["price"].abs()
#monthly_expense["amount"] = monthly_expense["price"].abs()
if monthly_expense.empty:
    last_month = df[df["price"]< 0]["month"].max()
    st.warning(f"No expense data for {current_month}, showing last available month: {last_month}")
    monthly_expense = df[(df["price"] < 0) & (df["month"] == last_month)].copy()

# Aggregate total per category
budget_summary = (
    monthly_expense
    .groupby("category")["price"]
    .sum()
    .reset_index()
)

# Dynamically generate a "budget" (e.g., 20% more than spent)
budget_summary["budget"] = budget_summary["price"].abs() * 1.2
budget_summary["remaining"] = budget_summary["budget"] - budget_summary["price"]

# Grid options
gb = GridOptionsBuilder.from_dataframe(budget_summary)
gb.configure_default_column(resizable=True, sortable=True, filter=True)
gb.configure_column("price", header_name="Spent")
gb.configure_column("budget", header_name="Budget")
gb.configure_column("remaining", header_name="Remaining")
grid_options = gb.build()

st.markdown("""
<style>
.ag-root-wrapper {
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 5px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}
.ag-header {
    background: rgba(255, 255, 255, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)
AgGrid(
    budget_summary,
    gridOptions=grid_options,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    theme="balham",
    height=200
)
#transaction distribution 

st.subheader("📊 Transaction Amount Distribution")

fig = px.histogram(
    df,
    x="price",
    nbins =100
)
fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0.2)',  # glass navy
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    xaxis_title="Transaction Amount (₹)",
    yaxis_title="Number of Transactions",
    bargap=0.05

)


st.plotly_chart(fig, use_container_width=True, key="txn_hist")

# Plot forecast
st.subheader("🔮 7-Day Spending Forecast")

chart = (
    alt.Chart(forecast_df)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("predicted_total:Q", title="Predicted Spending"),
        tooltip=["date", "predicted_total"]
    )
    .properties(
        height=400,
        background="rgba(0,0,0,0)"  # glass effect
    )
    .configure_view(
        strokeOpacity=0
    )
    .configure_axis(
        grid=True,
        gridOpacity=0.2
    )
)

st.altair_chart(chart, use_container_width=True)


# Auto refresh
st.caption("🔄 Auto refresh every 60 seconds")
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.markdown('</div>', unsafe_allow_html=True)

