import pandas as pd

def prepend_old_data(prices_file="prices.csv", old_file="old_data.csv", output_file="prices.csv"):
    # 1. Читаємо old_data.csv (там роздільник ;)
    df_old = pd.read_csv(old_file, sep=";")

    # 2. Читаємо prices.csv (там роздільник ,)
    df_prices = pd.read_csv(prices_file, sep=",")

    # 3. Об’єднуємо: спочатку old_data, потім prices
    df_combined = pd.concat([df_old, df_prices], ignore_index=True)

    # 4. Записуємо назад у форматі prices.csv (роздільник ,)
    df_combined.to_csv(output_file, sep=",", index=False)

    print(f"Файл {output_file} оновлено: дані з {old_file} додані на початок.")

if __name__ == "__main__":
    prepend_old_data()
