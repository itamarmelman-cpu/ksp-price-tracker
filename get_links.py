from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# 1. Insert the link to your chosen category here!
CATEGORY_URL = ("https://ksp.co.il/web/cat/31635..61633..573")

# Usage example (uncomment if you don't have a link):
# CATEGORY_URL = "https://ksp.co.il/web/cat/1033..389"

print("🕷️ Crawler starting...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

try:
    driver.get(CATEGORY_URL)
    print("Accessing category page, waiting for initial load...")
    time.sleep(5)

    # --- Scroll Logic ---
    # Instruct the browser to scroll down so the site loads more products (Lazy Loading).
    # We perform 3 major scrolls (increase the range if you need more products).
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"Scroll {i + 1} completed...")
        time.sleep(3)  # Waiting is mandatory between scrolls to allow content loading

    # --- Link Extraction ---
    # We are searching for 'a' tags (links) where the href contains '/item/'.
    # This is the unique identifier for a product page on KSP.
    elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")

    product_links = []

    for elem in elems:
        link = elem.get_attribute("href")
        # Filter duplicates and valid links
        if link and link not in product_links:
            product_links.append(link)

    print(f"\n✅ Success! Collected {len(product_links)} unique products.")
    print("Here are the first 5 examples:")
    for l in product_links[:5]:
        print(l)

except Exception as e:
    print(f"Error: {e}")

finally:
    input("Press Enter to close the browser...")  # Keeps the browser open for debugging
    driver.quit()