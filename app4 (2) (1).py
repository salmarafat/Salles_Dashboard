import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ======================
# 🎨 UI
# ======================
st.set_page_config(page_title="AI Retail Dashboard", layout="wide")

st.markdown("""
<style>
body {background-color:#0E1117;}
h1,h2,h3 {color:#00C2FF;}
.stMetric {background-color:#1F2937; padding:10px; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# ======================


# ======================
# 📥 LOAD DATA
# ======================
@st.cache_data
def load_data():
    df1 = pd.read_csv(r"data_part1.csv")
    df2 = pd.read_csv(r"data_part2.csv")

    df = pd.concat([df1, df2], ignore_index=True)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    return df

df = load_data()

# ======================
# 🎛️ FILTER
# ======================
st.sidebar.title("🔍 Filters")

country = st.sidebar.multiselect(
    "Country",
    df["Country"].unique(),
    default=df["Country"].unique()
)

df = df[df["Country"].isin(country)]

# ======================
# 📊 TITLE
# ======================
st.title("🚀 AI Retail Dashboard")

# ======================
# 📊 KPIs
# ======================
c1,c2,c3,c4 = st.columns(4)

c1.metric("💰 Revenue", f"{df['TotalPrice'].sum():,.0f}")
c2.metric("🧾 Orders", df['InvoiceNo'].nunique())
c3.metric("👤 Customers", df['CustomerID'].nunique())
c4.metric("📦 Products", df['StockCode'].nunique())

st.markdown("---")

# ======================
# 📊 TABS
# ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "📈 Sales",
    "👤 Customers",
    "🌍 Map",
    "🤖 AI Assistant"
])

# ======================
# 📊 OVERVIEW
# ======================
with tab1:
    daily = df.groupby(df['InvoiceDate'].dt.date)['TotalPrice'].sum().reset_index()

    fig = px.line(daily, x='InvoiceDate', y='TotalPrice', title="Sales Trend")
    st.plotly_chart(fig, use_container_width=True)

# ======================
# 📈 SALES (INTERACTIVE)
# ======================
with tab2:

    st.subheader("📊 Orders vs Sales")

    daily_orders = df.groupby(df['InvoiceDate'].dt.date)['InvoiceNo'].nunique()
    daily_sales = df.groupby(df['InvoiceDate'].dt.date)['TotalPrice'].sum()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_orders.index,
        y=daily_orders.values,
        name="Orders",
        line=dict(color="#00C2FF", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=daily_sales.index,
        y=daily_sales.values,
        name="Sales",
        line=dict(color="#FF6B6B", width=3, dash='dash'),
        yaxis="y2"
    ))

    fig.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="Orders"),
        yaxis2=dict(
            title="Sales",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Top products
    st.subheader("📦 Top Products")
    top_products = df.groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(10)

    fig2 = px.bar(
        x=top_products.values,
        y=top_products.index,
        orientation='h'
    )

    st.plotly_chart(fig2, use_container_width=True)

# ======================
# 👤 CUSTOMERS
# ======================
with tab3:

    # ======================
    # 👤 RFM CALCULATION
    # ======================
    rfm = df.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (df['InvoiceDate'].max() - x.max()).days,
        'InvoiceNo': 'nunique',
        'TotalPrice': 'sum'
    })

    rfm.columns = ['Recency', 'Frequency', 'Monetary']

    # ======================
    # 👑 SEGMENTATION (IMPORTANT)
    # ======================
    rfm['Type'] = 'Normal'
    rfm.loc[rfm['Monetary'] > rfm['Monetary'].quantile(0.8), 'Type'] = 'Churn Risk'
    rfm.loc[rfm['Recency'] > 200, 'Type'] = 'High Spender'

    # ======================
    # 📊 RFM SCATTER
    # ======================
    st.subheader("📊 Customer Behavior (RFM)")

    fig = px.scatter(
        rfm,
        x='Frequency',
        y='Monetary',
        size='Monetary',
        color='Type',
        title="Customer Segments"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================
    # 👑 TOP VIP CUSTOMERS
    # ======================
    st.subheader("👑 Top 11 VIP Customers")

    top_vip = rfm.sort_values('Monetary', ascending=False).head(11).reset_index()

    fig = px.bar(
        top_vip,
        x='CustomerID',
        y='Monetary',
        color='Monetary',
        color_continuous_scale='Blues'
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================
    # 📊 SEGMENT BREAKDOWN
    # ======================
    st.subheader("📊 Customer Segments Breakdown")

    seg_counts = rfm['Type'].value_counts().reset_index()
    seg_counts.columns = ['Type', 'Count']

    fig = px.bar(
        seg_counts,
        x='Type',
        y='Count',
        color='Type',
        text='Count'
    )

    st.plotly_chart(fig, use_container_width=True)
# ======================
# 🌍 MAP
# ======================
with tab4:

    country_sales = df.groupby('Country')['TotalPrice'].sum().reset_index()

    fig = px.choropleth(
        country_sales,
        locations="Country",
        locationmode="country names",
        color="TotalPrice"
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================
# 🤖 AI ASSISTANT (SMART)
# ======================
with tab5:

    st.subheader("🤖 Smart Business AI Assistant")

    question = st.text_input("Ask about your business data 👇")

    if question:

        q = question.lower()

        # ======================
        # 🌍 MARKET INSIGHT (REVENUE REMOVED)
        # ======================
        if any(word in q for word in ["revenue", "sales", "money"]):

            top_country = df.groupby("Country")["TotalPrice"].sum().idxmax()
            top_product = df.groupby("Description")["Quantity"].sum().idxmax()

            st.success(f"""
🌍 Market Insight:

- Strongest market: {top_country}  
- Most demanded product: {top_product}  

📌 Interpretation:
Business performance is driven by a few key markets and products,
rather than evenly distributed demand.
""")

        # ======================
        # 👤 CUSTOMER BEHAVIOR (NO COUNT)
        # ======================
        elif any(word in q for word in ["customers", "users", "clients"]):

            repeat_rate = (df.groupby("CustomerID")["InvoiceNo"].nunique() > 1).mean() * 100

            st.success(f"""
👤 Customer Behavior Insight:

- Repeat purchasing behavior exists across customers  
- Engagement is driven by returning customers

📌 Interpretation:
Customer value is concentrated in a loyal segment,
while many customers interact less frequently.
""")

        # ======================
        # 🧾 ORDER BEHAVIOR (NO ORDER COUNT)
        # ======================
        elif any(word in q for word in ["orders", "invoices", "bills"]):

            avg_items = df.groupby("InvoiceNo")["Quantity"].sum().mean()

            behavior = "small basket behavior" if avg_items < 10 else "bulk purchase behavior"

            st.success(f"""
🧾 Order Insight:

- Buying pattern: {behavior}  
- Order sizes vary significantly across transactions  

📌 Interpretation:
Customer purchasing behavior is inconsistent,
indicating mixed intent between small and bulk purchases.
""")

        # ======================
        # 💡 INSIGHT MODE
        # ======================
        elif any(word in q for word in ["insight", "analysis", "summary"]):

            top_product = df.groupby("Description")["Quantity"].sum().idxmax()
            top_country = df.groupby("Country")["TotalPrice"].sum().idxmax()
            peak_day = df.groupby(df['InvoiceDate'].dt.date)['TotalPrice'].sum().idxmax()

            st.info(f"""
💡 Business Insight:

- Dominant product: {top_product}  
- Leading market: {top_country}  
- Peak activity day: {peak_day}  

📌 Key Interpretation:
Sales are driven by a small number of high-impact products and peak activity periods.
""")

        # ======================
        # 📈 TREND (WITH INSIGHT)
        # ======================
        elif any(word in q for word in ["trend", "time", "chart"]):

            daily = df.groupby(df['InvoiceDate'].dt.date)['TotalPrice'].sum()

            fig = px.line(daily, title="Sales Behavior Over Time")
            st.plotly_chart(fig, use_container_width=True)

            st.success("""
📈 Time-Based Insight:

- Sales show fluctuations rather than steady growth  
- Demand is influenced by specific time periods  

📌 Interpretation:
Business performance is event-driven rather than stable.
""")

        # ======================
        # ❌ UNKNOWN QUERY
        # ======================
        else:
            st.warning("""
🤖 Try asking:

- revenue / sales  
- customers  
- orders  
- insight  
- time                       
 
            """)
# ======================
# 💡 ADVANCED INSIGHTS
# ======================

# ======================
# 💡 ADVANCED INSIGHTS (SAFE VERSION)
# ======================

st.markdown("## 💡 Business Insights")

# -------- Revenue & Orders
total_revenue = df['TotalPrice'].sum()
total_orders = df['InvoiceNo'].nunique()

# -------- Time insights
daily_sales = df.groupby(df['InvoiceDate'].dt.date)['TotalPrice'].sum()
best_day = daily_sales.idxmax()

monthly_sales = df.groupby(df['InvoiceDate'].dt.to_period('M'))['TotalPrice'].sum()
best_month = str(monthly_sales.idxmax())

# -------- Top products
top_products = (
    df.groupby('Description')['Quantity']
    .sum()
    .sort_values(ascending=False)
    .head(3)
)

top_1 = top_products.index[0]
top_2 = top_products.index[1]
top_3 = top_products.index[2]

# -------- Order insights
order_values = df.groupby('InvoiceNo')['TotalPrice'].sum()
top_order = order_values.idxmax()
top_order_value = order_values.max()

# -------- RFM check (safe)
if 'Type' in rfm.columns:
    vip_count = (rfm['Type'] == 'High Spender').sum()
else:
    vip_count = 0

total_customers = len(rfm)
percentage = (vip_count / total_customers) * 100 if total_customers > 0 else 0

# ======================
# 📊 FINAL DISPLAY
# ======================

st.info(f"""
 Business Insights:

 Best Day: {best_day}  
 Best Month: {best_month}  

 Largest Order: {top_order}  

 Top Products:
1- {top_1}  
2- {top_2}  
3- {top_3}  


 Recommendation:
- Focus on peak sales periods  
- Promote top-performing products  
- Target VIP customers for maximum revenue
""")
