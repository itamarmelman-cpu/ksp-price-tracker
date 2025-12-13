import sqlite3

# Connect to the database file
conn = sqlite3.connect('prices.db')
c = conn.cursor()

# Simple SQL command: "Fetch everything from the prices table"
c.execute("SELECT * FROM prices")
rows = c.fetchall()

print(f"--- Total records saved: {len(rows)} ---")
print("ID | Product Name | Price | Date")
print("-" * 50)

for row in rows:
    # 'row' is a simple tuple, e.g.: (1, 'Keyboard', 101.0, '2023-12-01')
    # Note: Changed '₪' to 'NIS' for standard English logging
    print(f"{row[0]} | {row[1]} | {row[2]} NIS | {row[3]}")

conn.close()