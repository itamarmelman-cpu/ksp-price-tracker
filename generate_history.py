import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = 'market_pulse.db'


def generate_mock_history():
    """
    Utility script to backfill the database with synthetic historical data.
    This allows visualizing trends without waiting for weeks of real data accumulation.
    """
    print("⏳ Generating synthetic historical data...")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Fetch current real products
    c.execute("SELECT DISTINCT product_name, price, url FROM prices ORDER BY date DESC")
    real_products = c.fetchall()

    # Deduplicate (keep latest)
    unique_products = {}
    for name, price, url in real_products:
        if name not in unique_products:
            unique_products[name] = (price, url)

    print(f"Found {len(unique_products)} unique products. Backfilling 30 days...")

    # 2. Generate 30-day history for each product
    new_records = 0

    for name, (current_price, url) in unique_products.items():
        for days_back in range(1, 31):
            date_time = datetime.now() - timedelta(days=days_back)
            date_str = date_time.strftime("%Y-%m-%d %H:%M:%S")

            # Logic: Simulate price fluctuations
            # Random variation between -5% and +10%
            change_factor = random.uniform(0.95, 1.10)

            # Simulate "Price Drops": 20% of items were significantly more expensive in the past
            if random.random() < 0.2:
                change_factor = random.uniform(1.1, 1.3)

            past_price = current_price * change_factor

            # Rounding for realistic pricing (e.g., 4990 instead of 4991.23)
            past_price = round(past_price / 10) * 10
            if past_price < 100: past_price = current_price  # Sanity check

            c.execute("INSERT INTO prices (product_name, price, url, date) VALUES (?, ?, ?, ?)",
                      (name, past_price, url, date_str))
            new_records += 1

    conn.commit()
    conn.close()
    print(f"✅ Success! Added {new_records} historical records to {DB_NAME}.")


if __name__ == "__main__":
    generate_mock_history()