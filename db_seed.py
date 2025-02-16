import sqlite3
from datetime import datetime

DB_PATH = "data/portfolio.db"

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Testdaten für Watchlist
    cursor.execute("INSERT INTO watchlist (ticker, name, isin, wkn, added_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                   ("AAPL", "Apple Inc.", "US0378331005", "865985", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Wachstumsaktie"))

    cursor.execute("INSERT INTO watchlist (ticker, name, isin, wkn, added_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                   ("MSFT", "Microsoft Corporation", "US5949181045", "870747", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Langfristiges Investment"))

    # Testdaten für Trades
    cursor.execute("INSERT INTO trades (ticker, name, date, type, shares, price_per_share, currency, total_price, fees, total_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ("AAPL", "Apple Inc.", "2025-02-16", "buy", 10, 145.50, "USD", 1455.00, 5.00, 1460.00, "Testkauf"))

    cursor.execute("INSERT INTO trades (ticker, name, date, type, shares, price_per_share, currency, total_price, fees, total_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ("MSFT", "Microsoft Corporation", "2025-02-16", "buy", 5, 320.00, "USD", 1600.00, 3.00, 1597.00, "Teilverkauf"))

    conn.commit()
    conn.close()
    print("✅ Testdaten erfolgreich eingefügt.")

if __name__ == "__main__":
    seed_database()
