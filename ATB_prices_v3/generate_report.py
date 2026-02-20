import sqlite3
import pandas as pd

def generate_html_report(prices_db="prices.db", products_db="products.db", output_file="report.html"):
    # 1. Завантажуємо дані з бази цін
    conn_prices = sqlite3.connect(prices_db)
    df_prices = pd.read_sql_query("SELECT product_id, price, date FROM prices", conn_prices)
    conn_prices.close()

    # 2. Завантажуємо назви товарів
    conn_products = sqlite3.connect(products_db)
    df_products = pd.read_sql_query("SELECT product_id, product_name FROM products", conn_products)
    conn_products.close()

    # 3. Перетворюємо дату у формат datetime
    df_prices["date"] = pd.to_datetime(df_prices["date"], dayfirst=True, errors="coerce")
    df_prices = df_prices.dropna(subset=["date"])

    # 4. Об’єднуємо таблиці
    df = pd.merge(df_prices, df_products, on="product_id", how="left")

    # 5. Pivot: товари по рядках, дати по колонках
    pivot = df.pivot_table(index=["product_id", "product_name"],
                           columns="date",
                           values="price",
                           aggfunc="last")

    # 6. Скидаємо багаторівневий індекс колонок -> тільки дати
    pivot.columns = [col.strftime("%d/%m/%Y") for col in pivot.columns]

    # 7. Скидаємо індекс, щоб product_id та product_name стали колонками
    pivot = pivot.reset_index()

    # 8. Округлюємо ціни до двох знаків після коми
    for col in pivot.columns:
        if col not in ["product_id", "product_name"]:
            pivot[col] = pivot[col].apply(lambda x: round(x, 2) if pd.notna(x) else x)

    # 9. Додаємо розрахункові колонки (у відсотках)
    change_last_list = []
    change_year_list = []

    for _, row in pivot.iterrows():
        prices_series = row.drop(labels=["product_id", "product_name"]).dropna().sort_index()
        if prices_series.empty:
            change_last = None
            change_year = None
        else:
            last_price = prices_series.iloc[-1]
            if len(prices_series) > 1:
                prev_price = prices_series.iloc[-2]
                change_last = ((last_price - prev_price) / prev_price) * 100 if prev_price != 0 else None
            else:
                change_last = None
            first_price = prices_series.iloc[0]
            change_year = ((last_price - first_price) / first_price) * 100 if first_price != 0 else None

        change_last_list.append(change_last)
        change_year_list.append(change_year)

    pivot["Зміна з останньої дати (%)"] = change_last_list
    pivot["Зміна ціни від початку року (%)"] = change_year_list

    # 10. Додаємо рядок із середніми значеннями по всіх товарах
    avg_row = {col: None for col in pivot.columns}
    avg_row["product_id"] = "AVG"
    avg_row["product_name"] = "Середнє по всіх товарах"

    # середнє по датах
    for col in pivot.columns:
        if col not in ["product_id", "product_name", "Зміна з останньої дати (%)", "Зміна ціни від початку року (%)"]:
            avg_row[col] = pivot[col].mean()

    # середнє по змінах (%)
    avg_row["Зміна з останньої дати (%)"] = pd.Series(change_last_list).dropna().mean()
    avg_row["Зміна ціни від початку року (%)"] = pd.Series(change_year_list).dropna().mean()

    pivot = pd.concat([pivot, pd.DataFrame([avg_row])], ignore_index=True)

    # 11. Формуємо HTML з кольоровим форматуванням і стрілочками
    def format_change(val):
        if pd.isna(val) or val is None:
            return ""
        if val > 0:
            return f'<span class="positive">↑ {val:.2f}%</span>'
        elif val < 0:
            return f'<span class="negative">↓ {val:.2f}%</span>'
        else:
            return f"{val:.2f}%"

    pivot_html = pivot.copy()
    for col in ["Зміна з останньої дати (%)", "Зміна ціни від початку року (%)"]:
        pivot_html[col] = pivot_html[col].apply(format_change)

    # 🔹 форматування цінових колонок у HTML (дві цифри після коми)
    for col in pivot_html.columns:
        if col not in ["product_id", "product_name", "Зміна з останньої дати (%)", "Зміна ціни від початку року (%)"]:
            pivot_html[col] = pivot_html[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Звіт по цінах</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: right; }}
            th {{ background-color: #f4f4f4; text-align: center; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
            .positive {{ color: green; font-weight: bold; }}
            .negative {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Звіт по цінах</h1>
        <p>Файл створено на основі бази <b>{prices_db}</b>. Ви можете ділитися цим HTML‑файлом із друзями.</p>
        {pivot_html.to_html(classes='table', index=False, escape=False)}
    </body>
    </html>
    """

    # 12. Записуємо у файл
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML-звіт збережено у {output_file}")

if __name__ == "__main__":
    generate_html_report()
