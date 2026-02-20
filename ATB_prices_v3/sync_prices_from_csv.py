import sqlite3
import pandas as pd

def sync_prices_db(csv_file="prices.csv", db_file="prices.db"):
    # 1. Завантажуємо дані з CSV
    df = pd.read_csv(csv_file)

    # 2. Підключаємося до бази
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 3. Створюємо таблицю, якщо її ще немає
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            price REAL,
            date TEXT
        )
    """)

    # 4. Для кожного рядка з CSV перевіряємо, чи він уже є в БД
    for _, row in df.iterrows():
        product_id = str(row["product_id"])
        price = float(row["price"])
        date = row["date"]

        # перевіряємо, чи існує запис із таким product_id та датою
        cursor.execute("SELECT price FROM prices WHERE product_id=? AND date=?", (product_id, date))
        result = cursor.fetchone()

        if result is None:
            # якщо запису немає — додаємо новий
            cursor.execute("INSERT INTO prices (product_id, price, date) VALUES (?, ?, ?)",
                           (product_id, price, date))
        elif result[0] != price:
            # якщо ціна змінилася — оновлюємо
            cursor.execute("UPDATE prices SET price=? WHERE product_id=? AND date=?",
                           (price, product_id, date))

    conn.commit()
    conn.close()
    print(f"База {db_file} синхронізована з {csv_file}.")

if __name__ == "__main__":
    sync_prices_db()
