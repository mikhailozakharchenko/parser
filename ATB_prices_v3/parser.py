import pandas as pd
import random
import time
import sqlite3
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Читаємо Excel
def read_ids(filename="product_id.xlsx"):
    df = pd.read_excel(filename)
    return df["product_id"].tolist()

# Ініціалізація Selenium
def init_driver():
    options = Options()
    #options.add_argument("--headless")  # без інтерфейсу
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service("chromedriver.exe")  # шлях до драйвера
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Парсинг ціни
def get_price(driver, product_id):
    url = f"https://www.atbmarket.com/sch?lang=uk&location=1154&query={product_id}"
    driver.get(url)
    try:
        # прокручуємо сторінку вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # чекаємо до 20 секунд, поки з’являться всі елементи з ціною
        elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-price__top"))
        )
        
        if elements:
            # беремо перший елемент зі списку
            price_text = elements[0].get_attribute("value")
            price = float(price_text)
        else:
            price = None
    except Exception as e:
        print(f"Помилка для товару {product_id}: {e}")
        price = None
    return price

def save_to_db(product_id, price, date):
    conn = sqlite3.connect("prices.db")
    cursor = conn.cursor()
    # створюємо таблицю, якщо її ще немає
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            price REAL,
            date TEXT
        )
    """)
    cursor.execute("INSERT INTO prices (product_id, price, date) VALUES (?, ?, ?)",
                   (product_id, price, date))
    conn.commit()
    conn.close()

def save_to_csv(product_id, price, date, filename="prices.csv"):
    file_exists = False
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["product_id", "price", "date"])
        writer.writerow([product_id, price, date])

# Логування
def log_message(message, logfile):
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(message + "\n")

if __name__ == "__main__":
    ids = read_ids("product_id.xlsx")
    driver = init_driver()
    today = datetime.now().strftime("%d_%m_%Y")
    logfile = f"log_{today}.txt"

    for pid in ids:
        price = get_price(driver, pid)
        date = datetime.now().strftime("%d/%m/%Y")
        if price is not None:
            log_message(f"[{date}] Товар {pid} – ціна {price} грн – успішно", logfile)
            print(f"{pid}: {price} грн")
            save_to_db(pid, price, date)
            save_to_csv(pid, price, date)
        else:
            log_message(f"[{date}] Товар {pid} – дані відсутні або помилка", logfile)
            print(f"{pid}: помилка")

        # випадкова пауза 2–10 секунд
        time.sleep(random.randint(2, 10))

    driver.quit()
    print("Парсинг завершено!")
