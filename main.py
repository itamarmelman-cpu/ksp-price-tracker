import sqlite3
import time
import re  # IMPORT REGEX FOR BULLDOZER
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# ==========================================
# PART 1: Database Management
# ==========================================

def init_db():
    conn = sqlite3.connect('ksp_prices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  price REAL,
                  url TEXT,
                  date TEXT)''')
    conn.commit()
    conn.close()


def save_product(name, price, url):
    conn = sqlite3.connect('ksp_prices.db')
    c = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO products (name, price, url, date) VALUES (?, ?, ?, ?)",
              (name, price, url, current_date))
    conn.commit()
    conn.close()
    print(f"[DB] Saved: {name[:30]}... | {price} NIS")


def view_results():
    conn = sqlite3.connect('ksp_prices.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"{'Price':<10} | {'Name'}")
    print("-" * 60)
    for row in rows:
        print(f"{row[2]:<10} | {row[1][:60]}")
    print("=" * 60 + "\n")
    conn.close()


# ==========================================
# PART 2: The Scraper Logic
# ==========================================

def get_category_links(driver, category_url):
    print(f"\n[Scraper] Accessing category...")
    driver.get(category_url)
    time.sleep(5)

    # Scroll down to load items
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")
    links = []
    for elem in elements:
        url = elem.get_attribute("href")
        if url and url not in links:
            links.append(url)

    print(f"[Scraper] Found {len(links)} unique products.")
    return links


def extract_product_details(driver, product_url):
    """
    THE BULLDOZER METHOD 🚜
    1. Grab ALL text from the page.
    2. Use Regex to find any number that looks like a price near a Shekel sign.
    3. Take the MAX price found (assumes product price > shipping/installments).
    """
    print(f"   [Debug] Navigating to: {product_url}")
    driver.get(product_url)
    time.sleep(5)

    product_name = driver.title
    price = None

    # --- THE BULLDOZER LOGIC ---
    try:
        # 1. Get the entire text of the body
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # 2. Regex to find patterns like: "₪500", "500 ₪", "5,000.00"
        # This looks for digits (with commas/dots) next to a Shekel sign
        # Explanation: ₪ \s? (optional space) [\d,.]+ (digits) OR digits then ₪
        matches = re.findall(r'₪\s?([\d,]+\.?\d*)', body_text)
        matches += re.findall(r'([\d,]+\.?\d*)\s?₪', body_text)

        valid_prices = []
        for m in matches:
            try:
                # Clean the string to be a pure float
                clean_val = float(m.replace(',', ''))
                # Filter noise (0, distinct years like 2024, or small shipping costs)
                if 50 < clean_val < 100000:
                    valid_prices.append(clean_val)
            except:
                continue

        if valid_prices:
            # 3. Strategy: The product price is usually the HIGHEST price on the page
            # (Higher than "monthly payment" or "shipping")
            price = max(valid_prices)
            print(f"   [Debug] 🚜 Bulldozer found max price: {price}")

    except Exception as e:
        print(f"   [Debug] Bulldozer failed: {e}")

    # Fallback to H1 for name if title is messy
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1").text.strip()
        if h1: product_name = h1
    except:
        pass

    if not price:
        print("   [Failure] Could not find price.")

    return product_name, price


# ==========================================
# PART 3: The Manager
# ==========================================

def main():
    init_db()
    # iPhone Category URL
    CATEGORY_URL = "https://ksp.co.il/web/cat/31635..61633..573"

    print("🚀 Starting Main Scraper (Bulldozer Mode)...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        links = get_category_links(driver, CATEGORY_URL)


        links_to_scan = links
        print(f"[Manager] Scanning {len(links_to_scan)} items...")

        for i, link in enumerate(links_to_scan, 1):
            print(f"\n--- Item {i} ---")
            try:
                name, price = extract_product_details(driver, link)
                if price:
                    save_product(name, price, link)
                else:
                    print("[Warning] No price found.")
            except Exception as e:
                print(f"[Error] {e}")

        view_results()

    finally:
        driver.quit()


import schedule  # Don't forget to add this at the very top of the file!
import time  # Ensure this is imported as well


# ... (All your existing functions: init_db, save_product, etc.) ...

# ==========================================
# PART 4: Scheduler Integration
# ==========================================

def job():
    """
    Wrapper function to execute the main scraping logic.
    """
    print(f"\n⏰ [Scheduler] Time to work! Starting daily scan at {datetime.now().strftime('%H:%M:%S')}")

    # Run the main scraper logic
    # Note: Ensure 'main()' is the function that runs the scraper without the 'if name == main' block
    try:
        # We call the logic directly.
        # If your main logic is inside a function called main(), call it here.
        # If it was just inside the 'if' block, you should wrap it in a function named run_scraper() or similar.
        main()
    except Exception as e:
        print(f"❌ [Scheduler] Error during scheduled run: {e}")

    print("💤 [Scheduler] Scan finished. Going back to sleep...")


if __name__ == "__main__":
    print("🚀 Scheduler started! The script is now running in the background.")
    print("📅 Schedule: Runs every day at 19:00.")

    # Schedule the job to run every day at a specific time (e.g., 7:00 PM)
    schedule.every().day.at("12:50").do(job)

    # Optional: Run once immediately to verify everything works
    # print("⚡ Running an immediate test scan...")
    # job()

    # Infinite loop to keep the script alive and checking the time
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped manually.")