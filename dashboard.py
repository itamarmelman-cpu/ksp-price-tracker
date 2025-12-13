import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# --- Application Configuration ---
st.set_page_config(page_title="KSP Deal Hunter", page_icon="🎯", layout="wide")

# Custom CSS for UI enhancements
st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    div.css-card {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;}
    h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif; color: #343a40;}
    </style>
""", unsafe_allow_html=True)

# --- Configuration ---
DB_NAME = 'ksp_prices.db'


# --- Helper Functions ---

def clean_product_name(name):
    if not isinstance(name, str): return str(name)
    removals = ['טלפון סלולרי', 'יבואן רשמי', 'שנה אחריות', 'ללא מטען', 'וללא אוזניות', 'צבע', 'במבצע', 'מתנה', 'מהיר',
                'חדש', 'הדגם החדש', 'GB', 'RAM']
    for w in removals:
        name = name.replace(w, '')
    name = re.sub(r'(Black|White|Silver|Gold|Blue|Titanium|Natural|Green|Pink|Yellow|Purple|Gray)', '', name,
                  flags=re.IGNORECASE)
    name = re.sub(r'(שחור|לבן|כסף|זהב|כחול|טיטניום|טבעי|ירוק|ורוד|צהוב|סגול|אפור)', '', name)
    return name.replace('-', '').replace('  ', ' ').strip()


def identify_brand(name):
    name = str(name).lower()
    if 'apple' in name or 'iphone' in name: return 'Apple'
    if 'samsung' in name or 'galaxy' in name: return 'Samsung'
    if 'xiaomi' in name or 'redmi' in name: return 'Xiaomi'
    if 'google' in name or 'pixel' in name: return 'Google'
    if 'logitech' in name: return 'Logitech'
    return 'Other'


# --- Data Management ---

def load_and_process_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return None

        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()

        if df.empty: return pd.DataFrame()

        if 'name' in df.columns:
            df.rename(columns={'name': 'product_name'}, inplace=True)

        df['date'] = pd.to_datetime(df['date'])
        df = df[df['price'] > 50]
        df = df[df['price'] < 100000]

        # Feature Engineering
        df['Brand'] = df['product_name'].apply(identify_brand)
        df['ModelName'] = df['product_name'].apply(clean_product_name)

        # --- NEW: Extract Day of Week ---
        df['DayOfWeek'] = df['date'].dt.day_name()

        return df
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame()


# --- Main Application Logic ---

try:
    df = load_and_process_data()

    if df is None or df.empty:
        st.warning(f"⚠️ No data found in `{DB_NAME}`. Please run `main.py` first.")
        st.stop()

    latest_prices = df.sort_values('date').groupby('url').tail(1).copy()
    stats = df.groupby('ModelName')['price'].agg(['mean', 'min', 'max']).rename(
        columns={'mean': 'avg_price', 'min': 'min_price', 'max': 'max_price'})
    deals_df = pd.merge(latest_prices, stats, on='ModelName', how='left')
    deals_df['avg_price'] = deals_df['avg_price'].fillna(deals_df['price'])
    deals_df['discount_nis'] = deals_df['avg_price'] - deals_df['price']
    deals_df['discount_pct'] = (deals_df['discount_nis'] / deals_df['avg_price']) * 100

    # Sidebar
    st.sidebar.title("🎯 Settings")
    min_budget = st.sidebar.slider("Minimum Budget (NIS)", 0, 10000, 100)
    all_brands = ['All'] + sorted(deals_df['Brand'].unique().tolist())
    selected_brand = st.sidebar.selectbox("Filter by Brand", all_brands)

    filtered_df = deals_df[deals_df['price'] >= min_budget]
    if selected_brand != 'All':
        filtered_df = filtered_df[filtered_df['Brand'] == selected_brand]

    # Dashboard Header
    st.title("🛍️ KSP Price Tracker")
    st.markdown("---")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", f"{len(filtered_df)}")

    valid_deals = filtered_df[filtered_df['discount_pct'] > 1]
    if not valid_deals.empty:
        best_deal = valid_deals.sort_values('discount_pct', ascending=False).iloc[0]
        col2.metric("Best Deal", f"{best_deal['discount_pct']:.1f}% Off", best_deal['ModelName'][:15] + "...")
        col3.metric("Max Saving", f"₪{valid_deals['discount_nis'].max():,.0f}")
    else:
        col2.metric("Best Deal", "None", "No drops yet")
        col3.metric("Max Saving", "₪0")

    col4.metric("Avg Market Price", f"₪{filtered_df['price'].mean():,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section 1: Table
    st.subheader("📋 Product List")
    st.dataframe(
        filtered_df[['Brand', 'ModelName', 'price', 'avg_price', 'discount_pct', 'url']].sort_values('price',
                                                                                                     ascending=False),
        column_config={
            "ModelName": "Model",
            "price": st.column_config.NumberColumn("Current Price", format="₪%d"),
            "avg_price": st.column_config.NumberColumn("Avg Price", format="₪%d"),
            "discount_pct": st.column_config.ProgressColumn("Discount", format="%.1f%%", min_value=0, max_value=20),
            "url": st.column_config.LinkColumn("Link"),
        },
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Section 2: Visuals
    st.subheader("📊 Visual Insights")
    c1, c2 = st.columns(2)
    with c1:
        top_expensive = filtered_df.nlargest(10, 'price')
        fig_bar = px.bar(top_expensive, x='price', y='ModelName', orientation='h',
                         title="Top 10 Most Expensive Items", color='price')
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        fig_scatter = px.scatter(filtered_df, x='price', y='discount_pct',
                                 color='Brand', size='price', hover_data=['ModelName'],
                                 title="Price vs. Discount Distribution")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- NEW SECTION: BEST DAY ANALYSIS ---
    st.markdown("---")
    st.subheader("📅 Smart Insights: When is the best time to buy?")

    # Calculate average price per day of week
    if not df.empty:
        # Group by Day Name
        day_stats = df.groupby('DayOfWeek')['price'].mean().reset_index()

        # Order days correctly
        cats = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_stats['DayOfWeek'] = pd.Categorical(day_stats['DayOfWeek'], categories=cats, ordered=True)
        day_stats = day_stats.sort_values('DayOfWeek')

        # Create Bar Chart
        fig_days = px.bar(day_stats, x='DayOfWeek', y='price',
                          title="Average Market Price by Day of Week",
                          color='price', color_continuous_scale='RdYlGn_r')  # Red=Expensive, Green=Cheap

        fig_days.update_layout(yaxis_tickprefix='₪')
        st.plotly_chart(fig_days, use_container_width=True)

        st.info(
            "💡 **Pro Tip:** Keep running the scraper daily. Once you have 1-2 weeks of data, this graph will reveal which day typically has the lowest prices!")

except Exception as e:
    st.error(f"Application Error: {e}")