import sqlite3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


# --- Part 1: Database Setup ---
def init_db():
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_name TEXT,
                  price REAL,
                  date TEXT)''')
    conn.commit()
    conn.close()


def save_price_to_db(name, price):
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO prices (product_name, price, date) VALUES (?, ?, ?)",
              (name, price, current_date))
    conn.commit()
    conn.close()
    print(f"✅ Saved to DB: {price} at {current_date}")


# --- Part 2: Enhanced Scraping ---

init_db()
print("🚀 Launching browser...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
url = "https://ksp.co.il/web/item/253966"

try:
    driver.get(url)
    print("⏳ Waiting 8 seconds for full load...")
    time.sleep(8)  # Extended time for safety

    found_price = None
    product_name = "Logitech Keyboard"  # Translated for consistency

    # --- Attempt 1: Search by visible text ---
    print("\n--- Starting Attempt 1 (Visible Text) ---")
    # Looking for elements containing the Shekel symbol
    elements = driver.find_elements(By.XPATH, "//*[contains(text(), '₪')]")
    print(f"Found {len(elements)} elements with the '₪' symbol. Checking them:")

    for el in elements:
        try:
            text = el.text.strip()
            print(f"   Checked: '{text}'")  # Debug print
            # Validation: contains symbol, short length, and contains at least one digit
            if '₪' in text and len(text) < 20 and any(char.isdigit() for char in text):
                clean_price = float(text.replace('₪', '').replace(',', '').strip())
                print(f"   🎉 Bingo! Price found in text: {clean_price}")
                found_price = clean_price
                break
        except:
            continue

    # --- Attempt 2: Search by aria-label (Fallback) ---
    if not found_price:
        print("\n--- Not found in text. Starting Attempt 2 (aria-label) ---")
        try:
            # Searching for any element with a label containing the Shekel symbol
            element = driver.find_element(By.CSS_SELECTOR, "[aria-label*='₪']")
            raw_label = element.get_attribute("aria-label")
            print(f"   Hidden label found: '{raw_label}'")

            clean_price = float(raw_label.replace('₪', '').replace(',', '').strip())
            print(f"   🎉 Bingo! Price extracted from label: {clean_price}")
            found_price = clean_price
        except Exception as e:
            print(f"   Attempt 2 also failed: {e}")

    # --- Summary and Save ---
    if found_price:
        save_price_to_db(product_name, found_price)
    else:
        print("\n❌ Disappointment: Could not find price using any method.")

except Exception as e:
    print(f"General Error: {e}")

finally:
    # Keep open briefly for observation
    time.sleep(5)
    driver.quit()