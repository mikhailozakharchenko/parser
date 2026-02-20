import sqlite3
import pandas as pd

# 1. Завантажуємо дані з Excel
df = pd.read_excel("products_names.xlsx")

# 2. Створюємо нову SQLite-базу
conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# 3. Створюємо таблицю products
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT
    )
""")

# 4. Записуємо дані з Excel у таблицю
for _, row in df.iterrows():
    cursor.execute("INSERT OR REPLACE INTO products (product_id, product_name) VALUES (?, ?)",
                   (str(row["product_id"]), row["product_name"]))

conn.commit()
conn.close()

print("База даних products.db успішно створена та заповнена.")
