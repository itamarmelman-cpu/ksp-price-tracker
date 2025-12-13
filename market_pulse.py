import sqlite3
import re
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
CATEGORY_URL = "https://ksp.co.il/web/cat/31635..61633..573"  # Example category (Smartphones)
DB_NAME = 'market_pulse.db'


# --- Database Management ---
def init_db():
    """Initializes the SQLite database table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_name TEXT,
                  price REAL,
                  url TEXT,
                  date TEXT)''')
    conn.commit()
    conn.close()


def save_to_db(name, price, url):
    """Saves a scraped product record to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO prices (product_name, price, url, date) VALUES (?, ?, ?, ?)",
                  (name, price, url, current_date))
        conn.commit()
        conn.close()
        print(f"   [+] Saved: {price} NIS | {name[:30]}...")
    except Exception as e:
        print(f"   [!] Database Error: {e}")


# --- Scraping Logic ---

def scrape_smart(driver, url):
    """
    Intelligent scraper that attempts multiple methods to extract price:
    1. Checks for 'Out of Stock' markers.
    2. JSON-LD (Structured Data) - Most reliable.
    3. Brute-force Regex search in visible text - Fallback.
    """
    try:
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content load

        # 1. Check Stock Status
        page_source = driver.page_source
        if "אזל מהמלאי" in page_source or "Out of stock" in page_source:
            print("   [-] Item out of stock. Skipping.")
            return None, None

        product_name = "Unknown Product"
        price = None

        # 2. Strategy A: JSON-LD Extraction (Best Practice)
        try:
            scripts = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            for script in scripts:
                content = script.get_attribute('innerHTML')
                if not content: continue

                data = json.loads(content)
                # Handle both single dict and graph lists
                objs = data['graph'] if isinstance(data, dict) and '@graph' in data else [data] if isinstance(data,
                                                                                                              dict) else data

                for obj in objs:
                    if obj.get('@type') == 'Product':
                        product_name = obj.get('name', product_name)
                        offers = obj.get('offers')
                        if offers:
                            offer_list = offers if isinstance(offers, list) else [offers]
                            for offer in offer_list:
                                if 'price' in offer:
                                    price = float(offer['price'])
                                    break
                    if price: break
                if price: break
        except Exception:
            pass  # Fail silently, move to fallback

        # 3. Strategy B: Visual/Regex Fallback
        if not price:
            try:
                # Fallback: Find price using regex on visible text
                body_text = driver.find_element(By.TAG_NAME, "body").text
                # Look for numbers followed/preceded by currency symbol
                matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*₪', body_text)
                candidates = [float(m.replace(',', '')) for m in matches]

                # Filter valid price range for smartphones (e.g., 500 - 20000)
                valid_candidates = [p for p in candidates if 500 < p < 20000]
                if valid_candidates:
                    price = max(valid_candidates)  # Usually the main price is the highest valid number
            except Exception:
                pass

        return product_name, price

    except Exception as e:
        print(f"   [!] Error scraping URL: {e}")
        return None, None


# --- Main Execution ---
def main():
    init_db()
    print("🚀 Starting Market Intelligence Scraper...")

    # Anti-detection settings
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 1. Harvest Links
    print(f"🔎 Collecting product links from category...")
    driver.get(CATEGORY_URL)
    time.sleep(5)

    # Scroll to load lazy items
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    product_links = []
    try:
        elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")
        for elem in elems:
            link = elem.get_attribute("href")
            if link and link not in product_links:
                product_links.append(link)
    except Exception as e:
        print(f"Error collecting links: {e}")

    print(f"✅ Found {len(product_links)} products. Starting detailed scan...")
    print("-" * 50)

    # 2. Process Products
    success_count = 0
    for i, link in enumerate(product_links):
        print(f"[{i + 1}/{len(product_links)}] Processing...", end="\r")
        name, price = scrape_smart(driver, link)

        if price:
            save_to_db(name, price, link)
            success_count += 1

    print("-" * 50)
    print(f"🏁 Job Done. Successfully tracked {success_count} products.")
    driver.quit()


if __name__ == "__main__":
    main()